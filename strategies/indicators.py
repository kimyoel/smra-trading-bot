"""
strategies/indicators.py — WFA 전략별 복합 진입 조건 함수 (v5.5.1)

[v5.5.1] _ichimoku() 헬퍼 Tenkan/Kijun 컬럼 매핑 버그 수정
  - 기존: ISA_(Senkou Span A)를 Tenkan으로, ISB_(Senkou Span B)를 Kijun으로 잘못 매핑
  - 수정: ITS_(Tenkan-sen 전환선), IKS_(Kijun-sen 기준선)으로 올바르게 변경
  - 영향: Ichimoku 사용 5개 전략 진입 신호 정확도 개선

[v5.5] ETHUSDT 5분봉 WFA 전략 진입 함수 10개 추가
  - ETHUSDT_5m_WFA_Report.docx 기반
  - LONG 5개 + SHORT 5개 (ETH 5분봉 전용)
  - 모든 지표 헬퍼는 기존 BTC와 공유 (심볼 무관 — df 기반)

[v5.4] 4시간봉 WFA 전략 진입 함수 10개 추가
  - BTCUSDT_4h_WFA_Report.docx 기반
  - 새 지표 헬퍼: CMF (Chaikin Money Flow)
  - LONG 5개 + SHORT 5개 (4시간봉 전용)

[v5.3] 1시간봉 WFA 전략 진입 함수 10개 추가
  - BTCUSDT_1h_WFA_Report.docx 기반
  - 새 지표 헬퍼: ROC (Rate of Change)
  - LONG 5개 + SHORT 5개 (1시간봉 전용)

[v5.2] 5분봉 WFA 전략 진입 함수 10개 추가
  - BTCUSDT_5m_WFA_Report.docx 기반
  - 새 지표 헬퍼: RSI, Stochastic, CCI, VWAP(HLCC/4), AD, MFI
  - LONG 5개 + SHORT 5개 (5분봉 전용)

[v5.0] WFA OOS 보고서 기반 전면 교체
  - 15분봉 전략별 복합 진입 함수 (entry_fn) → True/False 반환

지표 구현 목록:
  15m: Williams %R, BB, EMA Stack, ADX, Aroon, Donchian, Volume, MACD, PSAR, MOM,
       OBV, SMA, Ichimoku, STDDEV, Keltner, ATR
  5m:  + RSI, Stochastic(%K), CCI, VWAP(HLCC/4 SMA), AD(Accumulation/Distribution), MFI
  1h:  + ROC (Rate of Change)
  4h:  + CMF (Chaikin Money Flow)
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
    """이치모쿠 Tenkan(9)/Kijun(26) 반환

    pandas_ta 컬럼 매핑:
      ITS_9  = Tenkan-sen (전환선, 9기간 고저 중간값)
      IKS_26 = Kijun-sen  (기준선, 26기간 고저 중간값)
      ISA_9  = Senkou Span A (선행스팬A) — 사용하지 않음
      ISB_26 = Senkou Span B (선행스팬B) — 사용하지 않음
    """
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
    # ITS_ = Tenkan-sen (전환선), IKS_ = Kijun-sen (기준선)
    # 주의: ISA_ = Senkou Span A, ISB_ = Senkou Span B — 이들은 Tenkan/Kijun이 아님!
    tenkan_col = [c for c in ich_df.columns if c.startswith("ITS_")]
    kijun_col  = [c for c in ich_df.columns if c.startswith("IKS_")]
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
# 5분봉 추가 헬퍼: RSI, Stochastic, CCI, VWAP, AD, MFI
# ═══════════════════════════════════════════════════════════════

def _rsi(df: pd.DataFrame, period: int = 14):
    """RSI 계산, 최신값 반환"""
    rsi = ta.rsi(df["close"], length=period)
    if rsi is None or len(rsi) < period:
        return None
    val = float(rsi.iloc[-1])
    if np.isnan(val):
        return None
    return val


def _stoch_k(df: pd.DataFrame, period: int = 14):
    """Stochastic %K 계산, (current, previous) 반환 — 상향 전환 감지용"""
    stoch = ta.stoch(df["high"], df["low"], df["close"], k=period, d=3)
    if stoch is None or stoch.empty:
        return None, None
    k_col = [c for c in stoch.columns if c.startswith("STOCHk_")]
    if not k_col:
        return None, None
    k_series = stoch[k_col[0]]
    if len(k_series) < 2:
        return None, None
    curr = float(k_series.iloc[-1])
    prev = float(k_series.iloc[-2])
    if np.isnan(curr) or np.isnan(prev):
        return None, None
    return curr, prev


def _cci(df: pd.DataFrame, period: int = 20):
    """CCI 계산, 최신값 반환"""
    cci = ta.cci(df["high"], df["low"], df["close"], length=period)
    if cci is None or len(cci) < period:
        return None
    val = float(cci.iloc[-1])
    if np.isnan(val):
        return None
    return val


def _vwap_sma(df: pd.DataFrame, period: int = 20):
    """간이 VWAP: HLCC/4 가중평균 SMA 계산, 최신값 반환"""
    hlcc4 = (df["high"] + df["low"] + df["close"] + df["close"]) / 4
    vwap = ta.sma(hlcc4, length=period)
    if vwap is None or len(vwap) < period:
        return None
    val = float(vwap.iloc[-1])
    if np.isnan(val):
        return None
    return val


def _ad(df: pd.DataFrame):
    """Accumulation/Distribution, (ad_val, ad_sma_val) 반환"""
    ad = ta.ad(df["high"], df["low"], df["close"], df["volume"])
    if ad is None or len(ad) < 20:
        return None, None
    ad_sma = ta.sma(ad, length=20)
    if ad_sma is None or len(ad_sma) < 20:
        return None, None
    ad_val = float(ad.iloc[-1])
    sma_val = float(ad_sma.iloc[-1])
    if np.isnan(ad_val) or np.isnan(sma_val):
        return None, None
    return ad_val, sma_val


def _mfi(df: pd.DataFrame, period: int = 14):
    """MFI (Money Flow Index), 최신값 반환"""
    mfi = ta.mfi(df["high"], df["low"], df["close"], df["volume"], length=period)
    if mfi is None or len(mfi) < period:
        return None
    val = float(mfi.iloc[-1])
    if np.isnan(val):
        return None
    return val


# ═══════════════════════════════════════════════════════════════
# 5분봉 LONG 전략 진입 함수 (5개)
# ═══════════════════════════════════════════════════════════════

def entry_long_5m_bb_ema_stack_vol_inv(df: pd.DataFrame) -> bool:
    """
    5m LONG #1: 3_BB_EMA_STACK_VOL_INV (Score 14.28)
    진입: Close<BB_lo(20,2) AND EMA5>EMA26>EMA50
    필터: Vol≤SMA(20)*1.5
    """
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


def entry_long_5m_macd_ichimoku_stddev(df: pd.DataFrame) -> bool:
    """
    5m LONG #2: 3_MACD_ICHIMOKU_STDDEV (Score 12.54)
    진입: MACD>Sig(12,26,9) AND Tenkan>Kijun AND STD↑ AND Close>SMA(20)
    """
    macd_val, signal_val, _ = _macd(df, 12, 26, 9)
    if macd_val is None or signal_val is None:
        return False
    if macd_val <= signal_val:
        return False

    tenkan, kijun = _ichimoku(df)
    if tenkan is None or kijun is None:
        return False
    if tenkan <= kijun:
        return False

    _, _, is_expanding = _stddev(df, 20)
    if not is_expanding:
        return False

    close = float(df["close"].iloc[-1])
    sma20 = _sma(df, "close", 20)
    if sma20 is None:
        return False
    if close <= sma20:
        return False

    return True


def entry_long_5m_stoch_cci_ema_stack(df: pd.DataFrame) -> bool:
    """
    5m LONG #3: 3_STOCH_CCI_EMA_STACK (Score 12.07)
    진입: %K(14)<20 상향전환 AND CCI(20)<-100 AND EMA5>EMA26>EMA50
    """
    k_curr, k_prev = _stoch_k(df, 14)
    if k_curr is None or k_prev is None:
        return False
    # %K < 20 이면서 이전봉보다 상승 (상향 전환)
    if k_curr >= 20 or k_curr <= k_prev:
        return False

    cci_val = _cci(df, 20)
    if cci_val is None or cci_val >= -100:
        return False

    ema5  = _ema(df, 5)
    ema26 = _ema(df, 26)
    ema50 = _ema(df, 50)
    if ema5 is None or ema26 is None or ema50 is None:
        return False
    if not (ema5 > ema26 > ema50):
        return False

    return True


def entry_long_5m_cci_vwap_ad(df: pd.DataFrame) -> bool:
    """
    5m LONG #4: 3_CCI_VWAP_AD (Score 11.17)
    진입: CCI(20)<-100 AND Close>VWAP(20) AND AD>AD_SMA(20)
    """
    cci_val = _cci(df, 20)
    if cci_val is None or cci_val >= -100:
        return False

    close = float(df["close"].iloc[-1])
    vwap = _vwap_sma(df, 20)
    if vwap is None:
        return False
    if close <= vwap:
        return False

    ad_val, ad_sma_val = _ad(df)
    if ad_val is None or ad_sma_val is None:
        return False
    if ad_val <= ad_sma_val:
        return False

    return True


def entry_long_5m_rsi_cci_ema_stack(df: pd.DataFrame) -> bool:
    """
    5m LONG #5: 3_RSI_CCI_EMA_STACK (Score 11.04)
    진입: RSI(14)<30 AND CCI(20)<-100 AND EMA5>EMA26>EMA50
    """
    rsi_val = _rsi(df, 14)
    if rsi_val is None or rsi_val >= 30:
        return False

    cci_val = _cci(df, 20)
    if cci_val is None or cci_val >= -100:
        return False

    ema5  = _ema(df, 5)
    ema26 = _ema(df, 26)
    ema50 = _ema(df, 50)
    if ema5 is None or ema26 is None or ema50 is None:
        return False
    if not (ema5 > ema26 > ema50):
        return False

    return True


# ═══════════════════════════════════════════════════════════════
# 5분봉 SHORT 전략 진입 함수 (5개)
# ═══════════════════════════════════════════════════════════════

def entry_short_5m_rsi_willr_ema_stack(df: pd.DataFrame) -> bool:
    """
    5m SHORT #1: 3_RSI_WILLR_EMA_STACK (Score 13.26)
    진입: RSI(14)>70 AND WR(14)>-20 AND EMA5<EMA26<EMA50
    """
    rsi_val = _rsi(df, 14)
    if rsi_val is None or rsi_val <= 70:
        return False

    wr = _willr(df, 14)
    if wr is None or wr <= -20:
        return False

    ema5  = _ema(df, 5)
    ema26 = _ema(df, 26)
    ema50 = _ema(df, 50)
    if ema5 is None or ema26 is None or ema50 is None:
        return False
    if not (ema5 < ema26 < ema50):
        return False

    return True


def entry_short_5m_ema_ichimoku_volume(df: pd.DataFrame) -> bool:
    """
    5m SHORT #2: 3_EMA_ICHIMOKU_VOLUME (Score 12.41)
    진입: EMA12<EMA26 AND Tenkan<Kijun
    필터: Vol>SMA(20)*1.5
    """
    ema12 = _ema(df, 12)
    ema26 = _ema(df, 26)
    if ema12 is None or ema26 is None:
        return False
    if ema12 >= ema26:
        return False

    tenkan, kijun = _ichimoku(df)
    if tenkan is None or kijun is None:
        return False
    if tenkan >= kijun:
        return False

    vol_sma = ta.sma(df["volume"], length=20)
    if vol_sma is None or len(vol_sma) < 20:
        return False
    vol_sma_val = float(vol_sma.iloc[-1])
    if np.isnan(vol_sma_val):
        return False
    current_vol = float(df["volume"].iloc[-1])
    if current_vol <= vol_sma_val * 1.5:
        return False

    return True


def entry_short_5m_rsi_ema_stack(df: pd.DataFrame) -> bool:
    """
    5m SHORT #3: 2_RSI_EMA_STACK (Score 12.05)
    진입: RSI(14)>70 AND EMA5<EMA26<EMA50
    """
    rsi_val = _rsi(df, 14)
    if rsi_val is None or rsi_val <= 70:
        return False

    ema5  = _ema(df, 5)
    ema26 = _ema(df, 26)
    ema50 = _ema(df, 50)
    if ema5 is None or ema26 is None or ema50 is None:
        return False
    if not (ema5 < ema26 < ema50):
        return False

    return True


def entry_short_5m_rsi_ema_stack_atr_inv(df: pd.DataFrame) -> bool:
    """
    5m SHORT #4: 3_RSI_EMA_STACK_ATR_INV (Score 12.05)
    진입: RSI(14)>70 AND EMA5<EMA26<EMA50
    필터: ATR(14)≤ATR_SMA
    """
    rsi_val = _rsi(df, 14)
    if rsi_val is None or rsi_val <= 70:
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


def entry_short_5m_psar_mfi_stddev(df: pd.DataFrame) -> bool:
    """
    5m SHORT #5: 3_PSAR_MFI_STDDEV (Score 11.50)
    진입: SAR↓(0.02,0.2) AND MFI(14)>80 AND STD↑ AND Close<SMA(20)
    """
    psar_dir = _psar(df)
    if psar_dir != "short":
        return False

    mfi_val = _mfi(df, 14)
    if mfi_val is None or mfi_val <= 80:
        return False

    _, _, is_expanding = _stddev(df, 20)
    if not is_expanding:
        return False

    close = float(df["close"].iloc[-1])
    sma20 = _sma(df, "close", 20)
    if sma20 is None:
        return False
    if close >= sma20:
        return False

    return True


# ═══════════════════════════════════════════════════════════════
# 1시간봉 추가 헬퍼: ROC
# ═══════════════════════════════════════════════════════════════

def _roc(df: pd.DataFrame, period: int = 10):
    """Rate of Change 계산, 최신값 반환 (%)"""
    roc = ta.roc(df["close"], length=period)
    if roc is None or len(roc) < period:
        return None
    val = float(roc.iloc[-1])
    if np.isnan(val):
        return None
    return val


# ═══════════════════════════════════════════════════════════════
# 1시간봉 LONG 전략 진입 함수 (5개)
# ═══════════════════════════════════════════════════════════════

def entry_long_1h_sma_stddev_ema_stack(df: pd.DataFrame) -> bool:
    """
    1h LONG #1: 3_SMA_STDDEV_EMA_STACK (Score 22.99)
    진입: SMA10>SMA20 AND STD↑&Close>SMA(20) AND EMA5>EMA26>EMA50
    """
    sma10 = _sma(df, "close", 10)
    sma20 = _sma(df, "close", 20)
    if sma10 is None or sma20 is None:
        return False
    if sma10 <= sma20:
        return False

    _, _, is_expanding = _stddev(df, 20)
    if not is_expanding:
        return False

    close = float(df["close"].iloc[-1])
    if close <= sma20:
        return False

    ema5  = _ema(df, 5)
    ema26 = _ema(df, 26)
    ema50 = _ema(df, 50)
    if ema5 is None or ema26 is None or ema50 is None:
        return False
    if not (ema5 > ema26 > ema50):
        return False

    return True


def entry_long_1h_ema_stddev_adx_inv(df: pd.DataFrame) -> bool:
    """
    1h LONG #2: 3_EMA_STDDEV_ADX_INV (Score 22.40)
    진입: EMA12>EMA26 AND STD↑&Close>SMA(20)
    필터: ADX(14)≤25
    """
    ema12 = _ema(df, 12)
    ema26 = _ema(df, 26)
    if ema12 is None or ema26 is None:
        return False
    if ema12 <= ema26:
        return False

    _, _, is_expanding = _stddev(df, 20)
    if not is_expanding:
        return False

    close = float(df["close"].iloc[-1])
    sma20 = _sma(df, "close", 20)
    if sma20 is None:
        return False
    if close <= sma20:
        return False

    adx = _adx_value(df, 14)
    if adx is None or adx > 25:
        return False

    return True


def entry_long_1h_psar_aroon_mom(df: pd.DataFrame) -> bool:
    """
    1h LONG #3: 3_PSAR_AROON_MOM (Score 22.25)
    진입: SAR↑(0.02,0.2) AND AroonUp(25)>70 AND MOM(10)>0
    """
    psar_dir = _psar(df)
    if psar_dir != "long":
        return False

    aroon_up, _ = _aroon(df, 25)
    if aroon_up is None or aroon_up <= 70:
        return False

    mom_val = _mom(df, 10)
    if mom_val is None or mom_val <= 0:
        return False

    return True


def entry_long_1h_psar_aroon_vwap(df: pd.DataFrame) -> bool:
    """
    1h LONG #4: 3_PSAR_AROON_VWAP (Score 22.25)
    진입: SAR↑(0.02,0.2) AND AroonUp(25)>70 AND Close>VWAP(20)
    """
    psar_dir = _psar(df)
    if psar_dir != "long":
        return False

    aroon_up, _ = _aroon(df, 25)
    if aroon_up is None or aroon_up <= 70:
        return False

    close = float(df["close"].iloc[-1])
    vwap = _vwap_sma(df, 20)
    if vwap is None:
        return False
    if close <= vwap:
        return False

    return True


def entry_long_1h_psar_aroon_roc(df: pd.DataFrame) -> bool:
    """
    1h LONG #5: 3_PSAR_AROON_ROC (Score 22.25)
    진입: SAR↑(0.02,0.2) AND AroonUp(25)>70 AND ROC(10)>0%
    """
    psar_dir = _psar(df)
    if psar_dir != "long":
        return False

    aroon_up, _ = _aroon(df, 25)
    if aroon_up is None or aroon_up <= 70:
        return False

    roc_val = _roc(df, 10)
    if roc_val is None or roc_val <= 0:
        return False

    return True


# ═══════════════════════════════════════════════════════════════
# 1시간봉 SHORT 전략 진입 함수 (5개)
# ═══════════════════════════════════════════════════════════════

def entry_short_1h_adx_rsi_willr(df: pd.DataFrame) -> bool:
    """
    1h SHORT #1: 3_ADX_RSI_WILLR (Score 23.27)
    진입: RSI(14)>70 AND WR(14)>-20
    필터: ADX(14)>25
    """
    rsi_val = _rsi(df, 14)
    if rsi_val is None or rsi_val <= 70:
        return False

    wr = _willr(df, 14)
    if wr is None or wr <= -20:
        return False

    adx = _adx_value(df, 14)
    if adx is None or adx <= 25:
        return False

    return True


def entry_short_1h_adx_rsi_vol_inv(df: pd.DataFrame) -> bool:
    """
    1h SHORT #2: 3_ADX_RSI_VOL_INV (Score 22.44)
    진입: RSI(14)>70
    필터: ADX(14)>25 AND Vol≤SMA(20)*1.5
    """
    rsi_val = _rsi(df, 14)
    if rsi_val is None or rsi_val <= 70:
        return False

    adx = _adx_value(df, 14)
    if adx is None or adx <= 25:
        return False

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


def entry_short_1h_macd_stddev_vol_inv(df: pd.DataFrame) -> bool:
    """
    1h SHORT #3: 3_MACD_STDDEV_VOL_INV (Score 22.18)
    진입: MACD<Sig(12,26,9) AND STD↑&Close<SMA(20)
    필터: Vol≤SMA(20)*1.5
    """
    macd_val, signal_val, _ = _macd(df, 12, 26, 9)
    if macd_val is None or signal_val is None:
        return False
    if macd_val >= signal_val:
        return False

    _, _, is_expanding = _stddev(df, 20)
    if not is_expanding:
        return False

    close = float(df["close"].iloc[-1])
    sma20 = _sma(df, "close", 20)
    if sma20 is None:
        return False
    if close >= sma20:
        return False

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


def entry_short_1h_bb_mfi_adx_inv(df: pd.DataFrame) -> bool:
    """
    1h SHORT #4: 3_BB_MFI_ADX_INV (Score 22.11)
    진입: Close>BB_hi(20,2) AND MFI(14)>80
    필터: ADX(14)≤25
    """
    _, _, bb_upper = _bb(df, 20, 2.0)
    if bb_upper is None:
        return False
    close = float(df["close"].iloc[-1])
    if close <= bb_upper:
        return False

    mfi_val = _mfi(df, 14)
    if mfi_val is None or mfi_val <= 80:
        return False

    adx = _adx_value(df, 14)
    if adx is None or adx > 25:
        return False

    return True


def entry_short_1h_cci_ema_stack(df: pd.DataFrame) -> bool:
    """
    1h SHORT #5: 2_CCI_EMA_STACK (Score 20.80)
    진입: CCI(20)>+100 AND EMA5<EMA26<EMA50
    """
    cci_val = _cci(df, 20)
    if cci_val is None or cci_val <= 100:
        return False

    ema5  = _ema(df, 5)
    ema26 = _ema(df, 26)
    ema50 = _ema(df, 50)
    if ema5 is None or ema26 is None or ema50 is None:
        return False
    if not (ema5 < ema26 < ema50):
        return False

    return True


# ═══════════════════════════════════════════════════════════════
# 4시간봉 추가 헬퍼: CMF
# ═══════════════════════════════════════════════════════════════

def _cmf(df: pd.DataFrame, period: int = 20):
    """Chaikin Money Flow 계산, 최신값 반환"""
    cmf = ta.cmf(df["high"], df["low"], df["close"], df["volume"], length=period)
    if cmf is None or len(cmf) < period:
        return None
    val = float(cmf.iloc[-1])
    if np.isnan(val):
        return None
    return val


# ═══════════════════════════════════════════════════════════════
# 4시간봉 LONG 전략 진입 함수 (5개)
# ═══════════════════════════════════════════════════════════════

def entry_long_4h_volume_vwap_stddev(df: pd.DataFrame) -> bool:
    """
    4h LONG #1: 3_VOLUME_VWAP_STDDEV (Score 23.02)
    진입: Close>VWAP(20) AND STD↑&Close>SMA(20) AND Vol>SMA(20)*1.5
    """
    close = float(df["close"].iloc[-1])
    vwap = _vwap_sma(df, 20)
    if vwap is None:
        return False
    if close <= vwap:
        return False

    _, _, is_expanding = _stddev(df, 20)
    if not is_expanding:
        return False

    sma20 = _sma(df, "close", 20)
    if sma20 is None:
        return False
    if close <= sma20:
        return False

    vol_sma = ta.sma(df["volume"], length=20)
    if vol_sma is None or len(vol_sma) < 20:
        return False
    vol_sma_val = float(vol_sma.iloc[-1])
    if np.isnan(vol_sma_val):
        return False
    current_vol = float(df["volume"].iloc[-1])
    if current_vol <= vol_sma_val * 1.5:
        return False

    return True


def entry_long_4h_aroon_volume_adx_inv(df: pd.DataFrame) -> bool:
    """
    4h LONG #2: 3_AROON_VOLUME_ADX_INV (Score 23.01)
    진입: AroonUp(25)>70 AND Vol>SMA(20)*1.5
    필터: ADX(14)≤25
    """
    aroon_up, _ = _aroon(df, 25)
    if aroon_up is None or aroon_up <= 70:
        return False

    vol_sma = ta.sma(df["volume"], length=20)
    if vol_sma is None or len(vol_sma) < 20:
        return False
    vol_sma_val = float(vol_sma.iloc[-1])
    if np.isnan(vol_sma_val):
        return False
    current_vol = float(df["volume"].iloc[-1])
    if current_vol <= vol_sma_val * 1.5:
        return False

    adx = _adx_value(df, 14)
    if adx is None or adx > 25:
        return False

    return True


def entry_long_4h_atr_sig_volume_vwap(df: pd.DataFrame) -> bool:
    """
    4h LONG #3: 3_ATR_SIG_VOLUME_VWAP (Score 22.48)
    진입: Close>VWAP(20) AND ATR>ATR_SMA(20) AND Vol>SMA(20)*1.5
    """
    close = float(df["close"].iloc[-1])
    vwap = _vwap_sma(df, 20)
    if vwap is None:
        return False
    if close <= vwap:
        return False

    atr_val, atr_sma_val = _atr(df, 14)
    if atr_val is None or atr_sma_val is None:
        return False
    if atr_val <= atr_sma_val:
        return False

    vol_sma = ta.sma(df["volume"], length=20)
    if vol_sma is None or len(vol_sma) < 20:
        return False
    vol_sma_val = float(vol_sma.iloc[-1])
    if np.isnan(vol_sma_val):
        return False
    current_vol = float(df["volume"].iloc[-1])
    if current_vol <= vol_sma_val * 1.5:
        return False

    return True


def entry_long_4h_volume_ema_stack_atr_inv(df: pd.DataFrame) -> bool:
    """
    4h LONG #4: 3_VOLUME_EMA_STACK_ATR_INV (Score 21.90)
    진입: EMA5>EMA26>EMA50 AND Vol>SMA(20)*1.5
    필터: ATR(14)≤ATR_SMA(20)
    """
    ema5  = _ema(df, 5)
    ema26 = _ema(df, 26)
    ema50 = _ema(df, 50)
    if ema5 is None or ema26 is None or ema50 is None:
        return False
    if not (ema5 > ema26 > ema50):
        return False

    vol_sma = ta.sma(df["volume"], length=20)
    if vol_sma is None or len(vol_sma) < 20:
        return False
    vol_sma_val = float(vol_sma.iloc[-1])
    if np.isnan(vol_sma_val):
        return False
    current_vol = float(df["volume"].iloc[-1])
    if current_vol <= vol_sma_val * 1.5:
        return False

    atr_val, atr_sma_val = _atr(df, 14)
    if atr_val is None or atr_sma_val is None:
        return False
    if atr_val > atr_sma_val:
        return False

    return True


def entry_long_4h_volume_ema_stack(df: pd.DataFrame) -> bool:
    """
    4h LONG #5: 2_VOLUME_EMA_STACK (Score 21.90)
    진입: EMA5>EMA26>EMA50 AND Vol>SMA(20)*1.5
    """
    ema5  = _ema(df, 5)
    ema26 = _ema(df, 26)
    ema50 = _ema(df, 50)
    if ema5 is None or ema26 is None or ema50 is None:
        return False
    if not (ema5 > ema26 > ema50):
        return False

    vol_sma = ta.sma(df["volume"], length=20)
    if vol_sma is None or len(vol_sma) < 20:
        return False
    vol_sma_val = float(vol_sma.iloc[-1])
    if np.isnan(vol_sma_val):
        return False
    current_vol = float(df["volume"].iloc[-1])
    if current_vol <= vol_sma_val * 1.5:
        return False

    return True


# ═══════════════════════════════════════════════════════════════
# 4시간봉 SHORT 전략 진입 함수 (5개)
# ═══════════════════════════════════════════════════════════════

def entry_short_4h_willr_atr_sig_mfi(df: pd.DataFrame) -> bool:
    """
    4h SHORT #1: 3_WILLR_ATR_SIG_MFI (Score 29.53)
    진입: WR(14)>-20 AND ATR>ATR_SMA(20) AND MFI(14)>80
    """
    wr = _willr(df, 14)
    if wr is None or wr <= -20:
        return False

    atr_val, atr_sma_val = _atr(df, 14)
    if atr_val is None or atr_sma_val is None:
        return False
    if atr_val <= atr_sma_val:
        return False

    mfi_val = _mfi(df, 14)
    if mfi_val is None or mfi_val <= 80:
        return False

    return True


def entry_short_4h_willr_bb_cci(df: pd.DataFrame) -> bool:
    """
    4h SHORT #2: 3_WILLR_BB_CCI (Score 24.03)
    진입: WR(14)>-20 AND Close>BB_hi(20,2) AND CCI(20)>+100
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

    cci_val = _cci(df, 20)
    if cci_val is None or cci_val <= 100:
        return False

    return True


def entry_short_4h_willr_bb(df: pd.DataFrame) -> bool:
    """
    4h SHORT #3: 2_WILLR_BB (Score 22.54)
    진입: WR(14)>-20 AND Close>BB_hi(20,2)
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

    return True


def entry_short_4h_willr_bb_atr_inv(df: pd.DataFrame) -> bool:
    """
    4h SHORT #4: 3_WILLR_BB_ATR_INV (Score 22.54)
    진입: WR(14)>-20 AND Close>BB_hi(20,2)
    필터: ATR(14)≤ATR_SMA(20)
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

    atr_val, atr_sma_val = _atr(df, 14)
    if atr_val is None or atr_sma_val is None:
        return False
    if atr_val > atr_sma_val:
        return False

    return True


def entry_short_4h_adx_cmf_vol_inv(df: pd.DataFrame) -> bool:
    """
    4h SHORT #5: 3_ADX_CMF_VOL_INV (Score 22.34)
    진입: ADX(14)>25 AND CMF(20)<-0.1 AND Vol≤SMA(20)*1.5
    """
    adx = _adx_value(df, 14)
    if adx is None or adx <= 25:
        return False

    cmf_val = _cmf(df, 20)
    if cmf_val is None or cmf_val >= -0.1:
        return False

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


# ═══════════════════════════════════════════════════════════════
# ETHUSDT 5분봉 LONG 전략 진입 함수 (5개)
# ═══════════════════════════════════════════════════════════════

def entry_long_eth5m_willr_ichimoku_aroon(df: pd.DataFrame) -> bool:
    """
    ETH 5m LONG #1: 3_WILLR_ICHIMOKU_AROON (Score 22.84)
    진입: WR(14)<-80 AND Tenkan>Kijun AND AroonUp(25)>70
    """
    wr = _willr(df, 14)
    if wr is None or wr >= -80:
        return False

    tenkan, kijun = _ichimoku(df)
    if tenkan is None or kijun is None:
        return False
    if tenkan <= kijun:
        return False

    aroon_up, _ = _aroon(df, 25)
    if aroon_up is None or aroon_up <= 70:
        return False

    return True


def entry_long_eth5m_adx_stoch_ema_stack(df: pd.DataFrame) -> bool:
    """
    ETH 5m LONG #2: 3_ADX_STOCH_EMA_STACK (Score 19.17)
    진입: %K(14)<20 상향전환 AND EMA5>EMA26>EMA50
    필터: ADX(14)>25
    """
    k_curr, k_prev = _stoch_k(df, 14)
    if k_curr is None or k_prev is None:
        return False
    if k_curr >= 20 or k_curr <= k_prev:
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


def entry_long_eth5m_sma_adx_psar(df: pd.DataFrame) -> bool:
    """
    ETH 5m LONG #3: 3_SMA_ADX_PSAR (Score 17.60)
    진입: SMA10>SMA20 AND SAR↑(0.02,0.2)
    필터: ADX(14)>25
    """
    sma10 = _sma(df, "close", 10)
    sma20 = _sma(df, "close", 20)
    if sma10 is None or sma20 is None:
        return False
    if sma10 <= sma20:
        return False

    psar_dir = _psar(df)
    if psar_dir != "long":
        return False

    adx = _adx_value(df, 14)
    if adx is None or adx <= 25:
        return False

    return True


def entry_long_eth5m_bb_atr_sig_ema_stack(df: pd.DataFrame) -> bool:
    """
    ETH 5m LONG #4: 3_BB_ATR_SIG_EMA_STACK (Score 17.24)
    진입: Close<BB_lo(20,2) AND EMA5>EMA26>EMA50
    필터: ATR(14)>ATR_SMA(20)
    """
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

    atr_val, atr_sma_val = _atr(df, 14)
    if atr_val is None or atr_sma_val is None:
        return False
    if atr_val <= atr_sma_val:
        return False

    return True


def entry_long_eth5m_rsi_ema_stack(df: pd.DataFrame) -> bool:
    """
    ETH 5m LONG #5: 2_RSI_EMA_STACK (Score 16.62)
    진입: RSI(14)<30 AND EMA5>EMA26>EMA50
    """
    rsi_val = _rsi(df, 14)
    if rsi_val is None or rsi_val >= 30:
        return False

    ema5  = _ema(df, 5)
    ema26 = _ema(df, 26)
    ema50 = _ema(df, 50)
    if ema5 is None or ema26 is None or ema50 is None:
        return False
    if not (ema5 > ema26 > ema50):
        return False

    return True


# ═══════════════════════════════════════════════════════════════
# ETHUSDT 5분봉 SHORT 전략 진입 함수 (5개)
# ═══════════════════════════════════════════════════════════════

def entry_short_eth5m_stoch_obv_mfi(df: pd.DataFrame) -> bool:
    """
    ETH 5m SHORT #1: 3_STOCH_OBV_MFI (Score 19.89)
    진입: %K(14)>80 하향전환 AND OBV<OBV_SMA(20) AND MFI(14)>80
    """
    k_curr, k_prev = _stoch_k(df, 14)
    if k_curr is None or k_prev is None:
        return False
    if k_curr <= 80 or k_curr >= k_prev:
        return False

    obv_val, obv_sma_val = _obv(df)
    if obv_val is None or obv_sma_val is None:
        return False
    if obv_val >= obv_sma_val:
        return False

    mfi_val = _mfi(df, 14)
    if mfi_val is None or mfi_val <= 80:
        return False

    return True


def entry_short_eth5m_sma_macd_stddev(df: pd.DataFrame) -> bool:
    """
    ETH 5m SHORT #2: 3_SMA_MACD_STDDEV (Score 17.23)
    진입: SMA10<SMA20 AND MACD<Sig(12,26,9) AND STD↑&Close<SMA(20)
    """
    sma10 = _sma(df, "close", 10)
    sma20 = _sma(df, "close", 20)
    if sma10 is None or sma20 is None:
        return False
    if sma10 >= sma20:
        return False

    macd_val, signal_val, _ = _macd(df, 12, 26, 9)
    if macd_val is None or signal_val is None:
        return False
    if macd_val >= signal_val:
        return False

    _, _, is_expanding = _stddev(df, 20)
    if not is_expanding:
        return False

    close = float(df["close"].iloc[-1])
    if close >= sma20:
        return False

    return True


def entry_short_eth5m_adx_rsi_ema_stack(df: pd.DataFrame) -> bool:
    """
    ETH 5m SHORT #3: 3_ADX_RSI_EMA_STACK (Score 16.34)
    진입: RSI(14)>70 AND EMA5<EMA26<EMA50
    필터: ADX(14)>25
    """
    rsi_val = _rsi(df, 14)
    if rsi_val is None or rsi_val <= 70:
        return False

    ema5  = _ema(df, 5)
    ema26 = _ema(df, 26)
    ema50 = _ema(df, 50)
    if ema5 is None or ema26 is None or ema50 is None:
        return False
    if not (ema5 < ema26 < ema50):
        return False

    adx = _adx_value(df, 14)
    if adx is None or adx <= 25:
        return False

    return True


def entry_short_eth5m_aroon_cci_ema_stack(df: pd.DataFrame) -> bool:
    """
    ETH 5m SHORT #4: 3_AROON_CCI_EMA_STACK (Score 16.16)
    진입: AroonDown(25)>70 AND CCI(20)>+100 AND EMA5<EMA26<EMA50
    """
    _, aroon_down = _aroon(df, 25)
    if aroon_down is None or aroon_down <= 70:
        return False

    cci_val = _cci(df, 20)
    if cci_val is None or cci_val <= 100:
        return False

    ema5  = _ema(df, 5)
    ema26 = _ema(df, 26)
    ema50 = _ema(df, 50)
    if ema5 is None or ema26 is None or ema50 is None:
        return False
    if not (ema5 < ema26 < ema50):
        return False

    return True


def entry_short_eth5m_adx_psar_ichimoku(df: pd.DataFrame) -> bool:
    """
    ETH 5m SHORT #5: 3_ADX_PSAR_ICHIMOKU (Score 15.38)
    진입: SAR↓(0.02,0.2) AND Tenkan<Kijun
    필터: ADX(14)>25
    """
    psar_dir = _psar(df)
    if psar_dir != "short":
        return False

    tenkan, kijun = _ichimoku(df)
    if tenkan is None or kijun is None:
        return False
    if tenkan >= kijun:
        return False

    adx = _adx_value(df, 14)
    if adx is None or adx <= 25:
        return False

    return True


# ═══════════════════════════════════════════════════════════════
# entry_fn 이름 → 함수 매핑
# ═══════════════════════════════════════════════════════════════
ENTRY_FN_MAP = {
    # 15m LONG 전략
    "entry_long_willr_bb_ema_stack":     entry_long_willr_bb_ema_stack,
    "entry_long_adx_willr_ema_stack":    entry_long_adx_willr_ema_stack,
    "entry_long_aroon_donchian_vol_inv": entry_long_aroon_donchian_vol_inv,
    "entry_long_ema_macd_psar":          entry_long_ema_macd_psar,
    "entry_long_ema_psar_mom":           entry_long_ema_psar_mom,
    # 15m SHORT 전략
    "entry_short_willr_bb_obv":          entry_short_willr_bb_obv,
    "entry_short_sma_ichimoku_stddev":   entry_short_sma_ichimoku_stddev,
    "entry_short_obv_keltner_adx_inv":   entry_short_obv_keltner_adx_inv,
    "entry_short_bb_ema_stack":          entry_short_bb_ema_stack,
    "entry_short_bb_ema_stack_atr_inv":  entry_short_bb_ema_stack_atr_inv,
    # 5m LONG 전략
    "entry_long_5m_bb_ema_stack_vol_inv":    entry_long_5m_bb_ema_stack_vol_inv,
    "entry_long_5m_macd_ichimoku_stddev":    entry_long_5m_macd_ichimoku_stddev,
    "entry_long_5m_stoch_cci_ema_stack":     entry_long_5m_stoch_cci_ema_stack,
    "entry_long_5m_cci_vwap_ad":             entry_long_5m_cci_vwap_ad,
    "entry_long_5m_rsi_cci_ema_stack":       entry_long_5m_rsi_cci_ema_stack,
    # 5m SHORT 전략
    "entry_short_5m_rsi_willr_ema_stack":    entry_short_5m_rsi_willr_ema_stack,
    "entry_short_5m_ema_ichimoku_volume":    entry_short_5m_ema_ichimoku_volume,
    "entry_short_5m_rsi_ema_stack":          entry_short_5m_rsi_ema_stack,
    "entry_short_5m_rsi_ema_stack_atr_inv":  entry_short_5m_rsi_ema_stack_atr_inv,
    "entry_short_5m_psar_mfi_stddev":        entry_short_5m_psar_mfi_stddev,
    # 1h LONG 전략
    "entry_long_1h_sma_stddev_ema_stack":    entry_long_1h_sma_stddev_ema_stack,
    "entry_long_1h_ema_stddev_adx_inv":      entry_long_1h_ema_stddev_adx_inv,
    "entry_long_1h_psar_aroon_mom":          entry_long_1h_psar_aroon_mom,
    "entry_long_1h_psar_aroon_vwap":         entry_long_1h_psar_aroon_vwap,
    "entry_long_1h_psar_aroon_roc":          entry_long_1h_psar_aroon_roc,
    # 1h SHORT 전략
    "entry_short_1h_adx_rsi_willr":          entry_short_1h_adx_rsi_willr,
    "entry_short_1h_adx_rsi_vol_inv":        entry_short_1h_adx_rsi_vol_inv,
    "entry_short_1h_macd_stddev_vol_inv":    entry_short_1h_macd_stddev_vol_inv,
    "entry_short_1h_bb_mfi_adx_inv":         entry_short_1h_bb_mfi_adx_inv,
    "entry_short_1h_cci_ema_stack":          entry_short_1h_cci_ema_stack,
    # 4h LONG 전략
    "entry_long_4h_volume_vwap_stddev":      entry_long_4h_volume_vwap_stddev,
    "entry_long_4h_aroon_volume_adx_inv":    entry_long_4h_aroon_volume_adx_inv,
    "entry_long_4h_atr_sig_volume_vwap":     entry_long_4h_atr_sig_volume_vwap,
    "entry_long_4h_volume_ema_stack_atr_inv": entry_long_4h_volume_ema_stack_atr_inv,
    "entry_long_4h_volume_ema_stack":        entry_long_4h_volume_ema_stack,
    # 4h SHORT 전략
    "entry_short_4h_willr_atr_sig_mfi":      entry_short_4h_willr_atr_sig_mfi,
    "entry_short_4h_willr_bb_cci":           entry_short_4h_willr_bb_cci,
    "entry_short_4h_willr_bb":               entry_short_4h_willr_bb,
    "entry_short_4h_willr_bb_atr_inv":       entry_short_4h_willr_bb_atr_inv,
    "entry_short_4h_adx_cmf_vol_inv":        entry_short_4h_adx_cmf_vol_inv,
    # ETH 5m LONG 전략
    "entry_long_eth5m_willr_ichimoku_aroon":  entry_long_eth5m_willr_ichimoku_aroon,
    "entry_long_eth5m_adx_stoch_ema_stack":   entry_long_eth5m_adx_stoch_ema_stack,
    "entry_long_eth5m_sma_adx_psar":          entry_long_eth5m_sma_adx_psar,
    "entry_long_eth5m_bb_atr_sig_ema_stack":  entry_long_eth5m_bb_atr_sig_ema_stack,
    "entry_long_eth5m_rsi_ema_stack":         entry_long_eth5m_rsi_ema_stack,
    # ETH 5m SHORT 전략
    "entry_short_eth5m_stoch_obv_mfi":        entry_short_eth5m_stoch_obv_mfi,
    "entry_short_eth5m_sma_macd_stddev":      entry_short_eth5m_sma_macd_stddev,
    "entry_short_eth5m_adx_rsi_ema_stack":    entry_short_eth5m_adx_rsi_ema_stack,
    "entry_short_eth5m_aroon_cci_ema_stack":  entry_short_eth5m_aroon_cci_ema_stack,
    "entry_short_eth5m_adx_psar_ichimoku":    entry_short_eth5m_adx_psar_ichimoku,
}
