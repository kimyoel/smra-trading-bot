"""
config_v4.py  –  v4.0  B등급 이상 검증 기반 설정
=================================================
변경점 (v3.x → v4.0):
    - TP/SL 그리드: 30조합 → 6조합 (80% 감소)
    - 최악 TP/SL 블랙리스트 추가 (SL 1.0% 전체 제거)
    - TF/방향 활성 매트릭스: 36슬롯 → 14슬롯 (61% 감소)
    - 5m 전체 비활성, BOTH 전략 전체 비활성
    - MAX_COMBO_SIZE = 3 유지 (625개 조합)
"""

# ═══════════════════════════════════════════════════════════════
# 최대 조합 크기 (1+2+3 지표 조합)
# ═══════════════════════════════════════════════════════════════
MAX_COMBO_SIZE = 3   # C(10,1)+C(10,2)+C(10,3) + 필터 = 625개


# ═══════════════════════════════════════════════════════════════
# TP/SL 그리드 (v4.0: 검증된 조합만)
# ═══════════════════════════════════════════════════════════════
# 근거: 백테스트 TP/SL 분석 결과
#   최적: TP 5.0/SL 2.0 (평균 OOS 0.6088, 수익률 33.85%)
#   차선: TP 5.0/SL 1.3, TP 5.0/SL 3.0, TP 3.0/SL 2.0
#   최악: TP 1.3/SL 1.0 (-36.55%), TP 5.0/SL 1.0 (-46.86%)

TPSL_GRID = {
    # 기본 그리드 (모든 심볼/TF에 적용)
    'default': {
        'tp': [3.0, 5.0],
        'sl': [1.5, 2.0, 3.0],
    },
    # 심볼별 최적화 그리드 (기본 대비 우선)
    'BTC_1h': {
        'tp': [5.0],
        'sl': [1.5, 2.0, 3.0],
    },
    'ETH_1h': {
        'tp': [3.0, 5.0],
        'sl': [2.0, 3.0],
    },
    'XRP_1h': {
        'tp': [3.0, 5.0],
        'sl': [1.5, 2.0, 3.0],
    },
    'BTC_15m': {
        'tp': [5.0],
        'sl': [3.0],      # BTC 15m은 TP5/SL3만 S/A등급
    },
    'ETH_4h': {
        'tp': [3.0, 5.0],
        'sl': [2.0, 3.0],
    },
    'XRP_4h': {
        'tp': [3.0, 5.0],
        'sl': [2.0, 3.0],
    },
}

# TP/SL 블랙리스트 (절대 사용 금지)
TPSL_BLACKLIST = [
    (1.3, 1.0),   # 평균 OOS 0.4698, 수익률 -36.55%
    (5.0, 1.0),   # 평균 OOS 0.4586, 수익률 -46.86%
    (1.5, 1.0),   # SL 1.0% 계열 전부 제거
    (2.0, 1.0),   # 급변 시 즉시 손절 → 승률 치명적
    (3.0, 1.0),
    (1.0, 1.0),
]


# ═══════════════════════════════════════════════════════════════
# 활성 TF/방향 매트릭스
# ═══════════════════════════════════════════════════════════════
# True = 백테스트/실전 운용 대상, False = 건너뜀
# 근거: 타임프레임별 평균 성과
#   5m:  평균 OOS 0.4859, 수익률 -38.10% → 전체 비활성
#   15m: 평균 OOS 0.5204 → BTC LONG + XRP SHORT만 선별
#   1h:  평균 OOS 0.6495, 수익률 +48.55% → 메인 TF
#   4h:  평균 OOS 0.6087 → ETH/XRP만 보조

ACTIVE_CONFIGS = {
    # ── BTC ──
    ('BTC', '5m',  'LONG'):  False,
    ('BTC', '5m',  'SHORT'): False,
    ('BTC', '5m',  'BOTH'):  False,
    ('BTC', '15m', 'LONG'):  True,    # S등급: 3_STDDEV_AD_ADX (0.9017)
    ('BTC', '15m', 'SHORT'): False,
    ('BTC', '15m', 'BOTH'):  False,
    ('BTC', '1h',  'LONG'):  True,    # S등급: S_ADX (0.9110)
    ('BTC', '1h',  'SHORT'): True,    # A등급: 2_OBV_MOM (0.8674)
    ('BTC', '1h',  'BOTH'):  False,   # BOTH 전체 비활성
    ('BTC', '4h',  'LONG'):  False,
    ('BTC', '4h',  'SHORT'): False,
    ('BTC', '4h',  'BOTH'):  False,

    # ── ETH ──
    ('ETH', '5m',  'LONG'):  False,
    ('ETH', '5m',  'SHORT'): False,
    ('ETH', '5m',  'BOTH'):  False,
    ('ETH', '15m', 'LONG'):  True,    # B등급: 2_AROON_CCI (0.7926)
    ('ETH', '15m', 'SHORT'): False,
    ('ETH', '15m', 'BOTH'):  False,
    ('ETH', '1h',  'LONG'):  True,    # S등급: 2_OBV_VWAP (0.9442)
    ('ETH', '1h',  'SHORT'): True,    # A등급: S_CMF (0.8668)
    ('ETH', '1h',  'BOTH'):  False,
    ('ETH', '4h',  'LONG'):  True,    # A등급: S_ADX (0.8322)
    ('ETH', '4h',  'SHORT'): True,    # B등급: 2_MOM_VWAP (0.7976)
    ('ETH', '4h',  'BOTH'):  False,

    # ── XRP ──
    ('XRP', '5m',  'LONG'):  False,
    ('XRP', '5m',  'SHORT'): False,
    ('XRP', '5m',  'BOTH'):  False,
    ('XRP', '15m', 'LONG'):  False,
    ('XRP', '15m', 'SHORT'): True,    # A등급: 2_CMF_CCI (0.8206)
    ('XRP', '15m', 'BOTH'):  False,
    ('XRP', '1h',  'LONG'):  True,    # A등급: 2_VWAP_STDDEV (0.8464)
    ('XRP', '1h',  'SHORT'): True,    # S등급: S_AD (0.9837)
    ('XRP', '1h',  'BOTH'):  False,
    ('XRP', '4h',  'LONG'):  True,    # A등급: 2_MOM_VWAP (0.8283)
    ('XRP', '4h',  'SHORT'): True,    # B등급: S_STDDEV (0.7870)
    ('XRP', '4h',  'BOTH'):  False,
}


# ═══════════════════════════════════════════════════════════════
# 우선 실전 투입 전략 목록 (등급순)
# ═══════════════════════════════════════════════════════════════
PRIORITY_STRATEGIES = [
    # Tier 1: S등급 (OOS >= 0.90) - 최우선 투입
    {'symbol': 'XRP', 'tf': '1h', 'dir': 'SHORT', 'combo': 'S_AD',            'tp': 5.0, 'sl': 3.0, 'oos': 0.9837, 'grade': 'S'},
    {'symbol': 'ETH', 'tf': '1h', 'dir': 'LONG',  'combo': '2_OBV_VWAP',     'tp': 5.0, 'sl': 3.0, 'oos': 0.9442, 'grade': 'S'},
    {'symbol': 'XRP', 'tf': '1h', 'dir': 'SHORT', 'combo': '2_VWAP_AD',      'tp': 5.0, 'sl': 3.0, 'oos': 0.9430, 'grade': 'S'},
    {'symbol': 'BTC', 'tf': '1h', 'dir': 'LONG',  'combo': 'S_ADX',          'tp': 5.0, 'sl': 1.5, 'oos': 0.9110, 'grade': 'S'},
    {'symbol': 'BTC', 'tf': '15m', 'dir': 'LONG', 'combo': '3_STDDEV_AD_ADX','tp': 5.0, 'sl': 3.0, 'oos': 0.9017, 'grade': 'S'},

    # Tier 2: A등급 상위 (OOS 0.85+) - 주력 보조
    {'symbol': 'BTC', 'tf': '1h', 'dir': 'LONG',  'combo': 'S_MOM',          'tp': 5.0, 'sl': 2.0, 'oos': 0.8871, 'grade': 'A'},
    {'symbol': 'XRP', 'tf': '1h', 'dir': 'SHORT', 'combo': '2_OBV_AD',      'tp': 5.0, 'sl': 3.0, 'oos': 0.8813, 'grade': 'A'},
    {'symbol': 'ETH', 'tf': '1h', 'dir': 'LONG',  'combo': '2_OBV_AD',      'tp': 5.0, 'sl': 2.0, 'oos': 0.8792, 'grade': 'A'},
    {'symbol': 'ETH', 'tf': '1h', 'dir': 'LONG',  'combo': '3_VWAP_AD_ADX', 'tp': 5.0, 'sl': 3.0, 'oos': 0.8760, 'grade': 'A'},
    {'symbol': 'BTC', 'tf': '1h', 'dir': 'SHORT', 'combo': '2_OBV_MOM',     'tp': 5.0, 'sl': 3.0, 'oos': 0.8674, 'grade': 'A'},
    {'symbol': 'ETH', 'tf': '1h', 'dir': 'SHORT', 'combo': 'S_CMF',         'tp': 3.0, 'sl': 2.0, 'oos': 0.8668, 'grade': 'A'},
    {'symbol': 'BTC', 'tf': '1h', 'dir': 'SHORT', 'combo': '2_OBV_VWAP',    'tp': 5.0, 'sl': 3.0, 'oos': 0.8649, 'grade': 'A'},

    # Tier 3: A등급 하위 (OOS 0.80~0.85) - 분산
    {'symbol': 'XRP', 'tf': '1h', 'dir': 'SHORT', 'combo': '2_MOM_VWAP',    'tp': 3.0, 'sl': 2.0, 'oos': 0.8640, 'grade': 'A'},
    {'symbol': 'ETH', 'tf': '1h', 'dir': 'SHORT', 'combo': '2_CMF_AD',      'tp': 5.0, 'sl': 3.0, 'oos': 0.8607, 'grade': 'A'},
    {'symbol': 'ETH', 'tf': '4h', 'dir': 'LONG',  'combo': 'S_ADX',         'tp': 5.0, 'sl': 2.0, 'oos': 0.8322, 'grade': 'A'},
    {'symbol': 'XRP', 'tf': '4h', 'dir': 'LONG',  'combo': '2_MOM_VWAP',    'tp': 5.0, 'sl': 3.0, 'oos': 0.8283, 'grade': 'A'},
    {'symbol': 'XRP', 'tf': '15m', 'dir': 'SHORT','combo': '2_CMF_CCI',     'tp': 5.0, 'sl': 3.0, 'oos': 0.8206, 'grade': 'A'},
]


# ═══════════════════════════════════════════════════════════════
# 포트폴리오 배분 (총 100%)
# ═══════════════════════════════════════════════════════════════
PORTFOLIO_ALLOCATION = {
    # BTC (35%)
    'BTC_1h_LONG_S_ADX':      0.15,   # S등급, 가장 안정
    'BTC_1h_LONG_S_MOM':      0.10,   # A등급 상위
    'BTC_1h_SHORT_2_OBV_MOM': 0.10,   # A등급

    # ETH (35%)
    'ETH_1h_LONG_2_OBV_VWAP': 0.15,  # S등급
    'ETH_1h_SHORT_S_CMF':     0.10,   # A등급
    'ETH_1h_LONG_2_OBV_AD':   0.10,   # A등급

    # XRP (30%)
    'XRP_1h_SHORT_S_AD':      0.15,   # S등급, 최고 성과
    'XRP_1h_SHORT_2_VWAP_AD': 0.10,   # S등급
    'XRP_1h_SHORT_2_OBV_AD':  0.05,   # A등급, 분산
}


def get_tpsl_grid(symbol: str, tf: str) -> list[tuple[float, float]]:
    """심볼/TF에 맞는 TP/SL 조합 리스트 반환"""
    key = f"{symbol}_{tf}"
    grid = TPSL_GRID.get(key, TPSL_GRID['default'])
    pairs = [(tp, sl) for tp in grid['tp'] for sl in grid['sl']]
    # 블랙리스트 필터링
    pairs = [(tp, sl) for tp, sl in pairs if (tp, sl) not in TPSL_BLACKLIST]
    return pairs


def is_active(symbol: str, tf: str, direction: str) -> bool:
    """해당 심볼/TF/방향이 활성화 되어있는지 확인"""
    return ACTIVE_CONFIGS.get((symbol, tf, direction), False)
