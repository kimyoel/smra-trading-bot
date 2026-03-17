"""
strategies/indicators.py — pandas_ta 래퍼
각 지표 계산 함수. DataFrame을 받아 조건 True/False 반환.
"""

import pandas as pd
import pandas_ta as ta
import numpy as np


def calc_rsi(df: pd.DataFrame, period: int = 14) -> bool:
    """RSI > 50"""
    rsi = ta.rsi(df["close"], length=period)
    if rsi is None or len(rsi) < period:
        return False
    return float(rsi.iloc[-1]) > 50


def calc_aroon(df: pd.DataFrame, period: int = 25) -> bool:
    """Aroon_Up > Aroon_Down AND Aroon_Up > 70"""
    aroon = ta.aroon(df["high"], df["low"], length=period)
    if aroon is None or aroon.empty:
        return False
    up   = float(aroon[f"AROONU_{period}"].iloc[-1])
    down = float(aroon[f"AROOND_{period}"].iloc[-1])
    return up > down and up > 70


def calc_mfi(df: pd.DataFrame, period: int = 14) -> bool:
    """MFI > 50"""
    mfi = ta.mfi(df["high"], df["low"], df["close"], df["volume"], length=period)
    if mfi is None or len(mfi) < period:
        return False
    return float(mfi.iloc[-1]) > 50


def calc_psar(df: pd.DataFrame, af0: float = 0.02, af: float = 0.02, max_af: float = 0.2) -> bool:
    """가격 > PSAR (상향 전환)"""
    psar = ta.psar(df["high"], df["low"], df["close"], af0=af0, af=af, max_af=max_af)
    if psar is None or psar.empty:
        return False
    col = [c for c in psar.columns if "PSARl" in c]
    if not col:
        return False
    psar_val = psar[col[0]].iloc[-1]
    if pd.isna(psar_val):
        return False
    return float(df["close"].iloc[-1]) > float(psar_val)


def calc_willr(df: pd.DataFrame, period: int = 14) -> bool:
    """WILLR > -50"""
    willr = ta.willr(df["high"], df["low"], df["close"], length=period)
    if willr is None or len(willr) < period:
        return False
    return float(willr.iloc[-1]) > -50


def calc_vwap(df: pd.DataFrame) -> bool:
    """가격 > VWAP"""
    vwap = ta.vwap(df["high"], df["low"], df["close"], df["volume"])
    if vwap is None or len(vwap) == 0:
        return False
    return float(df["close"].iloc[-1]) > float(vwap.iloc[-1])


def calc_ichimoku(df: pd.DataFrame) -> bool:
    """가격 > Cloud AND Tenkan > Kijun"""
    ichi = ta.ichimoku(df["high"], df["low"], df["close"], tenkan=9, kijun=26, senkou=52)
    if ichi is None or len(ichi) < 2:
        return False
    spans = ichi[0]
    if spans is None or spans.empty:
        return False
    tenkan_col  = [c for c in spans.columns if "ITS" in c]
    kijun_col   = [c for c in spans.columns if "IKS" in c]
    spanA_col   = [c for c in spans.columns if "ISA" in c]
    spanB_col   = [c for c in spans.columns if "ISB" in c]
    if not (tenkan_col and kijun_col and spanA_col and spanB_col):
        return False
    close  = float(df["close"].iloc[-1])
    tenkan = float(spans[tenkan_col[0]].iloc[-1])
    kijun  = float(spans[kijun_col[0]].iloc[-1])
    spanA  = float(spans[spanA_col[0]].iloc[-1])
    spanB  = float(spans[spanB_col[0]].iloc[-1])
    cloud_top = max(spanA, spanB)
    return close > cloud_top and tenkan > kijun


def calc_ema(df: pd.DataFrame, period: int = 20) -> bool:
    """가격 > EMA20"""
    ema = ta.ema(df["close"], length=period)
    if ema is None or len(ema) < period:
        return False
    return float(df["close"].iloc[-1]) > float(ema.iloc[-1])


def calc_adx(df: pd.DataFrame, period: int = 14) -> bool:
    """ADX > 20"""
    adx = ta.adx(df["high"], df["low"], df["close"], length=period)
    if adx is None or adx.empty:
        return False
    col = [c for c in adx.columns if c.startswith("ADX_")]
    if not col:
        return False
    return float(adx[col[0]].iloc[-1]) > 20


def calc_obv(df: pd.DataFrame) -> bool:
    """OBV > OBV.EMA(20)"""
    obv = ta.obv(df["close"], df["volume"])
    if obv is None or len(obv) < 20:
        return False
    obv_ema = ta.ema(obv, length=20)
    if obv_ema is None or len(obv_ema) < 20:
        return False
    return float(obv.iloc[-1]) > float(obv_ema.iloc[-1])


def calc_cmf(df: pd.DataFrame, period: int = 20) -> bool:
    """CMF > 0"""
    cmf = ta.cmf(df["high"], df["low"], df["close"], df["volume"], length=period)
    if cmf is None or len(cmf) < period:
        return False
    return float(cmf.iloc[-1]) > 0


def calc_roc(df: pd.DataFrame, period: int = 12) -> bool:
    """ROC > 0"""
    roc = ta.roc(df["close"], length=period)
    if roc is None or len(roc) < period:
        return False
    return float(roc.iloc[-1]) > 0


def calc_mom(df: pd.DataFrame, period: int = 10) -> bool:
    """MOM > 0"""
    mom = ta.mom(df["close"], length=period)
    if mom is None or len(mom) < period:
        return False
    return float(mom.iloc[-1]) > 0


def calc_atr_sig(df: pd.DataFrame, period: int = 14) -> bool:
    """ATR 상향 돌파 + 가격 > EMA20"""
    atr = ta.atr(df["high"], df["low"], df["close"], length=period)
    if atr is None or len(atr) < period + 1:
        return False
    atr_rising = float(atr.iloc[-1]) > float(atr.iloc[-2])
    ema_cond   = calc_ema(df, period=20)
    return atr_rising and ema_cond


def calc_sma(df: pd.DataFrame, period: int = 20) -> bool:
    """가격 > SMA20"""
    sma = ta.sma(df["close"], length=period)
    if sma is None or len(sma) < period:
        return False
    return float(df["close"].iloc[-1]) > float(sma.iloc[-1])


def get_atr_value(df: pd.DataFrame, period: int = 14) -> float:
    """ATR 값 반환 (TP/SL 계산용)"""
    atr = ta.atr(df["high"], df["low"], df["close"], length=period)
    if atr is None or len(atr) < period:
        return 0.0
    return float(atr.iloc[-1])


# ── 지표 이름 → 함수 매핑 ────────────────────────────────────
INDICATOR_MAP = {
    "RSI":      calc_rsi,
    "AROON":    calc_aroon,
    "MFI":      calc_mfi,
    "PSAR":     calc_psar,
    "WILLR":    calc_willr,
    "VWAP":     calc_vwap,
    "ICHIMOKU": calc_ichimoku,
    "EMA":      calc_ema,
    "ADX":      calc_adx,
    "OBV":      calc_obv,
    "CMF":      calc_cmf,
    "ROC":      calc_roc,
    "MOM":      calc_mom,
    "ATR_SIG":  calc_atr_sig,
    "SMA":      calc_sma,
}
