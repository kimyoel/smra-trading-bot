"""
strategies/indicators.py — pandas_ta 래퍼  (v2.1)
각 지표 계산 함수. DataFrame을 받아 "long" / "short" / False 반환.

[v2.1] 롱/숏 양방향 신호 지원
  - 이전: True(롱 조건 충족) / False
  - 이후: "long" / "short" / False(신호 없음)
  - signal_generator에서 모든 지표 방향이 일치할 때만 신호 발생
"""

import pandas as pd
import pandas_ta as ta
import numpy as np


def calc_rsi(df: pd.DataFrame, period: int = 14):
    """RSI > 60 → long, RSI < 40 → short"""
    rsi = ta.rsi(df["close"], length=period)
    if rsi is None or len(rsi) < period:
        return False
    val = float(rsi.iloc[-1])
    if val > 60:
        return "long"
    if val < 40:
        return "short"
    return False


def calc_aroon(df: pd.DataFrame, period: int = 25):
    """Aroon_Up > Aroon_Down AND Up > 70 → long
       Aroon_Down > Aroon_Up AND Down > 70 → short"""
    aroon = ta.aroon(df["high"], df["low"], length=period)
    if aroon is None or aroon.empty:
        return False
    up   = float(aroon[f"AROONU_{period}"].iloc[-1])
    down = float(aroon[f"AROOND_{period}"].iloc[-1])
    if up > down and up > 70:
        return "long"
    if down > up and down > 70:
        return "short"
    return False


def calc_mfi(df: pd.DataFrame, period: int = 14):
    """MFI > 60 → long, MFI < 40 → short"""
    mfi = ta.mfi(df["high"], df["low"], df["close"], df["volume"], length=period)
    if mfi is None or len(mfi) < period:
        return False
    val = float(mfi.iloc[-1])
    if val > 60:
        return "long"
    if val < 40:
        return "short"
    return False


def calc_psar(df: pd.DataFrame, af0: float = 0.02, af: float = 0.02, max_af: float = 0.2):
    """가격 > PSAR → long (상향 전환)
       가격 < PSAR → short (하향 전환)"""
    psar = ta.psar(df["high"], df["low"], df["close"], af0=af0, af=af, max_af=max_af)
    if psar is None or psar.empty:
        return False
    # PSARl = long signal (price above PSAR), PSARs = short signal
    long_col  = [c for c in psar.columns if "PSARl" in c]
    short_col = [c for c in psar.columns if "PSARs" in c]
    close = float(df["close"].iloc[-1])
    if long_col:
        psar_long = psar[long_col[0]].iloc[-1]
        if not pd.isna(psar_long) and close > float(psar_long):
            return "long"
    if short_col:
        psar_short = psar[short_col[0]].iloc[-1]
        if not pd.isna(psar_short) and close < float(psar_short):
            return "short"
    return False


def calc_willr(df: pd.DataFrame, period: int = 14):
    """WILLR > -30 → long (과매수 진입), WILLR < -70 → short (과매도 반전)"""
    willr = ta.willr(df["high"], df["low"], df["close"], length=period)
    if willr is None or len(willr) < period:
        return False
    val = float(willr.iloc[-1])
    if val > -30:
        return "long"
    if val < -70:
        return "short"
    return False


def calc_vwap(df: pd.DataFrame):
    """가격 > VWAP → long, 가격 < VWAP → short"""
    vwap = ta.vwap(df["high"], df["low"], df["close"], df["volume"])
    if vwap is None or len(vwap) == 0:
        return False
    close = float(df["close"].iloc[-1])
    vwap_val = float(vwap.iloc[-1])
    if close > vwap_val:
        return "long"
    if close < vwap_val:
        return "short"
    return False


def calc_ichimoku(df: pd.DataFrame):
    """가격 > Cloud AND Tenkan > Kijun → long
       가격 < Cloud AND Tenkan < Kijun → short"""
    ichi = ta.ichimoku(df["high"], df["low"], df["close"], tenkan=9, kijun=26, senkou=52)
    if ichi is None or len(ichi) < 2:
        return False
    spans = ichi[0]
    if spans is None or spans.empty:
        return False
    tenkan_col = [c for c in spans.columns if "ITS" in c]
    kijun_col  = [c for c in spans.columns if "IKS" in c]
    spanA_col  = [c for c in spans.columns if "ISA" in c]
    spanB_col  = [c for c in spans.columns if "ISB" in c]
    if not (tenkan_col and kijun_col and spanA_col and spanB_col):
        return False
    close   = float(df["close"].iloc[-1])
    tenkan  = float(spans[tenkan_col[0]].iloc[-1])
    kijun   = float(spans[kijun_col[0]].iloc[-1])
    spanA   = float(spans[spanA_col[0]].iloc[-1])
    spanB   = float(spans[spanB_col[0]].iloc[-1])
    cloud_top = max(spanA, spanB)
    cloud_bot = min(spanA, spanB)
    if close > cloud_top and tenkan > kijun:
        return "long"
    if close < cloud_bot and tenkan < kijun:
        return "short"
    return False


def calc_ema(df: pd.DataFrame, period: int = 20):
    """가격 > EMA20 → long, 가격 < EMA20 → short"""
    ema = ta.ema(df["close"], length=period)
    if ema is None or len(ema) < period:
        return False
    close   = float(df["close"].iloc[-1])
    ema_val = float(ema.iloc[-1])
    if close > ema_val:
        return "long"
    if close < ema_val:
        return "short"
    return False


def calc_adx(df: pd.DataFrame, period: int = 14):
    """ADX > 20 (추세 강도만 확인, DI+/DI- 로 방향 판단)
       DI+ > DI- AND ADX > 20 → long
       DI- > DI+ AND ADX > 20 → short"""
    adx = ta.adx(df["high"], df["low"], df["close"], length=period)
    if adx is None or adx.empty:
        return False
    adx_col  = [c for c in adx.columns if c.startswith("ADX_")]
    dip_col  = [c for c in adx.columns if c.startswith("DMP_")]
    dim_col  = [c for c in adx.columns if c.startswith("DMN_")]
    if not (adx_col and dip_col and dim_col):
        return False
    adx_val = float(adx[adx_col[0]].iloc[-1])
    dip_val = float(adx[dip_col[0]].iloc[-1])
    dim_val = float(adx[dim_col[0]].iloc[-1])
    if adx_val > 20 and dip_val > dim_val:
        return "long"
    if adx_val > 20 and dim_val > dip_val:
        return "short"
    return False


def calc_obv(df: pd.DataFrame):
    """OBV > OBV_EMA20 → long (자금 유입), OBV < OBV_EMA20 → short"""
    obv = ta.obv(df["close"], df["volume"])
    if obv is None or len(obv) < 20:
        return False
    obv_ema = ta.ema(obv, length=20)
    if obv_ema is None or len(obv_ema) < 20:
        return False
    obv_val = float(obv.iloc[-1])
    ema_val = float(obv_ema.iloc[-1])
    if obv_val > ema_val:
        return "long"
    if obv_val < ema_val:
        return "short"
    return False


def calc_cmf(df: pd.DataFrame, period: int = 20):
    """CMF > 0.05 → long, CMF < -0.05 → short"""
    cmf = ta.cmf(df["high"], df["low"], df["close"], df["volume"], length=period)
    if cmf is None or len(cmf) < period:
        return False
    val = float(cmf.iloc[-1])
    if val > 0.05:
        return "long"
    if val < -0.05:
        return "short"
    return False


def calc_roc(df: pd.DataFrame, period: int = 12):
    """ROC > 0.5 → long, ROC < -0.5 → short"""
    roc = ta.roc(df["close"], length=period)
    if roc is None or len(roc) < period:
        return False
    val = float(roc.iloc[-1])
    if val > 0.5:
        return "long"
    if val < -0.5:
        return "short"
    return False


def calc_mom(df: pd.DataFrame, period: int = 10):
    """MOM > 0 → long, MOM < 0 → short"""
    mom = ta.mom(df["close"], length=period)
    if mom is None or len(mom) < period:
        return False
    val = float(mom.iloc[-1])
    if val > 0:
        return "long"
    if val < 0:
        return "short"
    return False


def calc_atr_sig(df: pd.DataFrame, period: int = 14):
    """ATR 상승 + EMA 방향으로 롱/숏 결정
       ATR 상승 AND 가격 > EMA20 → long
       ATR 상승 AND 가격 < EMA20 → short"""
    atr = ta.atr(df["high"], df["low"], df["close"], length=period)
    if atr is None or len(atr) < period + 1:
        return False
    atr_rising = float(atr.iloc[-1]) > float(atr.iloc[-2])
    if not atr_rising:
        return False
    ema_dir = calc_ema(df, period=20)
    return ema_dir  # "long" / "short" / False


def calc_sma(df: pd.DataFrame, period: int = 20):
    """가격 > SMA20 → long, 가격 < SMA20 → short"""
    sma = ta.sma(df["close"], length=period)
    if sma is None or len(sma) < period:
        return False
    close   = float(df["close"].iloc[-1])
    sma_val = float(sma.iloc[-1])
    if close > sma_val:
        return "long"
    if close < sma_val:
        return "short"
    return False


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
