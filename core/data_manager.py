"""
core/data_manager.py — ccxt OHLCV fetch + 캐시 (v2.3)

버그 수정:
  - ccxt.binanceusdm().fetch_balance() 내부에서 load_markets() 시
    sapi/v1/capital/config/getall (Spot API) 호출 → 지역 차단
  - get_balance()를 fapiPrivateGetBalance() 직접 호출로 변경
    → fapi.binance.com만 사용, Spot API 완전 우회
"""

import os
import time
import ccxt
import pandas as pd
from utils.logger import get_logger

logger = get_logger("data_manager")

# ── 거래소 초기화 (USDT-M Futures 전용) ─────────────────────
exchange = ccxt.binanceusdm({
    "apiKey":  os.getenv("BINANCE_API_KEY", ""),
    "secret":  os.getenv("BINANCE_API_SECRET", ""),
    "enableRateLimit": True,
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


def get_balance() -> float:
    """
    USDT 선물 잔고 직접 조회.
    fapiPrivateGetBalance() → fapi.binance.com/fapi/v1/balance
    fetch_balance() 대신 사용 → Spot sapi 엔드포인트 완전 우회
    """
    try:
        response = exchange.fapiPrivateGetBalance()
        for asset in response:
            if asset.get("asset") == "USDT":
                return float(asset.get("availableBalance", 0.0))
        logger.warning("[DATA] USDT 잔고 항목 없음")
        return 0.0
    except Exception as e:
        logger.error(f"[DATA] 잔고 조회 실패: {e}")
        return 0.0


def clear_cache() -> None:
    _cache.clear()
