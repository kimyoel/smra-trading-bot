"""
core/data_manager.py — ccxt OHLCV fetch + 캐시 (v2.7)

v2.7 추가:
  - _hedge_mode 글로벌 플래그: 현재 포지션 모드 추적 (True=Hedge, False=One-way)
  - is_hedge_mode(): 현재 모드 조회 함수 (다른 모듈에서 import)
  - try_switch_hedge_mode(): 비차단형 헤지 모드 전환 (포지션 0개일 때 자동 시도)
    → 성공 시 _hedge_mode=True, 실패 시 False 유지 (봇 계속 동작)
  - ensure_hedge_mode(): 기존 함수 유지 (하위 호환) — 내부에서 try_switch 호출

v2.6 추가:
  - ensure_hedge_mode(): Binance 헤지 모드(dualSidePosition=true) 전환
    → 봇 시작 시 1회 호출, 포지션 0개 확인 후 전환
    → 이미 헤지 모드이면 스킵 (idempotent)
    → 포지션 보유 중이면 전환 불가 → 안전하게 예외 raise

v2.5 추가:
  - ccxt timeout=5000ms 추가 (무한대기 방지)
  - fetch_ohlcv_parallel(): 유니크 심볼/TF 조합 ThreadPoolExecutor 병렬 fetch
    → 직렬 1.2s → 병렬 ~300ms 로 단축

버그 수정:
  - ccxt.binanceusdm().fetch_balance() 내부에서 load_markets() 시
    sapi/v1/capital/config/getall (Spot API) 호출 → 지역 차단
  - get_balance()를 fapiPrivateGetBalance() 직접 호출로 변경
    → fapi.binance.com만 사용, Spot API 완전 우회
  v2.4:
  - fapiPrivateGetBalance() → fapiPrivateV2GetBalance()
    /fapi/v1/balance deprecated → /fapi/v2/balance 로 변경
"""

import os
import time
import ccxt
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logger import get_logger

logger = get_logger("data_manager")

# ── 거래소 초기화 (USDT-M Futures 전용) ─────────────────────
exchange = ccxt.binanceusdm({
    "apiKey":  os.getenv("BINANCE_API_KEY", ""),
    "secret":  os.getenv("BINANCE_API_SECRET", ""),
    "enableRateLimit": True,
    "timeout": 5000,               # 5초 타임아웃 (무한대기 방지)
    "options": {
        "defaultType": "future",
        "fetchMarkets": ["linear"],   # futures 마켓만 로드
    },
})

# ── [v2.7] 헤지 모드 상태 플래그 ──────────────────────────────
_hedge_mode: bool = False


def is_hedge_mode() -> bool:
    """현재 헤지 모드 여부 반환. 다른 모듈에서 import하여 사용."""
    return _hedge_mode


# ── [v2.7] 비차단형 헤지 모드 전환 ────────────────────────────
def try_switch_hedge_mode() -> bool:
    """
    [v2.7] 포지션 0개일 때 헤지 모드 전환 시도 (비차단형).

    - 이미 헤지 모드이면 즉시 True 반환
    - 열린 포지션이 있으면 전환 불가 → False 반환 (봇 계속 동작)
    - 전환 성공 시 _hedge_mode=True 설정 후 True 반환
    - API 오류 시 False 반환 (다음 루프에서 재시도)

    Returns:
        True: 헤지 모드 활성 상태
        False: 아직 One-way 모드 (포지션 보유 중 또는 API 오류)
    """
    global _hedge_mode

    try:
        # 1. 현재 모드 조회
        resp = exchange.fapiPrivateGetPositionSideDual()
        is_hedge = resp.get("dualSidePosition", False)

        if is_hedge:
            if not _hedge_mode:
                logger.info("[DATA] ✅ 헤지 모드 확인 (dualSidePosition=true)")
            _hedge_mode = True
            return True

        # 2. One-way 모드 — 열린 포지션 확인
        positions = exchange.fetch_positions()
        open_count = sum(
            1 for p in positions
            if float(p.get("contracts", 0) or 0) > 0
        )

        if open_count > 0:
            logger.info(
                f"[DATA] ⏳ 헤지 모드 전환 대기 — 열린 포지션 {open_count}개 "
                f"(모두 청산되면 자동 전환)"
            )
            _hedge_mode = False
            return False

        # 3. 포지션 0개 → One-way → Hedge 전환
        exchange.fapiPrivatePostPositionSideDual({"dualSidePosition": "true"})
        _hedge_mode = True
        logger.info("[DATA] ✅ 헤지 모드 전환 완료 (One-way → Hedge)")
        return True

    except Exception as e:
        logger.warning(f"[DATA] 헤지 모드 전환 시도 실패 (다음 루프 재시도): {e}")
        return False


# ── [v2.6] 헤지 모드 전환 (하위 호환) ─────────────────────────
def ensure_hedge_mode() -> None:
    """
    [v2.6] 봇 시작 시 헤지 모드 확인/전환 (하위 호환).
    [v2.7] 내부에서 try_switch_hedge_mode() 호출.
           실패 시 RuntimeError 대신 경고만 출력 (봇 계속 동작).
    """
    result = try_switch_hedge_mode()
    if not result:
        logger.warning(
            "[DATA] ⚠️ 헤지 모드 전환 미완료 — One-way 호환 모드로 시작. "
            "기존 포지션 관리 계속, 포지션 청산 후 자동 전환 예정."
        )


# ── 1루프 캐시 ───────────────────────────────────────────────
_cache: dict = {}
CACHE_TTL_SEC = 55


def fetch_ohlcv(symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame | None:
    key = f"{symbol}_{timeframe}"
    now = time.time()

    if key in _cache:
        ts, df = _cache[key]
        if now - ts < CACHE_TTL_SEC:
            return df

    try:
        raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if not raw:
            logger.warning(f"[DATA] {key} — 빈 응답")
            return None

        df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
        _cache[key] = (now, df)
        return df

    except ccxt.NetworkError as e:
        logger.error(f"[DATA] 네트워크 오류 {key}: {e}")
    except ccxt.ExchangeError as e:
        logger.error(f"[DATA] 거래소 오류 {key}: {e}")
    except Exception as e:
        logger.error(f"[DATA] 알 수 없는 오류 {key}: {e}")
    return None


def fetch_funding_rate(symbol: str) -> float:
    try:
        info = exchange.fetch_funding_rate(symbol)
        return float(info.get("fundingRate", 0.0))
    except Exception as e:
        logger.warning(f"[DATA] 펀딩비 조회 실패 {symbol}: {e}")
        return 0.0


def fetch_orderbook(symbol: str) -> dict | None:
    try:
        return exchange.fetch_order_book(symbol, limit=5)
    except Exception as e:
        logger.warning(f"[DATA] 호가창 조회 실패 {symbol}: {e}")
        return None


def get_balance() -> tuple[float, float]:
    """
    USDT 선물 잔고 직접 조회. (v2.1: 필드명 수정)
    fapiPrivateV2GetBalance() → fapi.binance.com/fapi/v2/balance

    Binance /fapi/v2/balance 실제 응답 필드명:
        "balance"          → 총 지갑 잔고 (walletBalance라고 착각하기 쉬움)
        "availableBalance" → 여유 잔고
        ※ "walletBalance" 필드는 존재하지 않음 → 0.0 반환 버그의 원인

    Returns:
        (total, free) 튜플
        - total = balance         : 총 자본 (포지션 마진 포함, 미실현PnL 제외)
        - free  = availableBalance: 현재 사용 가능한 여유 잔고
    """
    try:
        response = exchange.fapiPrivateV2GetBalance()
        for asset in response:
            if asset.get("asset") == "USDT":
                total = float(asset.get("balance",          0.0))  # ← 올바른 필드명
                free  = float(asset.get("availableBalance", 0.0))
                logger.info(f"[DATA] 잔고 조회 성공: total={total:.2f} USDT / free={free:.2f} USDT")
                return total, free
        logger.warning("[DATA] USDT 잔고 항목 없음 (잔고 0 또는 미입금)")
        return 0.0, 0.0
    except Exception as e:
        logger.error(f"[DATA] 잔고 조회 실패: {e}")
        return 0.0, 0.0


def fetch_ohlcv_parallel(pairs: list[tuple[str, str]], limit: int = 100) -> None:
    """
    여러 (symbol, timeframe) 조합을 ThreadPoolExecutor로 병렬 fetch → 캐시 워밍.
    signal_generator 호출 전에 실행하면 직렬 대기 제거.

    Args:
        pairs: [(symbol, timeframe), ...] 유니크 조합 리스트
        limit: OHLCV 봉 개수
    """
    def _fetch_one(args):
        sym, tf = args
        return fetch_ohlcv(sym, tf, limit)

    with ThreadPoolExecutor(max_workers=len(pairs)) as executor:
        futures = {executor.submit(_fetch_one, p): p for p in pairs}
        for future in as_completed(futures):
            sym, tf = futures[future]
            try:
                result = future.result()
                status = f"{len(result)}봉" if result is not None else "실패"
                logger.info(f"[DATA] 병렬 fetch 완료: {sym} {tf} → {status}")
            except Exception as e:
                logger.error(f"[DATA] 병렬 fetch 오류 {sym} {tf}: {e}")


def clear_cache() -> None:
    _cache.clear()
