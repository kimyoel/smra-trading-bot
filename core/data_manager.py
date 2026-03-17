"""
core/data_manager.py — ccxt OHLCV fetch + 캐시 (v2.5)

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
    USDT 선물 잔고 직접 조회. (v2: total + free 동시 반환)
    fapiPrivateV2GetBalance() → fapi.binance.com/fapi/v2/balance

    Returns:
        (total, free) 튜플
        - total = walletBalance   : 총 자본 (포지션에 묶인 마진 포함, 미실현PnL 제외)
        - free  = availableBalance: 현재 사용 가능한 여유 잔고

    [v2 FIX] 이전 버전은 availableBalance만 반환 → 포지션 진입 후 여유잔고가 줄어
             배분 마진도 같이 줄어드는 버그 발생. total 기준으로 배분해야 함.
    """
    try:
        response = exchange.fapiPrivateV2GetBalance()
        for asset in response:
            if asset.get("asset") == "USDT":
                total = float(asset.get("walletBalance",    0.0))
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
