"""
indicators.py  –  v4.0  B등급 이상 검증 지표만 사용 (16개)
=========================================================
v4.0 변경 (v3.8 → v4.0):
    - 472개 백테스트 결과 기반 B등급(OOS>=0.70) 이상 전략에
      등장하지 않는 저성과 지표 11개 제거
    - 제거: SMA, EMA, MACD, RSI, STOCH, WILLR, BB, PSAR, ICHIMOKU, DONCHIAN, KELTNER
    - 유지: OBV, VWAP, AD, CMF, MOM, ROC, AROON, STDDEV, CCI, MFI (방향성 10개)
           + ADX, ATR_SIG, VOLUME, ADX_INV, ATR_INV, VOL_INV (필터 6개)
    - sig38 (N, 38) → sig22 (N, 22) 배열 축소  → 계산 성능 ~40% 향상
    - 조합 수: ~2,324개 → ~800개 (66% 감소)
    - 제거 근거:
        MACD:     평균 OOS 0.4598, 수익률 -46.44%  (전체 최하위)
        ICHIMOKU: 평균 OOS 0.4605  (분/시 차트 부적합)
        SMA:      평균 OOS 0.4914  (B+등급 0회 등장)
        RSI:      B+등급 독립 등장 0회 (과매수/과매도 단독 무효)
        STOCH:    B+등급 0회, RSI 대비 노이즈 취약
        WILLR:    RSI 수학적 동치, B+등급 0회
        BB:       B+등급 단독 0회, KELTNER과 함께 제거
        PSAR:     B+등급 1회(15m BOTH), 신호 빈도 부족
        DONCHIAN: B+등급 0회
        KELTNER:  B등급 일부(XRP SHORT)이나 단독 우위 없음

공개 API:
    compute_signals(df) → sig22: np.ndarray (N, 22) int8
                          atr  : np.ndarray (N,)    float32
                          close: np.ndarray (N,)    float32
    get_entries(sig22, indicators_str) → (long_mask, short_mask)
    combo_id_to_indicators(combo_id) → indicators_str
    get_combo_info(combo_id) → {'indicators', 'long_entry_cond', 'short_entry_cond', ...}
    FULL_IND_MAP     : dict  (지표 → long_col, short_col, is_filter)
    ENTRY_CONDITIONS : dict  (지표 → {'long': 설명, 'short': 설명})
    COMBO_LIST       : list[tuple]  (combo_id, indicators_str)
"""

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

# ═══════════════════════════════════════════════════════════════
# 지표 인덱스 맵  (v4.0: 16개 지표, 22컬럼)
# (long_col, short_col, is_filter)
# ═══════════════════════════════════════════════════════════════
FULL_IND_MAP = {
    # ── 핵심 거래량 지표 (TOP50 등장 20+18+13+11 = 62회) ──
    'OBV':      (0,  0,  False),   # col0:  OBV>SMA(+1) / OBV<SMA(-1)
    'CMF':      (1,  2,  False),   # col1:  CMF>+0.1(롱)  col2: CMF<-0.1(숏)
    'VWAP':     (3,  3,  False),   # col3:  Close>VWAP(+1) / Close<VWAP(-1)
    'AD':       (4,  4,  False),   # col4:  AD>AD_SMA(+1) / AD<AD_SMA(-1)

    # ── 모멘텀 지표 (TOP50 등장 8회) ──
    'MOM':      (5,  5,  False),   # col5:  MOM(10)>0(+1) / MOM(10)<0(-1)
    'ROC':      (6,  6,  False),   # col6:  ROC(10)>0%(+1) / ROC(10)<0%(-1)

    # ── 보조 신호 지표 ──
    'AROON':    (7,  7,  False),   # col7:  AroonUp>70(+1) / AroonDn>70(-1)
    'CCI':      (8,  9,  False),   # col8:  CCI<-100(롱)  col9: CCI>+100(숏)
    'MFI':      (10, 11, False),   # col10: MFI<20(롱)    col11: MFI>80(숏)
    'STDDEV':   (12, 12, False),   # col12: STDDEV팽창&Close>SMA(+1) / 팽창&Close<SMA(-1)

    # ── 필터 지표 (순방향 3개 + 역방향 3개) ──
    'ADX':      (13, 13, True),    # col13: ADX(14)>25 → +1 (추세강도)
    'ATR_SIG':  (14, 14, True),    # col14: ATR>ATR_SMA → +1 (변동성활성)
    'VOLUME':   (15, 15, True),    # col15: Vol>SMA*1.5 → +1 (거래량급증)
    'ADX_INV':  (16, 16, True),    # col16: ADX<=25 → +1 (횡보필터)
    'ATR_INV':  (17, 17, True),    # col17: ATR<=ATR_SMA → +1 (저변동성)
    'VOL_INV':  (18, 18, True),    # col18: Vol<=SMA*1.5 → +1 (거래량정상)
}

IND_NAMES = list(FULL_IND_MAP.keys())   # 16개

# ═══════════════════════════════════════════════════════════════
# 진입 조건 상세 설명  (v4.0: 유지 지표만)
# ═══════════════════════════════════════════════════════════════
ENTRY_CONDITIONS = {
    # ── 거래량 지표 ──
    'OBV': {
        'long' : 'OBV>OBV_SMA(20) (거래량 누적 상승추세)',
        'short': 'OBV<OBV_SMA(20) (거래량 누적 하락추세)',
    },
    'CMF': {
        'long' : 'CMF(20)>+0.1 (자금 순유입: 매집 우세)',
        'short': 'CMF(20)<-0.1 (자금 순유출: 분산 우세)',
    },
    'VWAP': {
        'long' : 'Close>VWAP(20) (종가가 VWAP 위: 매수세 우위)',
        'short': 'Close<VWAP(20) (종가가 VWAP 아래: 매도세 우위)',
    },
    'AD': {
        'long' : 'AD선>AD_SMA(20) (누적/분포선 상승: 매집 확대)',
        'short': 'AD선<AD_SMA(20) (누적/분포선 하락: 분산 확대)',
    },
    # ── 모멘텀 ──
    'MOM': {
        'long' : 'Momentum(10)>0 (10봉 전 대비 가격 상승)',
        'short': 'Momentum(10)<0 (10봉 전 대비 가격 하락)',
    },
    'ROC': {
        'long' : 'ROC(10)>0% (10봉 전 대비 변화율 양수)',
        'short': 'ROC(10)<0% (10봉 전 대비 변화율 음수)',
    },
    # ── 보조 ──
    'AROON': {
        'long' : 'AroonUp(25)>70 강한 상승추세 지속',
        'short': 'AroonDown(25)>70 강한 하락추세 지속',
    },
    'CCI': {
        'long' : 'CCI(20)<-100 과매도 구간 (평균 대비 저평가)',
        'short': 'CCI(20)>+100 과매수 구간 (평균 대비 고평가)',
    },
    'MFI': {
        'long' : 'MFI(14)<20 과매도 (거래량 가중 RSI 낮음)',
        'short': 'MFI(14)>80 과매수 (거래량 가중 RSI 높음)',
    },
    'STDDEV': {
        'long' : 'STDDEV(20) 팽창 & Close>SMA20 (변동성 확대 + 상승추세)',
        'short': 'STDDEV(20) 팽창 & Close<SMA20 (변동성 확대 + 하락추세)',
    },
    # ── 필터 (순방향) ──
    'ADX': {
        'long' : 'ADX(14)>25 추세강도 확인 [필터: 롱/숏 방향 모두 허용]',
        'short': 'ADX(14)>25 추세강도 확인 [필터: 롱/숏 방향 모두 허용]',
    },
    'ATR_SIG': {
        'long' : 'ATR(14)>ATR_SMA(20) 변동성 활성 [필터: 롱/숏 방향 모두 허용]',
        'short': 'ATR(14)>ATR_SMA(20) 변동성 활성 [필터: 롱/숏 방향 모두 허용]',
    },
    'VOLUME': {
        'long' : 'Volume>Volume_SMA(20)*1.5 거래량 급증 [필터: 롱/숏 방향 모두 허용]',
        'short': 'Volume>Volume_SMA(20)*1.5 거래량 급증 [필터: 롱/숏 방향 모두 허용]',
    },
    # ── 필터 (역방향) ──
    'ADX_INV': {
        'long' : 'ADX(14)<=25 횡보/약추세 구간 [역방향필터: 롱/숏 방향 모두 허용]',
        'short': 'ADX(14)<=25 횡보/약추세 구간 [역방향필터: 롱/숏 방향 모두 허용]',
    },
    'ATR_INV': {
        'long' : 'ATR(14)<=ATR_SMA(20) 저변동성 구간 [역방향필터: 롱/숏 방향 모두 허용]',
        'short': 'ATR(14)<=ATR_SMA(20) 저변동성 구간 [역방향필터: 롱/숏 방향 모두 허용]',
    },
    'VOL_INV': {
        'long' : 'Volume<=Volume_SMA(20)*1.5 거래량 정상 구간 [역방향필터: 롱/숏 방향 모두 허용]',
        'short': 'Volume<=Volume_SMA(20)*1.5 거래량 정상 구간 [역방향필터: 롱/숏 방향 모두 허용]',
    },
}

# ═══════════════════════════════════════════════════════════════
# 지표 파라미터 (v4.0: 유지 지표만)
# ═══════════════════════════════════════════════════════════════
INDICATOR_PARAMS = {
    'OBV':      'sma_period=20                   |  조건: OBV>OBV_SMA(롱) / OBV<OBV_SMA(숏)',
    'CMF':      'period=20, threshold=0.1        |  조건: CMF>+0.1(롱) / CMF<-0.1(숏)',
    'VWAP':     'period=20                       |  조건: Close>VWAP(롱) / Close<VWAP(숏)',
    'AD':       'sma_period=20                   |  조건: AD>AD_SMA(롱매집) / AD<AD_SMA(숏분산)',
    'MOM':      'period=10                       |  조건: MOM>0(롱상승) / MOM<0(숏하락)',
    'ROC':      'period=10                       |  조건: ROC>0%(롱) / ROC<0%(숏)',
    'AROON':    'period=25, threshold=70         |  조건: AroonUp>70(롱) / AroonDown>70(숏)',
    'CCI':      'period=20, threshold=100        |  조건: CCI<-100(롱과매도) / CCI>+100(숏과매수)',
    'MFI':      'period=14, threshold=20/80      |  조건: MFI<20(롱과매도) / MFI>80(숏과매수)',
    'STDDEV':   'period=20, ema_period=20        |  조건: STDDEV팽창+Close>SMA(롱) / STDDEV팽창+Close<SMA(숏)',
    'ADX':      'period=14, threshold=25         |  조건: ADX>25 (추세 강도)',
    'ATR_SIG':  'atr_period=14, sma_period=20    |  조건: ATR>ATR_SMA (고변동성)',
    'VOLUME':   'sma_period=20, spike_mult=1.5   |  조건: Volume>SMA*1.5 (거래량급증)',
    'ADX_INV':  'period=14, threshold=25         |  조건: ADX<=25 (횡보/약추세)',
    'ATR_INV':  'atr_period=14, sma_period=20    |  조건: ATR<=ATR_SMA (저변동성)',
    'VOL_INV':  'sma_period=20, spike_mult=1.5   |  조건: Volume<=SMA*1.5 (거래량정상)',
}

# ═══════════════════════════════════════════════════════════════
# 콤팩트 진입 표현식  (v4.0)
# ═══════════════════════════════════════════════════════════════
ENTRY_SHORT_EXPR: dict[str, dict] = {
    # ─ 거래량 ─
    "OBV":      {"long": "OBV>OBV_SMA(20)",     "short": "OBV<OBV_SMA(20)"},
    "CMF":      {"long": "CMF(20)>0.1",         "short": "CMF(20)<-0.1"},
    "VWAP":     {"long": "Close>VWAP(20)",       "short": "Close<VWAP(20)"},
    "AD":       {"long": "AD>AD_SMA(20)",        "short": "AD<AD_SMA(20)"},
    # ─ 모멘텀 ─
    "MOM":      {"long": "MOM(10)>0",           "short": "MOM(10)<0"},
    "ROC":      {"long": "ROC(10)>0%",          "short": "ROC(10)<0%"},
    # ─ 보조 ─
    "AROON":    {"long": "AroonUp(25)>70",      "short": "AroonDn(25)>70"},
    "CCI":      {"long": "CCI(20)<-100",        "short": "CCI(20)>+100"},
    "MFI":      {"long": "MFI(14)<20",          "short": "MFI(14)>80"},
    "STDDEV":   {"long": "STD↑&Close>SMA(20)",  "short": "STD↑&Close<SMA(20)"},
    # ─ 필터 (순방향) ─
    "ADX":      {"filter": "ADX(14)>25"},
    "ATR_SIG":  {"filter": "ATR(14)>ATR_SMA"},
    "VOLUME":   {"filter": "Vol>SMA(20)*1.5"},
    # ─ 필터 (역방향) ─
    "ADX_INV":  {"filter": "ADX(14)≤25"},
    "ATR_INV":  {"filter": "ATR(14)≤ATR_SMA"},
    "VOL_INV":  {"filter": "Vol≤SMA(20)*1.5"},
}

SHORT_COND: dict[str, tuple[str, str]] = {
    'OBV':      ('OBV>OBV_SMA(20)',       'OBV<OBV_SMA(20)'),
    'CMF':      ('CMF(20)>+0.1',          'CMF(20)<-0.1'),
    'VWAP':     ('Close>VWAP(20)',        'Close<VWAP(20)'),
    'AD':       ('AD>AD_SMA(20)',         'AD<AD_SMA(20)'),
    'MOM':      ('MOM(10)>0↑',           'MOM(10)<0↓'),
    'ROC':      ('ROC(10)>0%↑',          'ROC(10)<0%↓'),
    'AROON':    ('AroonUp(25)>70',        'AroonDn(25)>70'),
    'CCI':      ('CCI(20)<-100',          'CCI(20)>+100'),
    'MFI':      ('MFI(14)<20',            'MFI(14)>80'),
    'STDDEV':   ('STDDEV↑&Close>SMA20',  'STDDEV↑&Close<SMA20'),
    'ADX':      ('[ADX(14)>25]',          '[ADX(14)>25]'),
    'ATR_SIG':  ('[ATR>ATR_SMA]',         '[ATR>ATR_SMA]'),
    'VOLUME':   ('[Vol>VolSMA×1.5]',      '[Vol>VolSMA×1.5]'),
    'ADX_INV':  ('[ADX(14)≤25]',         '[ADX(14)≤25]'),
    'ATR_INV':  ('[ATR≤ATR_SMA(20)]',    '[ATR≤ATR_SMA(20)]'),
    'VOL_INV':  ('[Vol≤VolSMA×1.5]',     '[Vol≤VolSMA×1.5]'),
}

SHORT_PARAMS: dict[str, str] = {
    'OBV':      'OBV(SMA20)',
    'CMF':      'CMF(20,th=0.1)',
    'VWAP':     'VWAP(20)',
    'AD':       'AD(SMA20)',
    'MOM':      'MOM(10)',
    'ROC':      'ROC(10)',
    'AROON':    'AROON(25,th=70)',
    'CCI':      'CCI(20,th=100)',
    'MFI':      'MFI(14)',
    'STDDEV':   'STDDEV(20)',
    'ADX':      'ADX(14,>25)',
    'ATR_SIG':  'ATR(14,SMA20)',
    'VOLUME':   'VOL(SMA20,×1.5)',
    'ADX_INV':  'ADX_INV(14,≤25)',
    'ATR_INV':  'ATR_INV(14,SMA20)',
    'VOL_INV':  'VOL_INV(SMA20,×1.5)',
}

# ── 상호 배타 쌍 (동일 콤보에 함께 포함 불가) ──
MUTUAL_EXCLUSIVE_PAIRS = [
    ('ADX',     'ADX_INV'),
    ('ATR_SIG', 'ATR_INV'),
    ('VOLUME',  'VOL_INV'),
]


# ═══════════════════════════════════════════════════════════════
# combo_id ↔ indicators_str 변환
# ═══════════════════════════════════════════════════════════════
def combo_id_to_indicators(combo_id: str) -> str:
    """
    combo_id 포맷으로부터 indicators_str 복원.
    예: 'S_AD' → 'AD', '2_OBV_VWAP' → 'OBV|VWAP'
    """
    parts = combo_id.split('_')
    prefix = parts[0]
    if prefix == 'S':
        return '_'.join(parts[1:])
    try:
        n = int(prefix)
    except ValueError:
        return combo_id
    remainder = parts[1:]
    inds_out = []
    i = 0
    while i < len(remainder) and len(inds_out) < n:
        if i + 1 < len(remainder):
            two = remainder[i] + '_' + remainder[i+1]
            if two in FULL_IND_MAP:
                inds_out.append(two)
                i += 2
                continue
        inds_out.append(remainder[i])
        i += 1
    return '|'.join(inds_out) if inds_out else combo_id


def get_combo_info(combo_id: str) -> dict:
    """
    combo_id → 지표명·롱조건·숏조건 딕셔너리 반환.  (v4.0: 축소 지표 세트)
    """
    indicators_str = combo_id_to_indicators(combo_id)
    inds = [x.strip() for x in indicators_str.split('|')]

    main_longs   = []
    main_shorts  = []
    filter_exprs = []

    for ind in inds:
        expr = ENTRY_SHORT_EXPR.get(ind, {})
        if not expr:
            info = ENTRY_CONDITIONS.get(ind, {})
            if FULL_IND_MAP.get(ind, (0, 0, False))[2]:
                filter_exprs.append(ind)
            else:
                main_longs.append(info.get('long', ind)[:40])
                main_shorts.append(info.get('short', ind)[:40])
            continue
        if 'filter' in expr:
            filter_exprs.append(expr['filter'])
        else:
            main_longs.append(expr.get('long', ind))
            main_shorts.append(expr.get('short', ind))

    sep = ' & '
    long_str  = sep.join(main_longs)
    short_str = sep.join(main_shorts)
    filter_str = ' & '.join(filter_exprs)

    if filter_str:
        long_str  = f"{long_str} [{filter_str}]"  if long_str  else f"[{filter_str}]"
        short_str = f"{short_str} [{filter_str}]" if short_str else f"[{filter_str}]"

    l_part = sep.join(main_longs)
    s_part = sep.join(main_shorts)
    parts = []
    if l_part:  parts.append(f"[L]{l_part}")
    if s_part:  parts.append(f"[S]{s_part}")
    if filter_str: parts.append(f"[F]{filter_str}")
    entry_rule = "  ".join(parts)

    _COMPACT_PARAMS = {
        'OBV':      'sma=20',
        'CMF':      'p=20,thr=0.1',
        'VWAP':     'p=20',
        'AD':       'sma=20',
        'MOM':      'p=10',
        'ROC':      'p=10',
        'AROON':    'p=25,thr=70',
        'CCI':      'p=20,thr=100',
        'MFI':      'p=14',
        'STDDEV':   'p=20',
        'ADX':      'p=14,thr=25',
        'ATR_SIG':  'atr=14,sma=20',
        'VOLUME':   'sma=20,mul=1.5',
        'ADX_INV':  'p=14,thr=25',
        'ATR_INV':  'atr=14,sma=20',
        'VOL_INV':  'sma=20,mul=1.5',
    }
    params_parts = [f"{ind}:{_COMPACT_PARAMS.get(ind, '?')}" for ind in inds]
    params_str   = ' | '.join(params_parts)

    return {
        'indicators'      : indicators_str,
        'long_entry_cond' : long_str,
        'short_entry_cond': short_str,
        'indicator_params': params_str,
        'entry_rule'      : entry_rule,
    }


# ═══════════════════════════════════════════════════════════════
# 기초 계산 유틸 (변경 없음)
# ═══════════════════════════════════════════════════════════════
def fast_sma(x, n):
    r = np.full(len(x), np.nan, dtype=np.float32)
    if len(x) < n:
        return r
    cs = np.cumsum(np.concatenate([[0.], x.astype(np.float64)]))
    r[n-1:] = (cs[n:] - cs[:len(x)-n+1]) / n
    return r


def fast_ema_pd(x, span):
    return pd.Series(x).ewm(span=span, adjust=False).mean().values.astype(np.float32)


def fast_atr(h, l, c, n=14):
    tr = np.maximum(
        h[1:] - l[1:],
        np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1]))
    )
    atr = pd.Series(tr).ewm(alpha=1/n, adjust=False).mean().values.astype(np.float32)
    return np.concatenate([[np.nan], atr])


# ═══════════════════════════════════════════════════════════════
# v4.0: 핵심 신호 계산 (19컬럼 = 방향성 13 + 필터 6)
# ═══════════════════════════════════════════════════════════════

def _compute_core_signals(close, high, low, vol, N, atr14):
    """
    v4.0 핵심: B등급 이상 검증 지표만 계산
    반환: (N, 19) int8   (col 0~18)

    col 0:  OBV       (+1/-1)
    col 1:  CMF long  (+1/0)
    col 2:  CMF short (-1/0)
    col 3:  VWAP      (+1/-1)
    col 4:  AD        (+1/-1)
    col 5:  MOM       (+1/-1)
    col 6:  ROC       (+1/-1)
    col 7:  AROON     (+1/-1)
    col 8:  CCI long  (+1/0)
    col 9:  CCI short (-1/0)
    col 10: MFI long  (+1/0)
    col 11: MFI short (-1/0)
    col 12: STDDEV    (+1/-1)
    col 13: ADX       (필터 +1/0)
    col 14: ATR_SIG   (필터 +1/0)
    col 15: VOLUME    (필터 +1/0)
    col 16: ADX_INV   (필터 +1/0)
    col 17: ATR_INV   (필터 +1/0)
    col 18: VOL_INV   (필터 +1/0)
    """
    sig = np.zeros((N, 19), dtype=np.int8)

    # ── col 0: OBV 추세 ──
    obv_diff = np.sign(np.diff(close.astype(np.float64), prepend=close[0]))
    obv      = np.cumsum(obv_diff * vol.astype(np.float64))
    obv_sma  = fast_sma(obv.astype(np.float32), 20)
    sig[:, 0] = np.where(obv > obv_sma, np.int8(1),
                np.where(obv < obv_sma, np.int8(-1), np.int8(0)))
    del obv, obv_sma, obv_diff

    # ── col 1,2: CMF(20) ──
    mf_mult = ((close - low) - (high - close)) / (high - low + 1e-10)
    mfv     = mf_mult * vol.astype(np.float64)
    cmf     = (pd.Series(mfv).rolling(20).sum() /
               pd.Series(vol.astype(np.float64)).rolling(20).sum()).values.astype(np.float32)
    sig[:, 1] = np.where(cmf >  0.1, np.int8(1),  np.int8(0))
    sig[:, 2] = np.where(cmf < -0.1, np.int8(-1), np.int8(0))
    del mf_mult, mfv, cmf

    # ── col 3: VWAP(20) ──
    tpv = (high + low + close) / 3.0 * vol
    if N >= 20:
        sw_tpv = sliding_window_view(tpv.astype(np.float64), 20)
        sw_vol = sliding_window_view(vol.astype(np.float64),  20)
        r_tpv  = np.concatenate([np.full(19, np.nan), sw_tpv.sum(axis=1)])
        r_vol  = np.concatenate([np.full(19, np.nan), sw_vol.sum(axis=1)])
        del sw_tpv, sw_vol
    else:
        r_tpv = np.full(N, np.nan, dtype=np.float64)
        r_vol = np.full(N, np.nan, dtype=np.float64)
    vwap = (r_tpv / (r_vol + 1e-10)).astype(np.float32)
    sig[:, 3] = np.where(close > vwap, np.int8(1),
                np.where(close < vwap, np.int8(-1), np.int8(0)))
    del tpv, r_tpv, r_vol, vwap

    # ── col 4: AD (Accumulation/Distribution) ──
    hl_range = high.astype(np.float64) - low.astype(np.float64)
    hl_safe  = np.where(hl_range > 1e-10, hl_range, 1.0)
    clv      = np.where(hl_range > 1e-10,
                        ((close.astype(np.float64) - low.astype(np.float64)) -
                         (high.astype(np.float64) - close.astype(np.float64))) / hl_safe,
                        0.)
    ad_line  = np.cumsum(clv * vol.astype(np.float64)).astype(np.float32)
    ad_sma   = fast_sma(ad_line, 20)
    ad_sma_safe = np.where(np.isnan(ad_sma), ad_line, ad_sma)
    sig[:, 4] = np.where(ad_line > ad_sma_safe, np.int8(1),
                np.where(ad_line < ad_sma_safe, np.int8(-1), np.int8(0)))
    del hl_range, hl_safe, clv, ad_line, ad_sma, ad_sma_safe

    # ── col 5: MOM(10) ──
    mom = np.concatenate([np.zeros(10), close[10:] - close[:-10]]).astype(np.float32)
    sig[:, 5] = np.where(mom > 0, np.int8(1),
                np.where(mom < 0, np.int8(-1), np.int8(0)))
    del mom

    # ── col 6: ROC(10) ──
    roc = np.concatenate([np.zeros(10),
          (close[10:] - close[:-10]) / (close[:-10] + 1e-10) * 100]).astype(np.float32)
    sig[:, 6] = np.where(roc > 0, np.int8(1),
                np.where(roc < 0, np.int8(-1), np.int8(0)))
    del roc

    # ── col 7: AROON(25) ──
    n_aroon = 25
    if N > n_aroon:
        hw = sliding_window_view(high[:N], n_aroon + 1)
        lw = sliding_window_view(low[:N],  n_aroon + 1)
        au = np.argmax(hw, axis=1).astype(np.float32) / n_aroon * 100
        ad_ar = np.argmin(lw, axis=1).astype(np.float32) / n_aroon * 100
        sig[n_aroon:, 7] = np.where(au > 70, np.int8(1),
                           np.where(ad_ar > 70, np.int8(-1), np.int8(0)))

    # ── col 8,9: CCI(20) ──
    n_cci = 20
    tp  = (high + low + close) / 3.0
    stp = fast_sma(tp, n_cci)
    if N >= n_cci:
        swv      = sliding_window_view(tp.astype(np.float64), n_cci)
        row_mean = swv.mean(axis=1)
        mad_sw   = np.abs(swv - row_mean[:, None]).mean(axis=1).astype(np.float32)
        mad      = np.concatenate([np.zeros(n_cci-1, dtype=np.float32), mad_sw])
    else:
        mad = np.zeros(N, dtype=np.float32)
    cci = np.where(mad > 1e-10, (tp - stp) / (0.015 * mad), 0.).astype(np.float32)
    sig[:, 8] = np.where(cci < -100, np.int8(1),  np.int8(0))
    sig[:, 9] = np.where(cci >  100, np.int8(-1), np.int8(0))
    del tp, stp, mad, cci

    # ── col 10,11: MFI(14) ──
    tp2  = (high + low + close) / 3.0
    mf   = tp2 * vol
    diff = np.diff(tp2, prepend=tp2[0])
    pmf  = pd.Series(np.where(diff >= 0, mf, 0.)).rolling(14).sum().values
    nmf  = pd.Series(np.where(diff <  0, mf, 0.)).rolling(14).sum().values
    mfi  = np.where(nmf > 0, 100. - 100. / (1. + pmf / (nmf + 1e-10)), 100.).astype(np.float32)
    sig[:, 10] = np.where(mfi < 20, np.int8(1),  np.int8(0))
    sig[:, 11] = np.where(mfi > 80, np.int8(-1), np.int8(0))
    del tp2, mf, diff, pmf, nmf, mfi

    # ── col 12: STDDEV(20) ──
    std20 = pd.Series(close.astype(np.float64)).rolling(20).std().values.astype(np.float32)
    std20_safe = np.where(np.isnan(std20), 0., std20)
    std_ema = fast_ema_pd(std20_safe, 20)
    sma20   = fast_sma(close, 20)
    sma20_safe = np.where(np.isnan(sma20), close, sma20)
    vol_expanding = std20_safe > std_ema
    sig[:, 12] = np.where(vol_expanding & (close > sma20_safe), np.int8(1),
                 np.where(vol_expanding & (close < sma20_safe), np.int8(-1), np.int8(0)))
    del std20, std20_safe, std_ema, sma20, sma20_safe, vol_expanding

    # ── col 13: ADX 필터 (ADX>25 → 추세 존재) ──
    a14 = np.where(np.isnan(atr14), 1e-10, atr14).astype(np.float64)
    dm_p = np.where((high[1:] - high[:-1]) > (low[:-1] - low[1:]),
                    np.maximum(high[1:] - high[:-1], 0.), 0.)
    dm_n = np.where((low[:-1] - low[1:]) > (high[1:] - high[:-1]),
                    np.maximum(low[:-1] - low[1:], 0.), 0.)
    dm_p = np.concatenate([[0.], dm_p])
    dm_n = np.concatenate([[0.], dm_n])
    di_p = fast_ema_pd(dm_p / (a14 + 1e-10), 14) * 100
    di_n = fast_ema_pd(dm_n / (a14 + 1e-10), 14) * 100
    dx   = np.abs(di_p - di_n) / (di_p + di_n + 1e-10) * 100
    adx  = fast_ema_pd(dx, 14)
    sig[:, 13] = np.where(adx > 25, np.int8(1), np.int8(0))
    del dm_p, dm_n, di_p, di_n, dx

    # ── col 14: ATR_SIG 필터 (ATR > ATR_SMA20) ──
    atr_sma = fast_sma(np.where(np.isnan(atr14), 0., atr14).astype(np.float32), 20)
    sig[:, 14] = np.where(atr14 > atr_sma, np.int8(1), np.int8(0))

    # ── col 15: VOLUME 필터 ──
    vs = fast_sma(vol.astype(np.float32), 20)
    sig[:, 15] = np.where(vol > vs * 1.5, np.int8(1), np.int8(0))

    # ── col 16: ADX_INV (ADX<=25) ──
    sig[:, 16] = np.where(adx <= 25., np.int8(1), np.int8(0))
    del adx

    # ── col 17: ATR_INV (ATR<=ATR_SMA) ──
    atr_sma_safe = np.where(np.isnan(atr_sma), atr14, atr_sma)
    sig[:, 17] = np.where(atr14 <= atr_sma_safe, np.int8(1), np.int8(0))
    del atr_sma, atr_sma_safe

    # ── col 18: VOL_INV (Vol<=SMA*1.5) ──
    vol_sma_safe = np.where(np.isnan(vs), vol, vs)
    sig[:, 18] = np.where(
        vol.astype(np.float64) <= vol_sma_safe.astype(np.float64) * 1.5,
        np.int8(1), np.int8(0)
    )
    del vs, vol_sma_safe

    return sig


# ═══════════════════════════════════════════════════════════════
# 메인 공개 함수
# ═══════════════════════════════════════════════════════════════
def compute_signals(df: pd.DataFrame):
    """
    DataFrame → (sig19, atr, close)
    df 필수 컬럼: open, high, low, close, volume

    v4.0: 38컬럼 → 19컬럼 (검증 지표만)
    """
    df.columns = [c.lower() for c in df.columns]
    N     = len(df)
    close = df['close'].values.astype(np.float32)
    high  = df['high'].values.astype(np.float32)
    low   = df['low'].values.astype(np.float32)
    vol   = df.get('volume', pd.Series(np.ones(N))).values.astype(np.float32)

    atr14 = fast_atr(high, low, close, 14)

    sig19 = _compute_core_signals(close, high, low, vol, N, atr14)

    return sig19, atr14.astype(np.float32), close


# ═══════════════════════════════════════════════════════════════
# 진입 신호 추출
# ═══════════════════════════════════════════════════════════════
def get_entries(sig: np.ndarray, indicators_str: str):
    """
    indicators_str: 'OBV|VWAP|ADX' 형태
    반환: (long_mask, short_mask) bool arrays or (None, None)
    """
    inds = [x.strip() for x in indicators_str.split('|')]
    N    = sig.shape[0]
    lm   = np.ones(N, dtype=np.bool_)
    sm   = np.ones(N, dtype=np.bool_)
    fm   = np.ones(N, dtype=np.bool_)
    has_filter = False

    for ind in inds:
        if ind not in FULL_IND_MAP:
            return None, None
        lc, sc, isf = FULL_IND_MAP[ind]
        if isf:
            fm &= (sig[:, lc] > 0)
            has_filter = True
        else:
            lm &= (sig[:, lc] == 1)
            sm &= (sig[:, sc] == -1)

    if has_filter:
        lm &= fm
        sm &= fm

    return lm, sm


# ═══════════════════════════════════════════════════════════════
# 콤보 리스트 로딩  (v4.0: 축소 지표 세트)
# ═══════════════════════════════════════════════════════════════
def load_combo_list(data_dir: str):
    """
    v4.0: 16개 지표(방향성 10 + 필터 6) 기반 조합 생성
    ──────────────────────────────────────────────────────
    MAX_COMBO_SIZE = 2  → C(10,1)+C(10,2) = 55개  + 필터조합
    MAX_COMBO_SIZE = 3  → +C(10,3) = 175개 기본   + 필터조합
    기존 ~2,324개 → ~800개 (66% 감소)

    제약 조건:
        - 비필터(방향성) 지표 1개 이상 필수
        - 상호 배타 쌍(ADX+ADX_INV 등) 동시 포함 금지
    """
    import os
    from itertools import combinations

    try:
        from config import MAX_COMBO_SIZE
    except ImportError:
        MAX_COMBO_SIZE = 3

    csv_path = os.path.join(data_dir, 'backtest_all_results.csv')
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path, usecols=['combo_id', 'indicators'])
            pairs = df[['combo_id', 'indicators']].drop_duplicates().values.tolist()
            print(f"[IND v4.0] 콤보 {len(pairs)}개 로드 (backtest_all_results.csv)")
            return pairs
        except Exception as e:
            print(f"[WARN] combo CSV 로드 실패: {e} → 자동 생성")

    all_inds = IND_NAMES   # 16개
    combos   = []
    counts   = {}

    filter_set = {k for k, v in FULL_IND_MAP.items() if v[2]}

    def _has_mutual_exclusive(group):
        g_set = set(group)
        for a, b in MUTUAL_EXCLUSIVE_PAIRS:
            if a in g_set and b in g_set:
                return True
        return False

    for n in range(1, MAX_COMBO_SIZE + 1):
        prefix = "S" if n == 1 else str(n)
        n_raw  = 0
        n_skip = 0
        for group in combinations(all_inds, n):
            n_raw += 1
            has_direction = any(g not in filter_set for g in group)
            if not has_direction:
                n_skip += 1
                continue
            if _has_mutual_exclusive(group):
                n_skip += 1
                continue
            combo_id       = f"{prefix}_{'_'.join(group)}"
            indicators_str = "|".join(group)
            combos.append((combo_id, indicators_str))
        counts[n] = n_raw - n_skip

    detail = ", ".join(
        f"{'단일' if n==1 else f'{n}조합'}={counts[n]}"
        for n in sorted(counts)
    )
    filter_removed = sum(
        1 for n in range(1, MAX_COMBO_SIZE + 1)
        for group in combinations(all_inds, n)
        if all(g in filter_set for g in group)
    )
    mutex_removed = sum(
        1 for n in range(1, MAX_COMBO_SIZE + 1)
        for group in combinations(all_inds, n)
        if not all(g in filter_set for g in group) and _has_mutual_exclusive(group)
    )
    print(f"[IND v4.0] 자동 생성 콤보: {len(combos)}개  ({detail})  "
          f"[MAX_COMBO_SIZE={MAX_COMBO_SIZE}, 필터전용 {filter_removed}개 + 상호배타 {mutex_removed}개 제거]")
    print(f"[IND v4.0] 지표 16개 (방향성 10 + 필터 6) — 저성과 11개 지표 제거 완료")
    return combos
