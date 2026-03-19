"""
strategies/indicators.py — pandas_ta 래퍼  (v3.0)
각 지표 계산 함수. DataFrame을 받아 "long" / "short" / False 반환.

[v3.0] 백테스트 B등급 이상 검증 지표로 전면 교체
  - 제거: RSI, PSAR, WILLR, ICHIMOKU, EMA, SMA (B+등급 미달)
  - 유지+조정: OBV, CMF, VWAP, AROON, MOM, ROC, ADX, ATR_SIG, MFI, CCI
  - 신규: AD(누적/분포선), STDDEV(표준편차)
  - 임계값: 백테스트 indicators.py v3.8 기준에 맞춰 조정
    (예: CMF 0.05→0.1, ADX 20→25, RSI 60/40→제거)
"""

import pandas as pd
import pandas_ta as ta
import numpy as np


# ═══════════════════════════════════════════════════════════════
# 핵심 거래량 지표 (TOP50 등장 62회)
# ═══════════════════════════════════════════════════════════════

def calc_obv(df: pd.DataFrame):
    """OBV > OBV_SMA(20) → long, OBV < OBV_SMA(20) → short
    
    백테스트 근거: TOP50에 20회 등장, S/A등급 핵심 구성요소
    기존 v2.1과 동일 로직 (EMA20 → SMA20으로 변경하여 백테스트와 일치)
    """
    obv = ta.obv(df["close"], df["volume"])
    if obv is None or len(obv) < 20:
        return False
    obv_sma = ta.sma(obv, length=20)
    if obv_sma is None or len(obv_sma) < 20:
        return False
    obv_val = float(obv.iloc[-1])
    sma_val = float(obv_sma.iloc[-1])
    if obv_val > sma_val:
        return "long"
    if obv_val < sma_val:
        return "short"
    return False


def calc_cmf(df: pd.DataFrame, period: int = 20):
    """CMF(20) > +0.1 → long, CMF(20) < -0.1 → short
    
    백테스트 근거: TOP50에 11회 등장, A등급 ETH 1h SHORT(OOS 0.8668)
    임계값: 0.05 → 0.1 (백테스트 검증값, 더 강한 신호만 취급)
    """
    cmf = ta.cmf(df["high"], df["low"], df["close"], df["volume"], length=period)
    if cmf is None or len(cmf) < period:
        return False
    val = float(cmf.iloc[-1])
    if val > 0.1:
        return "long"
    if val < -0.1:
        return "short"
    return False


def calc_vwap(df: pd.DataFrame):
    """Close > VWAP(20) → long, Close < VWAP(20) → short
    
    백테스트 근거: TOP50에 18회 등장, 최고 평균 OOS(0.6510)
    S등급: ETH 1h LONG 2_OBV_VWAP (OOS 0.9442, 수익률 769%)
    """
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


def calc_ad(df: pd.DataFrame):
    """AD > AD_SMA(20) → long (매집 확대), AD < AD_SMA(20) → short (분산 확대)
    
    백테스트 근거: S등급 1위 — XRP 1h SHORT S_AD (OOS 0.9837, 수익률 943.59%)
    TOP50에 13회 등장. 가격-거래량 괴리를 포착하여 숨겨진 매집/분산 감지
    """
    ad = ta.ad(df["high"], df["low"], df["close"], df["volume"])
    if ad is None or len(ad) < 20:
        return False
    ad_sma = ta.sma(ad, length=20)
    if ad_sma is None or len(ad_sma) < 20:
        return False
    ad_val  = float(ad.iloc[-1])
    sma_val = float(ad_sma.iloc[-1])
    if ad_val > sma_val:
        return "long"
    if ad_val < sma_val:
        return "short"
    return False


# ═══════════════════════════════════════════════════════════════
# 모멘텀 지표
# ═══════════════════════════════════════════════════════════════

def calc_mom(df: pd.DataFrame, period: int = 10):
    """MOM(10) > 0 → long, MOM(10) < 0 → short
    
    백테스트 근거: A등급 BTC 1h LONG S_MOM (OOS 0.8871, 수익률 329%)
    TOP50에 8회 등장. 단순하지만 과적합 위험 최소
    """
    mom = ta.mom(df["close"], length=period)
    if mom is None or len(mom) < period:
        return False
    val = float(mom.iloc[-1])
    if val > 0:
        return "long"
    if val < 0:
        return "short"
    return False


def calc_roc(df: pd.DataFrame, period: int = 10):
    """ROC(10) > 0% → long, ROC(10) < 0% → short
    
    백테스트 근거: A등급 BTC 1h LONG S_ROC (OOS 0.8871, 수익률 329%)
    MOM의 비율 버전. period=12→10 (백테스트 기준과 일치)
    임계값: 0.5→0 (백테스트에서 0% 기준이 더 좋은 성과)
    """
    roc = ta.roc(df["close"], length=period)
    if roc is None or len(roc) < period:
        return False
    val = float(roc.iloc[-1])
    if val > 0:
        return "long"
    if val < 0:
        return "short"
    return False


# ═══════════════════════════════════════════════════════════════
# 보조 신호 지표
# ═══════════════════════════════════════════════════════════════

def calc_aroon(df: pd.DataFrame, period: int = 25):
    """AroonUp(25) > 70 → long, AroonDown(25) > 70 → short
    
    백테스트 근거: A등급 BTC 15m LONG 3_CMF_AROON_ADX (OOS 0.8795)
    TOP50에 5회 등장. 추세 시작/종료 시점 포착
    """
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


def calc_cci(df: pd.DataFrame, period: int = 20):
    """CCI(20) < -100 → long (과매도 반등), CCI(20) > +100 → short (과매수 반락)
    
    백테스트 근거: A등급 XRP 15m SHORT 2_CMF_CCI (OOS 0.8206)
    B등급 다수. 평균 대비 가격 위치를 표준화하여 극단적 이탈 감지
    """
    cci = ta.cci(df["high"], df["low"], df["close"], length=period)
    if cci is None or len(cci) < period:
        return False
    val = float(cci.iloc[-1])
    if val < -100:
        return "long"
    if val > 100:
        return "short"
    return False


def calc_mfi(df: pd.DataFrame, period: int = 14):
    """MFI(14) < 20 → long (과매도), MFI(14) > 80 → short (과매수)
    
    백테스트 근거: B등급 XRP 1h LONG S_MFI (OOS 0.7864)
    임계값: 60/40 → 80/20 (백테스트 검증값, 극단치만 취급)
    """
    mfi = ta.mfi(df["high"], df["low"], df["close"], df["volume"], length=period)
    if mfi is None or len(mfi) < period:
        return False
    val = float(mfi.iloc[-1])
    if val < 20:
        return "long"
    if val > 80:
        return "short"
    return False


def calc_stddev(df: pd.DataFrame, period: int = 20):
    """STDDEV 팽창 & Close > SMA20 → long, STDDEV 팽창 & Close < SMA20 → short
    
    백테스트 근거: S등급 BTC 15m LONG 3_STDDEV_AD_ADX (OOS 0.9017, 수익률 300.87%)
    변동성 팽창 구간 + 추세 방향 결합. 스퀴즈 후 폭발 움직임 감지
    """
    stdev = ta.stdev(df["close"], length=period)
    if stdev is None or len(stdev) < period + 10:
        return False
    sma20 = ta.sma(df["close"], length=period)
    if sma20 is None or len(sma20) < period:
        return False
    # STDDEV의 EMA(20)로 팽창 여부 판단
    stdev_ema = ta.ema(stdev, length=period)
    if stdev_ema is None or len(stdev_ema) < period:
        return False
    
    current_std = float(stdev.iloc[-1])
    std_ema_val = float(stdev_ema.iloc[-1])
    close       = float(df["close"].iloc[-1])
    sma_val     = float(sma20.iloc[-1])
    
    # 변동성 팽창 조건: 현재 STDDEV > STDDEV의 EMA20
    if current_std > std_ema_val:
        if close > sma_val:
            return "long"
        if close < sma_val:
            return "short"
    return False


# ═══════════════════════════════════════════════════════════════
# 필터 지표 (추세 강도 / 변동성 활성 확인)
# ═══════════════════════════════════════════════════════════════

def calc_adx(df: pd.DataFrame, period: int = 14):
    """ADX(14) > 25 & DI+>DI- → long, ADX(14) > 25 & DI->DI+ → short
    
    백테스트 근거: S등급 BTC 1h LONG S_ADX (OOS 0.9110, 수익률 430%)
    TOP50에 13회 등장. 추세강도 확인 + DI 방향으로 진입 방향 결정
    임계값: 20→25 (백테스트 기준)
    """
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
    if adx_val > 25 and dip_val > dim_val:
        return "long"
    if adx_val > 25 and dim_val > dip_val:
        return "short"
    return False


def calc_atr_sig(df: pd.DataFrame, period: int = 14):
    """ATR(14) > ATR_SMA(20) → 변동성 활성, 가격 방향으로 롱/숏 결정
    
    백테스트 근거: A등급 BTC 15m LONG 3_AROON_AD_ATR_SIG (OOS 0.8847)
    B등급 다수 등장. ATR 상승 + 가격 vs SMA20 방향으로 진입
    """
    atr = ta.atr(df["high"], df["low"], df["close"], length=period)
    if atr is None or len(atr) < 21:
        return False
    atr_sma = ta.sma(atr, length=20)
    if atr_sma is None or len(atr_sma) < 20:
        return False
    atr_val     = float(atr.iloc[-1])
    atr_sma_val = float(atr_sma.iloc[-1])
    
    if atr_val <= atr_sma_val:
        return False   # 변동성 비활성 → 신호 없음
    
    # 방향 결정: Close vs SMA20
    sma20 = ta.sma(df["close"], length=20)
    if sma20 is None or len(sma20) < 20:
        return False
    close   = float(df["close"].iloc[-1])
    sma_val = float(sma20.iloc[-1])
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


# ═══════════════════════════════════════════════════════════════
# 지표 이름 → 함수 매핑
# ═══════════════════════════════════════════════════════════════
INDICATOR_MAP = {
    # 핵심 거래량 (62회/TOP50)
    "OBV":      calc_obv,
    "CMF":      calc_cmf,
    "VWAP":     calc_vwap,
    "AD":       calc_ad,       # v3.0 신규
    # 모멘텀
    "MOM":      calc_mom,
    "ROC":      calc_roc,
    # 보조
    "AROON":    calc_aroon,
    "CCI":      calc_cci,      # v3.0 신규
    "MFI":      calc_mfi,
    "STDDEV":   calc_stddev,   # v3.0 신규
    # 필터
    "ADX":      calc_adx,
    "ATR_SIG":  calc_atr_sig,
}
