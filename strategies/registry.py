"""
strategies/registry.py — WFA OOS 백테스트 검증 전략 레지스트리 (v5.0)

[v5.0] BTCUSDT_15m_WFA_Report.docx 기반 전면 교체
  - 기존 17개 다심볼 전략 → BTCUSDT 15m 전용 10개 전략
  - LONG 5개 + SHORT 5개 (WFA 황금기준 통과 상위 전략)
  - 선별 기준: survived_windows ≥ 5, avg_calmar ≥ 2.0, min_calmar ≥ 0.5
  - 종합 스코어: (survived_windows×2) + (min_calmar×3) + ln(1+avg_calmar)
  - 충돌 해소: Score 기반 순위 (config.py ALL_STRATEGIES 순서)

주요 변경:
  - 모든 전략이 BTCUSDT 15분봉 → 심볼/타임프레임 단일화
  - entry_fn 필드: 각 전략의 진입 조건 함수명 (strategies/indicators.py에 정의)
  - 기존 indicators 리스트 + AND 조건 → entry_fn 단일 함수로 교체
    (보고서의 복합 조건을 정확히 구현하기 위해)
  - score 필드: 충돌 시 우선순위 (높을수록 우선)
  - leverage: WFA 보고서에 레버리지 정보 없음 → 보수적 3x 기본값
  - max_hold_bars: 보고서 max_hold 컬럼 기반

TP/SL 타입:
  tp_type: "fixed" (고정 %)
  tp_mult: TP 비율 (소수, 예: 0.10 = 10%)
  sl_mult: SL 비율 (소수, 예: 0.025 = 2.5%)
"""

STRATEGY_REGISTRY = {

    # ═══════════════════════════════════════════════════════════
    # LONG 전략 — 상위 5개 (Score 순)
    # ═══════════════════════════════════════════════════════════

    # LONG #1 — 전체 2위 | 7윈도우 생존, 3중 컨펌 구조
    # 진입: WR(14)<-80 AND Close<BB_lower(20,2) AND EMA5>EMA26>EMA50
    # 해석: Williams %R 과매도 + BB 하단 이탈 + EMA 정배열 → 추세 추종형 평균 회귀
    "L1_WILLR_BB_EMA_STACK": {
        "id":             "L1_WILLR_BB_EMA_STACK",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_willr_bb_ema_stack",
        "score":          19.21,
        "survived_windows": 7,
        "avg_calmar":     3.649,
        "min_calmar":     1.223,
        "leverage":       3,
        "max_leverage":   5,
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.025,     # SL 2.5%
        "base_mdd":       0.025,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # LONG #2 — 전체 5위 | 안정성 LONG 1위 (min_calmar 2.451)
    # 진입: WR(14)<-80 AND EMA5>EMA26>EMA50
    # 필터: ADX(14)>25 (추세 강도 확인)
    "L2_ADX_WILLR_EMA_STACK": {
        "id":             "L2_ADX_WILLR_EMA_STACK",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_adx_willr_ema_stack",
        "score":          18.73,
        "survived_windows": 5,
        "avg_calmar":     2.953,
        "min_calmar":     2.451,
        "leverage":       3,
        "max_leverage":   5,
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.05,      # SL 5.0%
        "base_mdd":       0.05,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # LONG #3 — 전체 8위 | 저볼륨 돌파 특화
    # 진입: AroonUp(25)>70 AND Close>Donchian_upper(20)
    # 필터: Volume ≤ SMA(20)×1.5 (거래량 미급증 조건)
    "L3_AROON_DONCHIAN_VOL_INV": {
        "id":             "L3_AROON_DONCHIAN_VOL_INV",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_aroon_donchian_vol_inv",
        "score":          15.97,
        "survived_windows": 5,
        "avg_calmar":     2.044,
        "min_calmar":     1.619,
        "leverage":       3,
        "max_leverage":   5,
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.06,      # SL 6.0%
        "base_mdd":       0.06,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # LONG #4 — 전체 9위 | LONG 최고 avg_calmar 4.042
    # 진입: EMA12>EMA26 AND MACD>Signal(12,26,9) AND Parabolic SAR 상승 전환
    # 특징: max_hold 12봉(3시간) — 단기 포지션
    "L4_EMA_MACD_PSAR": {
        "id":             "L4_EMA_MACD_PSAR",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_ema_macd_psar",
        "score":          15.64,
        "survived_windows": 6,
        "avg_calmar":     4.042,
        "min_calmar":     0.675,
        "leverage":       3,
        "max_leverage":   5,
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.02,      # SL 2.0%
        "base_mdd":       0.02,
        "max_hold_bars":  12,        # 12봉 (3시간)
    },

    # LONG #5 — 전체 10위 | 고RR 타이트 손절형 (RR 24배)
    # 진입: EMA12>EMA26 AND Parabolic SAR 상승 전환 AND MOM(10)>0
    # 특징: SL 0.5% 극타이트 — 높은 손절 빈도, 한 번 적중 시 12% 수익
    "L5_EMA_PSAR_MOM": {
        "id":             "L5_EMA_PSAR_MOM",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_ema_psar_mom",
        "score":          15.53,
        "survived_windows": 5,
        "avg_calmar":     2.050,
        "min_calmar":     1.472,
        "leverage":       3,
        "max_leverage":   5,
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # ═══════════════════════════════════════════════════════════
    # SHORT 전략 — 상위 5개 (Score 순)
    # ═══════════════════════════════════════════════════════════

    # SHORT #1 — 전체 1위 | 종합 스코어 최고 (20.36)
    # 진입: WR(14)>-20 AND Close>BB_upper(20,2) AND OBV<OBV_SMA(20)
    # 해석: 가격(BB) + 모멘텀(WR) + 거래량(OBV) 3차원 숏 신호
    "S1_WILLR_BB_OBV": {
        "id":             "S1_WILLR_BB_OBV",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_willr_bb_obv",
        "score":          20.36,
        "survived_windows": 7,
        "avg_calmar":     8.013,
        "min_calmar":     1.387,
        "leverage":       3,
        "max_leverage":   5,
        "tp_type":        "fixed",
        "tp_mult":        0.03,      # TP 3.0%
        "sl_mult":        0.025,     # SL 2.5%
        "base_mdd":       0.025,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # SHORT #2 — 전체 3위 | avg_calmar 41.3 (이상치 주의)
    # 진입: SMA10<SMA20 AND Tenkan<Kijun AND STD상승 & Close<SMA(20)
    # 해석: SMA(추세) + 이치모쿠(전환선/기준선) + STDDEV(변동성 확장) 3중 조건
    "S2_SMA_ICHIMOKU_STDDEV": {
        "id":             "S2_SMA_ICHIMOKU_STDDEV",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_sma_ichimoku_stddev",
        "score":          19.36,
        "survived_windows": 6,
        "avg_calmar":     41.302,
        "min_calmar":     1.204,
        "leverage":       3,
        "max_leverage":   5,
        "tp_type":        "fixed",
        "tp_mult":        0.05,      # TP 5.0%
        "sl_mult":        0.04,      # SL 4.0%
        "base_mdd":       0.04,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # SHORT #3 — 전체 4위 | 횡보장 특화 역추세 (min_calmar 1.971 SHORT 최고)
    # 진입: OBV<OBV_SMA(20) AND Close>KC_upper(20,2)
    # 필터: ADX(14)≤25 (추세 약세 = 횡보장에서만 진입)
    "S3_OBV_KELTNER_ADX_INV": {
        "id":             "S3_OBV_KELTNER_ADX_INV",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_obv_keltner_adx_inv",
        "score":          18.98,
        "survived_windows": 5,
        "avg_calmar":     20.451,
        "min_calmar":     1.971,
        "leverage":       3,
        "max_leverage":   5,
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.04,      # SL 4.0%
        "base_mdd":       0.04,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # SHORT #4 — 전체 6위 | 7윈도우 안정형, 2지표 조합 (단순 = 강건)
    # 진입: Close>BB_upper(20,2) AND EMA5<EMA26<EMA50
    # 필터: 없음 (2지표 조합)
    "S4_BB_EMA_STACK": {
        "id":             "S4_BB_EMA_STACK",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_bb_ema_stack",
        "score":          18.73,
        "survived_windows": 7,
        "avg_calmar":     3.799,
        "min_calmar":     1.055,
        "leverage":       3,
        "max_leverage":   5,
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.03,      # SL 3.0%
        "base_mdd":       0.03,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # SHORT #5 — 전체 7위 | #4 ATR 필터 추가 버전
    # 진입: Close>BB_upper(20,2) AND EMA5<EMA26<EMA50
    # 필터: ATR(14) ≤ ATR_SMA (변동성 평균 이하)
    "S5_BB_EMA_STACK_ATR_INV": {
        "id":             "S5_BB_EMA_STACK_ATR_INV",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_bb_ema_stack_atr_inv",
        "score":          18.73,
        "survived_windows": 7,
        "avg_calmar":     3.799,
        "min_calmar":     1.055,
        "leverage":       3,
        "max_leverage":   5,
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.03,      # SL 3.0%
        "base_mdd":       0.03,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },
}
