"""
strategies/indicators.py — WFA 전략별 복합 진입 조건 함수 (v5.0)

[v5.0] WFA OOS 보고서 기반 전면 교체
  - 기존: 개별 지표 → "long"/"short"/False 반환 → AND 조합
  - 변경: 전략별 복합 진입 함수 (entry_fn) → True/False 반환
  - 각 함수는 보고서의 진입 조건을 정확히 구현
  - 크로스(전환) 감지는 signal_generator에서 처리

지표 구현 목록:
  - Williams %R (14)
  - Bollinger Bands (20, 2)
  - EMA Stack (5, 26, 50) — 정배열/역배열
  - EMA Cross (12, 26)
  - ADX (14)
  - Aroon (25)
  - Donchian Channel (20)
  - Volume SMA (20) 필터
  - MACD (12, 26, 9)
  - Parabolic SAR
  - MOM (10)
  - OBV + OBV SMA (20)
  - SMA (10, 20)
  - Ichimoku (Tenkan/Kijun)
  - STDDEV (20) 팽창 감지
  - Keltner Channel (20, 2)
  - ATR (14) + ATR SMA 필터
"""

import pandas as pd
import pandas_ta as ta
import numpy as np


# ═══════════════════════════════════════════════════════════════
# 공통 헬퍼: 지표 계산 (각 entry_fn에서 호출)
# ═══════════════════════════════════════════════════════════════

def _willr(df: pd.DataFrame, period: int = 14):
    """Williams %R 계산, 최신값 반환"""
    wr = ta.willr(df["high"], df["low"], df["close"], length=period)
    if wr is None or len(wr) < period:
        return None
    val = float(wr.iloc[-1])
    if np.isnan(val):
        return None
    return val


def _bb(df: pd.DataFrame, period: int = 20, std: float = 2.0):
    """Bollinger Bands 계산, (lower, mid, upper) 반환"""
    bb = ta.bbands(df["close"], length=period, std=std)
    if bb is None or bb.empty:
        return None, None, None
    lower_col = [c for c in bb.columns if c.startswith("BBL_")]
    mid_col   = [c for c in bb.columns if c.startswith("BBM_")]
    upper_col = [c for c in bb.columns if c.startswith("BBU_")]
    if not (lower_col and mid_col and upper_col):
        return None, None, None
    lower = float(bb[lower_col[0]].iloc[-1])
    mid   = float(bb[mid_col[0]].iloc[-1])
    upper = float(bb[upper_col[0]].iloc[-1])
    if any(np.isnan(v) for v in [lower, mid, upper]):
        return None, None, None
    return lower, mid, upper


def _ema(df: pd.DataFrame, period: int):
    """EMA 계산, 최신값 반환"""
    ema = ta.ema(df["close"], length=period)
    if ema is None or len(ema) < period:
        return None
    val = float(ema.iloc[-1])
    if np.isnan(val):
        return None
    return val


def _sma(df: pd.DataFrame, col: str = "close", period: int = 20):
    """SMA 계산, 최신값 반환"""
    sma = ta.sma(df[col], length=period)
    if sma is None or len(sma) < period:
        return None
    val = float(sma.iloc[-1])
    if np.isnan(val):
        return None
    return val


def _adx_value(df: pd.DataFrame, period: int = 14):
    """ADX 값만 반환 (방향 무관)"""
    adx = ta.adx(df["high"], df["low"], df["close"], length=period)
    if adx is None or adx.empty:
        return None
    adx_col = [c for c in adx.columns if c.startswith("ADX_")]
    if not adx_col:
        return None
    val = float(adx[adx_col[0]].iloc[-1])
    if np.isnan(val):
        return None
    return val


def _aroon(df: pd.DataFrame, period: int = 25):
    """Aroon 계산, (up, down) 반환"""
    aroon = ta.aroon(df["high"], df["low"], length=period)
    if aroon is None or aroon.empty:
        return None, None
    up_col   = [c for c in aroon.columns if c.startswith("AROONU_")]
    down_col = [c for c in aroon.columns if c.startswith("AROOND_")]
    if not (up_col and down_col):
        return None, None
    up   = float(aroon[up_col[0]].iloc[-1])
    down = float(aroon[down_col[0]].iloc[-1])
    if np.isnan(up) or np.isnan(down):
        return None, None
    return up, down


def _donchian(df: pd.DataFrame, period: int = 20):
    """Donchian Channel, (lower, mid, upper) 반환"""
    donchian = ta.donchian(df["high"], df["low"], lower_length=period, upper_length=period)
    if donchian is None or donchian.empty:
        return None, None, None
    lower_col = [c for c in donchian.columns if c.startswith("DCL_")]
    mid_col   = [c for c in donchian.columns if c.startswith("DCM_")]
    upper_col = [c for c in donchian.columns if c.startswith("DCU_")]
    if not (lower_col and mid_col and upper_col):
        return None, None, None
    lower = float(donchian[lower_col[0]].iloc[-1])
    mid   = float(donchian[mid_col[0]].iloc[-1])
    upper = float(donchian[upper_col[0]].iloc[-1])
    if any(np.isnan(v) for v in [lower, mid, upper]):
        return None, None, None
    return lower, mid, upper


def _macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD 계산, (macd_line, signal_line, histogram) 반환"""
    macd = ta.macd(df["close"], fast=fast, slow=slow, signal=signal)
    if macd is None or macd.empty:
        return None, None, None
    macd_col   = [c for c in macd.columns if c.startswith("MACD_")]
    signal_col = [c for c in macd.columns if c.startswith("MACDs_")]
    hist_col   = [c for c in macd.columns if c.startswith("MACDh_")]
    if not (macd_col and signal_col):
        return None, None, None
    m = float(macd[macd_col[0]].iloc[-1])
    s = float(macd[signal_col[0]].iloc[-1])
    h = float(macd[hist_col[0]].iloc[-1]) if hist_col else m - s
    if np.isnan(m) or np.isnan(s):
        return None, None, None
    return m, s, h


def _psar(df: pd.DataFrame):
    """Parabolic SAR, (long_sar, short_sar, direction) 반환
    direction: "long" = SAR 상승 전환 (가격 위), "short" = SAR 하락 전환
    """
    psar = ta.psar(df["high"], df["low"], df["close"])
    if psar is None or psar.empty:
        return None
    long_col  = [c for c in psar.columns if c.startswith("PSARl_")]
    short_col = [c for c in psar.columns if c.startswith("PSARs_")]
    if not (long_col and short_col):
        return None
    long_val  = psar[long_col[0]].iloc[-1]
    short_val = psar[short_col[0]].iloc[-1]
    # pandas_ta PSAR: long 열에 값이 있으면 SAR이 가격 아래 = 상승 전환
    if pd.notna(long_val) and (pd.isna(short_val) or np.isnan(short_val)):
        return "long"
    elif pd.notna(short_val) and (pd.isna(long_val) or np.isnan(long_val)):
        return "short"
    return None


def _mom(df: pd.DataFrame, period: int = 10):
    """Momentum 계산, 최신값 반환"""
    mom = ta.mom(df["close"], length=period)
    if mom is None or len(mom) < period:
        return None
    val = float(mom.iloc[-1])
    if np.isnan(val):
        return None
    return val


def _obv(df: pd.DataFrame):
    """OBV, (obv_val, obv_sma_val) 반환"""
    obv = ta.obv(df["close"], df["volume"])
    if obv is None or len(obv) < 20:
        return None, None
    obv_sma = ta.sma(obv, length=20)
    if obv_sma is None or len(obv_sma) < 20:
        return None, None
    obv_val = float(obv.iloc[-1])
    sma_val = float(obv_sma.iloc[-1])
    if np.isnan(obv_val) or np.isnan(sma_val):
        return None, None
    return obv_val, sma_val


def _ichimoku(df: pd.DataFrame):
    """이치모쿠 Tenkan(9)/Kijun(26) 반환"""
    ichimoku_result = ta.ichimoku(df["high"], df["low"], df["close"],
                                   tenkan=9, kijun=26, senkou=52)
    if ichimoku_result is None:
        return None, None
    # ta.ichimoku returns a tuple: (ichimoku_df, span_df)
    if isinstance(ichimoku_result, tuple):
        ich_df = ichimoku_result[0]
    else:
        ich_df = ichimoku_result
    if ich_df is None or ich_df.empty:
        return None, None
    tenkan_col = [c for c in ich_df.columns if "ISA_" in c or "ITS_" in c]
    kijun_col  = [c for c in ich_df.columns if "ISB_" in c or "IKS_" in c]
    if not (tenkan_col and kijun_col):
        return None, None
    tenkan = float(ich_df[tenkan_col[0]].iloc[-1])
    kijun  = float(ich_df[kijun_col[0]].iloc[-1])
    if np.isnan(tenkan) or np.isnan(kijun):
        return None, None
    return tenkan, kijun


def _stddev(df: pd.DataFrame, period: int = 20):
    """표준편차 + 팽창 여부, (current_std, std_ema, is_expanding) 반환"""
    stdev = ta.stdev(df["close"], length=period)
    if stdev is None or len(stdev) < period + 10:
        return None, None, False
    stdev_ema = ta.ema(stdev, length=period)
    if stdev_ema is None or len(stdev_ema) < period:
        return None, None, False
    current = float(stdev.iloc[-1])
    ema_val = float(stdev_ema.iloc[-1])
    if np.isnan(current) or np.isnan(ema_val):
        return None, None, False
    return current, ema_val, current > ema_val


def _keltner(df: pd.DataFrame, period: int = 20, scalar: float = 2.0):
    """Keltner Channel, (lower, mid, upper) 반환"""
    kc = ta.kc(df["high"], df["low"], df["close"], length=period, scalar=scalar)
    if kc is None or kc.empty:
        return None, None, None
    lower_col = [c for c in kc.columns if c.startswith("KCL")]
    mid_col   = [c for c in kc.columns if c.startswith("KCB")]
    upper_col = [c for c in kc.columns if c.startswith("KCU")]
    if not (lower_col and mid_col and upper_col):
        return None, None, None
    lower = float(kc[lower_col[0]].iloc[-1])
    mid   = float(kc[mid_col[0]].iloc[-1])
    upper = float(kc[upper_col[0]].iloc[-1])
    if any(np.isnan(v) for v in [lower, mid, upper]):
        return None, None, None
    return lower, mid, upper


def _atr(df: pd.DataFrame, period: int = 14):
    """ATR, (atr_val, atr_sma) 반환"""
    atr = ta.atr(df["high"], df["low"], df["close"], length=period)
    if atr is None or len(atr) < 21:
        return None, None
    atr_sma = ta.sma(atr, length=20)
    if atr_sma is None or len(atr_sma) < 20:
        return None, None
    atr_val = float(atr.iloc[-1])
    sma_val = float(atr_sma.iloc[-1])
    if np.isnan(atr_val) or np.isnan(sma_val):
        return None, None
    return atr_val, sma_val


def get_atr_value(df: pd.DataFrame, period: int = 14) -> float:
    """ATR 값 반환 (TP/SL 계산용) — 기존 호환"""
    atr = ta.atr(df["high"], df["low"], df["close"], length=period)
    if atr is None or len(atr) < period:
        return 0.0
    return float(atr.iloc[-1])


# ═══════════════════════════════════════════════════════════════
# LONG 전략 진입 함수 (5개)
# ═══════════════════════════════════════════════════════════════

def entry_long_willr_bb_ema_stack(df: pd.DataFrame) -> bool:
    """
    LONG #1: 3_WILLR_BB_EMA_STACK (Score 19.21)

    진입 조건:
      - WR(14) < -80  (과매도)
      - Close < BB 하단(20,2)  (볼린저 밴드 하단 이탈)
      - EMA5 > EMA26 > EMA50  (EMA 정배열 = 상승 추세)
    """
    wr = _willr(df, 14)
    if wr is None or wr >= -80:
        return False

    bb_lower, _, _ = _bb(df, 20, 2.0)
    if bb_lower is None:
        return False
    close = float(df["close"].iloc[-1])
    if close >= bb_lower:
        return False

    ema5  = _ema(df, 5)
    ema26 = _ema(df, 26)
    ema50 = _ema(df, 50)
    if ema5 is None or ema26 is None or ema50 is None:
        return False
    if not (ema5 > ema26 > ema50):
        return False

    return True


def entry_long_adx_willr_ema_stack(df: pd.DataFrame) -> bool:
    """
    LONG #2: 3_ADX_WILLR_EMA_STACK (Score 18.73)

    진입 조건:
      - WR(14) < -80  (과매도)
      - EMA5 > EMA26 > EMA50  (EMA 정배열)
    필터:
      - ADX(14) > 25  (추세 강도 확인)
    """
    wr = _willr(df, 14)
    if wr is None or wr >= -80:
        return False

    ema5  = _ema(df, 5)
    ema26 = _ema(df, 26)
    ema50 = _ema(df, 50)
    if ema5 is None or ema26 is None or ema50 is None:
        return False
    if not (ema5 > ema26 > ema50):
        return False

    adx = _adx_value(df, 14)
    if adx is None or adx <= 25:
        return False

    return True


def entry_long_aroon_donchian_vol_inv(df: pd.DataFrame) -> bool:
    """
    LONG #3: 3_AROON_DONCHIAN_VOL_INV (Score 15.97)

    진입 조건:
      - AroonUp(25) > 70  (상승 추세 초기)
      - Close > Donchian 상단(20)  (채널 돌파)
    필터:
      - Volume ≤ SMA(20) × 1.5  (거래량 미급증 = 저볼륨 돌파)
    """
    aroon_up, _ = _aroon(df, 25)
    if aroon_up is None or aroon_up <= 70:
        return False

    _, _, donchian_upper = _donchian(df, 20)
    if donchian_upper is None:
        return False
    close = float(df["close"].iloc[-1])
    if close <= donchian_upper:
        return False

    # 거래량 필터: Volume ≤ SMA(20) × 1.5
    vol_sma = ta.sma(df["volume"], length=20)
    if vol_sma is None or len(vol_sma) < 20:
        return False
    vol_sma_val = float(vol_sma.iloc[-1])
    if np.isnan(vol_sma_val):
        return False
    current_vol = float(df["volume"].iloc[-1])
    if current_vol > vol_sma_val * 1.5:
        return False

    return True


def entry_long_ema_macd_psar(df: pd.DataFrame) -> bool:
    """
    LONG #4: 3_EMA_MACD_PSAR (Score 15.64)

    진입 조건:
      - EMA12 > EMA26  (단기 EMA 골든크로스)
      - MACD > Signal(12,26,9)  (MACD 히스토그램 양수)
      - Parabolic SAR 상승 전환  (SAR이 가격 아래)
    """
    ema12 = _ema(df, 12)
    ema26 = _ema(df, 26)
    if ema12 is None or ema26 is None:
        return False
    if ema12 <= ema26:
        return False

    macd_val, signal_val, _ = _macd(df, 12, 26, 9)
    if macd_val is None or signal_val is None:
        return False
    if macd_val <= signal_val:
        return False

    psar_dir = _psar(df)
    if psar_dir != "long":
        return False

    return True


def entry_long_ema_psar_mom(df: pd.DataFrame) -> bool:
    """
    LONG #5: 3_EMA_PSAR_MOM (Score 15.53)

    진입 조건:
      - EMA12 > EMA26  (단기 EMA 골든크로스)
      - Parabolic SAR 상승 전환  (SAR이 가격 아래)
      - MOM(10) > 0  (모멘텀 양수)
    """
    ema12 = _ema(df, 12)
    ema26 = _ema(df, 26)
    if ema12 is None or ema26 is None:
        return False
    if ema12 <= ema26:
        return False

    psar_dir = _psar(df)
    if psar_dir != "long":
        return False

    mom = _mom(df, 10)
    if mom is None or mom <= 0:
        return False

    return True


# ═══════════════════════════════════════════════════════════════
# SHORT 전략 진입 함수 (5개)
# ═══════════════════════════════════════════════════════════════

def entry_short_willr_bb_obv(df: pd.DataFrame) -> bool:
    """
    SHORT #1: 3_WILLR_BB_OBV (Score 20.36)

    진입 조건:
      - WR(14) > -20  (과매수)
      - Close > BB 상단(20,2)  (볼린저 밴드 상단 돌파)
      - OBV < OBV_SMA(20)  (거래량 약세)
    """
    wr = _willr(df, 14)
    if wr is None or wr <= -20:
        return False

    _, _, bb_upper = _bb(df, 20, 2.0)
    if bb_upper is None:
        return False
    close = float(df["close"].iloc[-1])
    if close <= bb_upper:
        return False

    obv_val, obv_sma_val = _obv(df)
    if obv_val is None or obv_sma_val is None:
        return False
    if obv_val >= obv_sma_val:
        return False

    return True


def entry_short_sma_ichimoku_stddev(df: pd.DataFrame) -> bool:
    """
    SHORT #2: 3_SMA_ICHIMOKU_STDDEV (Score 19.36)

    진입 조건:
      - SMA10 < SMA20  (단기 SMA 데드크로스)
      - Tenkan < Kijun  (이치모쿠 약세)
      - STDDEV 상승 (변동성 팽창) & Close < SMA(20)
    """
    sma10 = _sma(df, "close", 10)
    sma20 = _sma(df, "close", 20)
    if sma10 is None or sma20 is None:
        return False
    if sma10 >= sma20:
        return False

    tenkan, kijun = _ichimoku(df)
    if tenkan is None or kijun is None:
        return False
    if tenkan >= kijun:
        return False

    _, _, is_expanding = _stddev(df, 20)
    if not is_expanding:
        return False

    close = float(df["close"].iloc[-1])
    if close >= sma20:
        return False

    return True


def entry_short_obv_keltner_adx_inv(df: pd.DataFrame) -> bool:
    """
    SHORT #3: 3_OBV_KELTNER_ADX_INV (Score 18.98)

    진입 조건:
      - OBV < OBV_SMA(20)  (거래량 약세)
      - Close > KC 상단(20,2)  (켈트너 채널 상단 돌파)
    필터:
      - ADX(14) ≤ 25  (추세 없음 = 횡보장에서만 역추세 진입)
    """
    obv_val, obv_sma_val = _obv(df)
    if obv_val is None or obv_sma_val is None:
        return False
    if obv_val >= obv_sma_val:
        return False

    _, _, kc_upper = _keltner(df, 20, 2.0)
    if kc_upper is None:
        return False
    close = float(df["close"].iloc[-1])
    if close <= kc_upper:
        return False

    adx = _adx_value(df, 14)
    if adx is None or adx > 25:
        return False

    return True


def entry_short_bb_ema_stack(df: pd.DataFrame) -> bool:
    """
    SHORT #4: 2_BB_EMA_STACK (Score 18.73)

    진입 조건:
      - Close > BB 상단(20,2)  (볼린저 밴드 상단 돌파)
      - EMA5 < EMA26 < EMA50  (EMA 역배열 = 하락 추세)
    필터: 없음 (2지표 조합)
    """
    _, _, bb_upper = _bb(df, 20, 2.0)
    if bb_upper is None:
        return False
    close = float(df["close"].iloc[-1])
    if close <= bb_upper:
        return False

    ema5  = _ema(df, 5)
    ema26 = _ema(df, 26)
    ema50 = _ema(df, 50)
    if ema5 is None or ema26 is None or ema50 is None:
        return False
    if not (ema5 < ema26 < ema50):
        return False

    return True


def entry_short_bb_ema_stack_atr_inv(df: pd.DataFrame) -> bool:
    """
    SHORT #5: 3_BB_EMA_STACK_ATR_INV (Score 18.73)

    진입 조건:
      - Close > BB 상단(20,2)  (볼린저 밴드 상단 돌파)
      - EMA5 < EMA26 < EMA50  (EMA 역배열)
    필터:
      - ATR(14) ≤ ATR_SMA  (변동성 평균 이하)
    """
    _, _, bb_upper = _bb(df, 20, 2.0)
    if bb_upper is None:
        return False
    close = float(df["close"].iloc[-1])
    if close <= bb_upper:
        return False

    ema5  = _ema(df, 5)
    ema26 = _ema(df, 26)
    ema50 = _ema(df, 50)
    if ema5 is None or ema26 is None or ema50 is None:
        return False
    if not (ema5 < ema26 < ema50):
        return False

    atr_val, atr_sma_val = _atr(df, 14)
    if atr_val is None or atr_sma_val is None:
        return False
    if atr_val > atr_sma_val:
        return False

    return True


# ═══════════════════════════════════════════════════════════════
# entry_fn 이름 → 함수 매핑
# ═══════════════════════════════════════════════════════════════
ENTRY_FN_MAP = {
    # LONG 전략
    "entry_long_willr_bb_ema_stack":     entry_long_willr_bb_ema_stack,
    "entry_long_adx_willr_ema_stack":    entry_long_adx_willr_ema_stack,
    "entry_long_aroon_donchian_vol_inv": entry_long_aroon_donchian_vol_inv,
    "entry_long_ema_macd_psar":          entry_long_ema_macd_psar,
    "entry_long_ema_psar_mom":           entry_long_ema_psar_mom,
    # SHORT 전략
    "entry_short_willr_bb_obv":          entry_short_willr_bb_obv,
    "entry_short_sma_ichimoku_stddev":   entry_short_sma_ichimoku_stddev,
    "entry_short_obv_keltner_adx_inv":   entry_short_obv_keltner_adx_inv,
    "entry_short_bb_ema_stack":          entry_short_bb_ema_stack,
    "entry_short_bb_ema_stack_atr_inv":  entry_short_bb_ema_stack_atr_inv,
}
