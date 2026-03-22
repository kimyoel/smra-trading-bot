"""
strategies/registry.py — WFA OOS 백테스트 검증 전략 레지스트리 (v6.3)

[v6.3] BTCUSDT 15분봉 WFA 전략 전면 교체
  - 출처: BTCUSDT_15m_WFA_Report.docx (2026-03-22)
  - LONG 5개 + SHORT 5개 전면 교체 (기존 전략 대비 Score 대폭 향상)
  - 레버리지: 전 전략 20× 통일 (보고서 권장)
  - LONG: WILLR_BB_EMA_STACK(유지), SMA_PSAR_ADX_INV(신규), PSAR_ICHIMOKU_ATR_SIG(신규),
          EMA_MACD_PSAR(유지), EMA_PSAR_AD(신규)
  - SHORT: OBV_CCI_MOM(신규), OBV_CCI_ROC(신규), ADX_KELTNER_AD(신규),
           BB_EMA_STACK(유지), BB_EMA_STACK_ATR_INV(유지)
  - 제거: ADX_WILLR_EMA_STACK, AROON_DONCHIAN_VOL_INV, EMA_PSAR_MOM,
          WILLR_BB_OBV, SMA_ICHIMOKU_STDDEV, OBV_KELTNER_ADX_INV
  - 총 120개 전략: BTC 40 + ETH 40 + XRP 40

[v6.2] XRPUSDT 4시간봉 WFA 전략 10개 추가
  - 출처: XRPUSDT_4h_WFA_Report.docx (2026-03-21)
  - LONG 5개 + SHORT 5개 (XRP 4시간봉: surv≥5, avg_calmar≥1.5, min_calmar≥0.4)
  - 1,957개 전략 → 필터 후 → Score 상위 5개씩 선별
  - SHORT #3·#4·#5 동일 성과 (Score 26.24, avg 4.84, min 2.49)
  - 레버리지: min((1-0.5%)/SL%×0.8, 20x)
  - 총 120개 전략: BTC 40 + ETH 40 + XRP 40

[v6.1] XRPUSDT 1시간봉 WFA 전략 10개 추가
  - 출처: XRPUSDT_1h_WFA_Report.docx (2026-03-21)
  - LONG 5개 + SHORT 5개 (XRP 1시간봉: surv≥5, avg_calmar≥1.5, min_calmar≥0.4)
  - 3,234개 전략 → 필터 후 1,139개 → Score 상위 5개씩 선별
  - SHORT 1위 surv=9 (Score 32.16), SHORT 2위 surv=12 (XRP 전체 최고 생존율)
  - 레버리지: min((1-0.5%)/SL%×0.8, 20x)
  - 총 110개 전략: BTC 40 + ETH 40 + XRP 30

[v6.0] XRPUSDT 15분봉 WFA 전략 10개 추가
  - 출처: XRPUSDT_15m_WFA_Report.docx (2026-03-21)
  - LONG 5개 + SHORT 5개 (XRP 15분봉: surv≥5, avg_calmar≥1.5, min_calmar≥0.4)
  - 3,227개 전략 → 필터 후 460개 → Score 상위 5개씩 선별
  - LONG 1·2·3위 surv=9 (XRP 최고 생존율)
  - 레버리지: min((1-0.5%)/SL%×0.8, 20x), XS10 = 15x (SL 5%)
  - 총 100개 전략: BTC 40 + ETH 40 + XRP 20

[v5.9] XRPUSDT 5분봉 WFA 전략 10개 추가
  - 출처: XRPUSDT_5m_WFA_Report.docx (2026-03-21)
  - LONG 5개 + SHORT 5개 (XRP 5분봉: surv≥4 완화, avg≥1.2, min≥0.35)
  - 1,100개 전략 중 206개(IQR×3 제거) → Score 상위 5개씩 선별
  - 레버리지: min((1-0.5%)/SL%×0.8, 20x) — 전 전략 20x
  - 총 90개 전략: BTC 40 + ETH 40 + XRP 10

[v5.8] ETHUSDT 4시간봉 WFA 전략 10개 추가
  - 출처: ETHUSDT_4h_WFA_Report.docx (2026-03-21)
  - LONG 5개 + SHORT 5개 (ETH 4시간봉: surv≥5, avg≥1.5, min≥0.4)
  - 1,870개 전략 중 885개(IQR×3 제거) → Score 상위 5개씩 선별
  - SHORT 1·2위 surv=11 (전체 데이터셋 최고 생존율)
  - 레버리지: 이론 = min((1-0.5%)/SL%×0.8, 20x)
  - 총 80개 전략: BTC(5m×10+15m×10+1h×10+4h×10) + ETH(5m×10+15m×10+1h×10+4h×10)

[v5.7] ETHUSDT 1시간봉 WFA 전략 10개 추가
  - 출처: ETHUSDT_1h_WFA_Report.docx (2026-03-21)
  - LONG 5개 + SHORT 5개 (ETH 1시간봉: surv≥5, avg≥1.5, min≥0.4)
  - 3,231개 전략 중 1,216개(IQR×3 제거) → Score 상위 5개씩 선별
  - 레버리지: 이론 = 1/(SL%+0.5%), 권장 = 이론×80% (상한 20x, min_calmar≥1.0→×1.05)
  - 총 70개 전략: BTC(5m×10+15m×10+1h×10+4h×10) + ETH(5m×10+15m×10+1h×10)

[v5.6] ETHUSDT 15분봉 WFA 전략 10개 추가
  - 출처: ETHUSDT_15m_WFA_Report.docx (2026-03-21)
  - LONG 5개 + SHORT 5개 (ETH 15분봉 완화기준: surv≥5, avg≥1.5, min≥0.4)
  - 3,239개 전략 중 447개(IQR×3 제거) → Score 상위 5개씩 선별
  - 레버리지: 이론 = 1/(SL%+0.5%), 권장 = 이론×80% (상한 20x, min_calmar≥1.0→×1.05)
  - 총 60개 전략: BTC(5m×10+15m×10+1h×10+4h×10) + ETH(5m×10+15m×10)
  → v5.7에서 70개로 확장

[v5.5] ETHUSDT 5분봉 WFA 전략 10개 추가
[v5.3] BTCUSDT 1시간봉 WFA 전략 10개 추가
[v5.2] BTCUSDT 5분봉 WFA 전략 10개 추가
[v5.1] 레버리지 설정 — 15분봉 WFA 보고서 레버리지 섹션 반영
[v5.0] BTCUSDT_15m_WFA_Report.docx 기반 전면 교체

TP/SL 타입:
  tp_type: "fixed" (고정 %)
  tp_mult: TP 비율 (소수), sl_mult: SL 비율 (소수)

레버리지:
  15m: recommended = floor(0.80 / (SL% + 0.4%))
  5m:  보고서 권장값 직접 적용 (이론 최대의 30~50%, 노이즈 감안)
  1h:  이론 = 1/(SL%+0.5%), 권장 = 이론×80% (상한 20x, min_calmar≥1.5시 +2)
  4h:  이론 = 1/(SL%+0.5%), 권장 = 이론×80% (상한 20x)
"""

STRATEGY_REGISTRY = {

    # ═══════════════════════════════════════════════════════════
    # LONG 전략 — 상위 5개 (Score 순)
    # ═══════════════════════════════════════════════════════════

    # LONG #1 — Score 24.92 | 7윈도우 생존, 3중 컨펌 구조
    # 진입: WR(14)<-80 AND Close<BB_lower(20,2) AND EMA5>EMA26>EMA50
    # 해석: Williams %R 과매도 + BB 하단 이탈 + EMA 정배열 → 추세 추종형 평균 회귀
    "L1_WILLR_BB_EMA_STACK": {
        "id":             "L1_WILLR_BB_EMA_STACK",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_willr_bb_ema_stack",
        "score":          24.92,
        "survived_windows": 7,
        "avg_calmar":     3.649,
        "min_calmar":     1.223,
        "leverage":       20,       # 보고서 권장 20×
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.025,     # SL 2.5%
        "base_mdd":       0.025,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # LONG #2 — Score 24.14 | avg_calmar 4.80 최강
    # 진입: SMA10>SMA20 AND SAR↑(0.02,0.2)
    # 필터: ADX(14)≤25 (횡보/약추세 필터)
    "L2_SMA_PSAR_ADX_INV": {
        "id":             "L2_SMA_PSAR_ADX_INV",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_sma_psar_adx_inv",
        "score":          24.14,
        "survived_windows": 6,
        "avg_calmar":     4.801,
        "min_calmar":     0.468,
        "leverage":       20,       # 보고서 권장 20×
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.008,     # SL 0.8%
        "base_mdd":       0.008,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # LONG #3 — Score 23.54 | min_calmar 3.13 방어적
    # 진입: SAR↑(0.02,0.2) AND Tenkan>Kijun
    # 필터: ATR(14)>ATR_SMA (변동성 확대 조건)
    "L3_PSAR_ICHIMOKU_ATR_SIG": {
        "id":             "L3_PSAR_ICHIMOKU_ATR_SIG",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_psar_ichimoku_atr_sig",
        "score":          23.54,
        "survived_windows": 4,
        "avg_calmar":     3.524,
        "min_calmar":     3.127,
        "leverage":       20,       # 보고서 권장 20×
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.04,      # TP 4.0%
        "sl_mult":        0.008,     # SL 0.8%
        "base_mdd":       0.008,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # LONG #4 — Score 21.41 | 단기(Hold=12) 추세 추종
    # 진입: EMA12>EMA26 AND MACD>Signal(12,26,9) AND SAR↑(0.02,0.2)
    "L4_EMA_MACD_PSAR": {
        "id":             "L4_EMA_MACD_PSAR",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_ema_macd_psar",
        "score":          21.41,
        "survived_windows": 6,
        "avg_calmar":     4.042,
        "min_calmar":     0.675,
        "leverage":       20,       # 보고서 권장 20×
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.02,      # SL 2.0%
        "base_mdd":       0.02,
        "max_hold_bars":  12,        # 12봉 (3시간)
    },

    # LONG #5 — Score 20.75 | EMA+PSAR+A/D 자금흐름 확인
    # 진입: EMA12>EMA26 AND SAR↑(0.02,0.2) AND AD>AD_SMA(20)
    "L5_EMA_PSAR_AD": {
        "id":             "L5_EMA_PSAR_AD",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_ema_psar_ad",
        "score":          20.75,
        "survived_windows": 6,
        "avg_calmar":     2.556,
        "min_calmar":     0.707,
        "leverage":       20,       # 보고서 권장 20×
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.05,      # TP 5.0%
        "sl_mult":        0.01,      # SL 1.0%
        "base_mdd":       0.01,
        "max_hold_bars":  24,        # 24봉 (6시간)
    },

    # ═══════════════════════════════════════════════════════════
    # SHORT 전략 — 상위 5개 (Score 순)
    # ═══════════════════════════════════════════════════════════

    # SHORT #1 — Score 26.75 | 최고 스코어, 수익성 최강
    # 진입: OBV<OBV_SMA(20) AND CCI(20)>+100 AND MOM(10)<0
    "S1_OBV_CCI_MOM": {
        "id":             "S1_OBV_CCI_MOM",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_obv_cci_mom",
        "score":          26.75,
        "survived_windows": 5,
        "avg_calmar":     6.372,
        "min_calmar":     1.598,
        "leverage":       20,       # 보고서 권장 20×
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.03,      # TP 3.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # SHORT #2 — Score 26.75 | MOM과 동등, ROC 대체 사용
    # 진입: OBV<OBV_SMA(20) AND CCI(20)>+100 AND ROC(10)<0%
    "S2_OBV_CCI_ROC": {
        "id":             "S2_OBV_CCI_ROC",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_obv_cci_roc",
        "score":          26.75,
        "survived_windows": 5,
        "avg_calmar":     6.372,
        "min_calmar":     1.598,
        "leverage":       20,       # 보고서 권장 20×
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.03,      # TP 3.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # SHORT #3 — Score 25.18 | 생존창 6, 안정성 균형
    # 진입: Close>KC_hi(20,2) AND AD<AD_SMA(20)
    # 필터: ADX(14)>25 (강추세 필터)
    "S3_ADX_KELTNER_AD": {
        "id":             "S3_ADX_KELTNER_AD",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_adx_keltner_ad",
        "score":          25.18,
        "survived_windows": 6,
        "avg_calmar":     5.452,
        "min_calmar":     1.499,
        "leverage":       20,       # 보고서 권장 20×
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.04,      # TP 4.0%
        "sl_mult":        0.02,      # SL 2.0%
        "base_mdd":       0.02,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # SHORT #4 — Score 23.81 | 생존창 7 최고, 단순 구조
    # 진입: Close>BB_upper(20,2) AND EMA5<EMA26<EMA50
    "S4_BB_EMA_STACK": {
        "id":             "S4_BB_EMA_STACK",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_bb_ema_stack",
        "score":          23.81,
        "survived_windows": 7,
        "avg_calmar":     3.799,
        "min_calmar":     1.055,
        "leverage":       20,       # 보고서 권장 20×
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.03,      # SL 3.0%
        "base_mdd":       0.03,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # SHORT #5 — Score 23.81 | #4 + ATR 저변동 필터
    # 진입: Close>BB_upper(20,2) AND EMA5<EMA26<EMA50
    # 필터: ATR(14) ≤ ATR_SMA (변동성 평균 이하)
    "S5_BB_EMA_STACK_ATR_INV": {
        "id":             "S5_BB_EMA_STACK_ATR_INV",
        "symbol":         "BTC/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_bb_ema_stack_atr_inv",
        "score":          23.81,
        "survived_windows": 7,
        "avg_calmar":     3.799,
        "min_calmar":     1.055,
        "leverage":       20,       # 보고서 권장 20×
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.03,      # SL 3.0%
        "base_mdd":       0.03,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # ═══════════════════════════════════════════════════════════
    # 5분봉 LONG 전략 — 상위 5개 (BTCUSDT_5m_WFA_Report.docx)
    # ═══════════════════════════════════════════════════════════

    # 5m LONG #1 — Score 14.28 | 유일한 5분봉 황금기준 통과 (surv=5)
    # 진입: Close<BB_lo(20,2) AND EMA5>EMA26>EMA50 AND Vol≤SMA(20)*1.5
    "L6_5m_BB_EMA_STACK_VOL_INV": {
        "id":             "L6_5m_BB_EMA_STACK_VOL_INV",
        "symbol":         "BTC/USDT",
        "timeframe":      "5m",
        "direction":      "long",
        "entry_fn":       "entry_long_5m_bb_ema_stack_vol_inv",
        "score":          14.28,
        "survived_windows": 5,
        "avg_calmar":     2.627,
        "min_calmar":     0.998,
        "leverage":       15,       # 보고서 권장 15x (이론 40x, 80% 버퍼+노이즈)
        "max_leverage":   40,       # 이론: 1/(0.02+0.005)=40x
        "tp_type":        "fixed",
        "tp_mult":        0.03,      # TP 3.0%
        "sl_mult":        0.02,      # SL 2.0%
        "base_mdd":       0.02,
        "max_hold_bars":  48,        # 48봉 (4시간)
    },

    # 5m LONG #2 — Score 12.54 | 최고 avg_calmar 4.574
    # 진입: MACD>Sig(12,26,9) AND Tenkan>Kijun AND STD↑&Close>SMA(20)
    "L7_5m_MACD_ICHIMOKU_STDDEV": {
        "id":             "L7_5m_MACD_ICHIMOKU_STDDEV",
        "symbol":         "BTC/USDT",
        "timeframe":      "5m",
        "direction":      "long",
        "entry_fn":       "entry_long_5m_macd_ichimoku_stddev",
        "score":          12.54,
        "survived_windows": 4,
        "avg_calmar":     4.574,
        "min_calmar":     0.941,
        "leverage":       20,       # 보고서 권장 20x (이론 67x, 상한 20x)
        "max_leverage":   67,       # 이론: 1/(0.01+0.005)=66.7x
        "tp_type":        "fixed",
        "tp_mult":        0.015,     # TP 1.5%
        "sl_mult":        0.01,      # SL 1.0%
        "base_mdd":       0.01,
        "max_hold_bars":  48,        # 48봉 (4시간)
    },

    # 5m LONG #3 — Score 12.07 | 최고 min_calmar 1.019, 3배 RR
    # 진입: Stoch %K(14)<20 상향 AND CCI(20)<-100 AND EMA5>EMA26>EMA50
    "L8_5m_STOCH_CCI_EMA_STACK": {
        "id":             "L8_5m_STOCH_CCI_EMA_STACK",
        "symbol":         "BTC/USDT",
        "timeframe":      "5m",
        "direction":      "long",
        "entry_fn":       "entry_long_5m_stoch_cci_ema_stack",
        "score":          12.07,
        "survived_windows": 4,
        "avg_calmar":     1.739,
        "min_calmar":     1.019,
        "leverage":       10,       # 보고서 권장 10x (SL 0.5% 타이트, 노이즈 위험)
        "max_leverage":   100,      # 이론: 1/(0.005+0.005)=100x
        "tp_type":        "fixed",
        "tp_mult":        0.015,     # TP 1.5%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  48,        # 48봉 (4시간)
    },

    # 5m LONG #4 — Score 11.17 | 가격·볼륨·수요 3차원 확인
    # 진입: CCI(20)<-100 AND Close>VWAP(20) AND AD>AD_SMA(20)
    "L9_5m_CCI_VWAP_AD": {
        "id":             "L9_5m_CCI_VWAP_AD",
        "symbol":         "BTC/USDT",
        "timeframe":      "5m",
        "direction":      "long",
        "entry_fn":       "entry_long_5m_cci_vwap_ad",
        "score":          11.17,
        "survived_windows": 4,
        "avg_calmar":     3.120,
        "min_calmar":     0.585,
        "leverage":       15,       # 보고서 권장 15x (min_calmar 낮아 보수적)
        "max_leverage":   40,       # 이론: 1/(0.02+0.005)=40x
        "tp_type":        "fixed",
        "tp_mult":        0.04,      # TP 4.0%
        "sl_mult":        0.02,      # SL 2.0%
        "base_mdd":       0.02,
        "max_hold_bars":  48,        # 48봉 (4시간)
    },

    # 5m LONG #5 — Score 11.04 | 이중 과매도 + 추세 확인
    # 진입: RSI(14)<30 AND CCI(20)<-100 AND EMA5>EMA26>EMA50
    "L10_5m_RSI_CCI_EMA_STACK": {
        "id":             "L10_5m_RSI_CCI_EMA_STACK",
        "symbol":         "BTC/USDT",
        "timeframe":      "5m",
        "direction":      "long",
        "entry_fn":       "entry_long_5m_rsi_cci_ema_stack",
        "score":          11.04,
        "survived_windows": 4,
        "avg_calmar":     1.787,
        "min_calmar":     0.671,
        "leverage":       15,       # 보고서 권장 15x (안전마진 고려)
        "max_leverage":   50,       # 이론: 1/(0.015+0.005)=50x
        "tp_type":        "fixed",
        "tp_mult":        0.03,      # TP 3.0%
        "sl_mult":        0.015,     # SL 1.5%
        "base_mdd":       0.015,
        "max_hold_bars":  48,        # 48봉 (4시간)
    },

    # ═══════════════════════════════════════════════════════════
    # 5분봉 SHORT 전략 — 상위 5개 (BTCUSDT_5m_WFA_Report.docx)
    # ═══════════════════════════════════════════════════════════

    # 5m SHORT #1 — Score 13.26 | SHORT 종합 1위, 최고 min_calmar 1.375
    # 진입: RSI(14)>70 AND WR(14)>-20 AND EMA5<EMA26<EMA50
    "S6_5m_RSI_WILLR_EMA_STACK": {
        "id":             "S6_5m_RSI_WILLR_EMA_STACK",
        "symbol":         "BTC/USDT",
        "timeframe":      "5m",
        "direction":      "short",
        "entry_fn":       "entry_short_5m_rsi_willr_ema_stack",
        "score":          13.26,
        "survived_windows": 4,
        "avg_calmar":     2.115,
        "min_calmar":     1.375,
        "leverage":       20,       # 보고서 권장 20x (min_calmar 최고 안정성)
        "max_leverage":   50,       # 이론: 1/(0.015+0.005)=50x
        "tp_type":        "fixed",
        "tp_mult":        0.02,      # TP 2.0%
        "sl_mult":        0.015,     # SL 1.5%
        "base_mdd":       0.015,
        "max_hold_bars":  48,        # 48봉 (4시간)
    },

    # 5m SHORT #2 — Score 12.41 | 거래량 폭증 + 추세 2중 확인
    # 진입: EMA12<EMA26 AND Tenkan<Kijun AND Vol>SMA(20)*1.5
    "S7_5m_EMA_ICHIMOKU_VOLUME": {
        "id":             "S7_5m_EMA_ICHIMOKU_VOLUME",
        "symbol":         "BTC/USDT",
        "timeframe":      "5m",
        "direction":      "short",
        "entry_fn":       "entry_short_5m_ema_ichimoku_volume",
        "score":          12.41,
        "survived_windows": 4,
        "avg_calmar":     1.880,
        "min_calmar":     1.116,
        "leverage":       15,       # 보고서 권장 15x (이론 33x, 안전 마진)
        "max_leverage":   33,       # 이론: 1/(0.025+0.005)=33x
        "tp_type":        "fixed",
        "tp_mult":        0.04,      # TP 4.0%
        "sl_mult":        0.025,     # SL 2.5%
        "base_mdd":       0.025,
        "max_hold_bars":  48,        # 48봉 (4시간)
    },

    # 5m SHORT #3 — Score 12.05 | 단순 2지표 고수익 (avg 3.746)
    # 진입: RSI(14)>70 AND EMA5<EMA26<EMA50
    "S8_5m_RSI_EMA_STACK": {
        "id":             "S8_5m_RSI_EMA_STACK",
        "symbol":         "BTC/USDT",
        "timeframe":      "5m",
        "direction":      "short",
        "entry_fn":       "entry_short_5m_rsi_ema_stack",
        "score":          12.05,
        "survived_windows": 4,
        "avg_calmar":     3.746,
        "min_calmar":     0.831,
        "leverage":       15,       # 보고서 권장 15x (hold 24봉 단기)
        "max_leverage":   33,       # 이론: 1/(0.025+0.005)=33x
        "tp_type":        "fixed",
        "tp_mult":        0.05,      # TP 5.0%
        "sl_mult":        0.025,     # SL 2.5%
        "base_mdd":       0.025,
        "max_hold_bars":  24,        # 24봉 (2시간)
    },

    # 5m SHORT #4 — Score 12.05 | #3 ATR 필터 추가 버전
    # 진입: RSI(14)>70 AND EMA5<EMA26<EMA50 AND ATR(14)≤ATR_SMA
    "S9_5m_RSI_EMA_STACK_ATR_INV": {
        "id":             "S9_5m_RSI_EMA_STACK_ATR_INV",
        "symbol":         "BTC/USDT",
        "timeframe":      "5m",
        "direction":      "short",
        "entry_fn":       "entry_short_5m_rsi_ema_stack_atr_inv",
        "score":          12.05,
        "survived_windows": 4,
        "avg_calmar":     3.746,
        "min_calmar":     0.831,
        "leverage":       15,       # 보고서 권장 15x (#3과 동일)
        "max_leverage":   33,       # 이론: 1/(0.025+0.005)=33x
        "tp_type":        "fixed",
        "tp_mult":        0.05,      # TP 5.0%
        "sl_mult":        0.025,     # SL 2.5%
        "base_mdd":       0.025,
        "max_hold_bars":  24,        # 24봉 (2시간)
    },

    # 5m SHORT #5 — Score 11.50 | 변동성 확장 + 자금흐름 숏
    # 진입: SAR↓(0.02,0.2) AND MFI(14)>80 AND STD↑&Close<SMA(20)
    "S10_5m_PSAR_MFI_STDDEV": {
        "id":             "S10_5m_PSAR_MFI_STDDEV",
        "symbol":         "BTC/USDT",
        "timeframe":      "5m",
        "direction":      "short",
        "entry_fn":       "entry_short_5m_psar_mfi_stddev",
        "score":          11.50,
        "survived_windows": 4,
        "avg_calmar":     2.650,
        "min_calmar":     0.735,
        "leverage":       15,       # 보고서 권장 15x (hold 24봉 단기)
        "max_leverage":   50,       # 이론: 1/(0.015+0.005)=50x
        "tp_type":        "fixed",
        "tp_mult":        0.03,      # TP 3.0%
        "sl_mult":        0.015,     # SL 1.5%
        "base_mdd":       0.015,
        "max_hold_bars":  24,        # 24봉 (2시간)
    },

    # ═══════════════════════════════════════════════════════════
    # 1시간봉 LONG 전략 — 상위 5개 (BTCUSDT_1h_WFA_Report.docx)
    # 황금기준: surv≥6, avg_calmar≥2, min_calmar≥0.5
    # 레버리지: 이론 = 1/(SL%+MMR0.5%), 권장 = 이론×80% (상한20x, min_calmar≥1.5→+2)
    # ═══════════════════════════════════════════════════════════

    # 1h LONG #1 — Score 22.99 | 전체 1위 LONG, 7윈도우 생존
    # 진입: SMA10>SMA20 AND STD↑&Close>SMA(20) AND EMA5>EMA26>EMA50
    # 해석: SMA 추세 + 변동성 팽창 + EMA 정배열 3중 확인
    "L11_1h_SMA_STDDEV_EMA_STACK": {
        "id":             "L11_1h_SMA_STDDEV_EMA_STACK",
        "symbol":         "BTC/USDT",
        "timeframe":      "1h",
        "direction":      "long",
        "entry_fn":       "entry_long_1h_sma_stddev_ema_stack",
        "score":          22.99,
        "survived_windows": 7,
        "avg_calmar":     5.2555,
        "min_calmar":     2.3858,
        "leverage":       20,       # 이론: 1/(0.01+0.005)=66.7x, 권장: 53x→상한20x+2(min≥1.5)→20x
        "max_leverage":   66,       # 이론: floor(1/(0.01+0.005))=66
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.01,      # SL 1.0%
        "base_mdd":       0.01,
        "max_hold_bars":  24,        # 24봉 (1일)
    },

    # 1h LONG #2 — Score 22.40 | 8윈도우 생존, 횡보장 추세 추종
    # 진입: EMA12>EMA26 AND STD↑&Close>SMA(20)
    # 필터: ADX(14)≤25 (횡보장에서만)
    "L12_1h_EMA_STDDEV_ADX_INV": {
        "id":             "L12_1h_EMA_STDDEV_ADX_INV",
        "symbol":         "BTC/USDT",
        "timeframe":      "1h",
        "direction":      "long",
        "entry_fn":       "entry_long_1h_ema_stddev_adx_inv",
        "score":          22.40,
        "survived_windows": 8,
        "avg_calmar":     3.7613,
        "min_calmar":     1.6143,
        "leverage":       14,       # 이론: 1/(0.06+0.005)=15.4x, 권장: 12+2(min≥1.5)=14x
        "max_leverage":   15,       # 이론: floor(1/(0.06+0.005))=15
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.06,      # SL 6.0%
        "base_mdd":       0.06,
        "max_hold_bars":  48,        # 48봉 (2일)
    },

    # 1h LONG #3 — Score 22.25 | 8윈도우 생존, 모멘텀 확인
    # 진입: SAR↑(0.02,0.2) AND AroonUp(25)>70 AND MOM(10)>0
    "L13_1h_PSAR_AROON_MOM": {
        "id":             "L13_1h_PSAR_AROON_MOM",
        "symbol":         "BTC/USDT",
        "timeframe":      "1h",
        "direction":      "long",
        "entry_fn":       "entry_long_1h_psar_aroon_mom",
        "score":          22.25,
        "survived_windows": 8,
        "avg_calmar":     3.1990,
        "min_calmar":     1.6041,
        "leverage":       20,       # 이론: 1/(0.03+0.005)=28.6x, 권장: 22+2→상한20x
        "max_leverage":   28,       # 이론: floor(1/(0.03+0.005))=28
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.03,      # SL 3.0%
        "base_mdd":       0.03,
        "max_hold_bars":  48,        # 48봉 (2일)
    },

    # 1h LONG #4 — Score 22.25 | #3과 동점, VWAP 확인
    # 진입: SAR↑(0.02,0.2) AND AroonUp(25)>70 AND Close>VWAP(20)
    "L14_1h_PSAR_AROON_VWAP": {
        "id":             "L14_1h_PSAR_AROON_VWAP",
        "symbol":         "BTC/USDT",
        "timeframe":      "1h",
        "direction":      "long",
        "entry_fn":       "entry_long_1h_psar_aroon_vwap",
        "score":          22.25,
        "survived_windows": 8,
        "avg_calmar":     3.1990,
        "min_calmar":     1.6041,
        "leverage":       20,       # 이론: 28.6x, 권장: 22+2→상한20x
        "max_leverage":   28,       # 이론: floor(1/(0.03+0.005))=28
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.03,      # SL 3.0%
        "base_mdd":       0.03,
        "max_hold_bars":  48,        # 48봉 (2일)
    },

    # 1h LONG #5 — Score 22.25 | #3/#4와 동점, ROC 확인
    # 진입: SAR↑(0.02,0.2) AND AroonUp(25)>70 AND ROC(10)>0%
    "L15_1h_PSAR_AROON_ROC": {
        "id":             "L15_1h_PSAR_AROON_ROC",
        "symbol":         "BTC/USDT",
        "timeframe":      "1h",
        "direction":      "long",
        "entry_fn":       "entry_long_1h_psar_aroon_roc",
        "score":          22.25,
        "survived_windows": 8,
        "avg_calmar":     3.1990,
        "min_calmar":     1.6041,
        "leverage":       20,       # 이론: 28.6x, 권장: 22+2→상한20x
        "max_leverage":   28,       # 이론: floor(1/(0.03+0.005))=28
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.03,      # SL 3.0%
        "base_mdd":       0.03,
        "max_hold_bars":  48,        # 48봉 (2일)
    },

    # ═══════════════════════════════════════════════════════════
    # 1시간봉 SHORT 전략 — 상위 5개 (BTCUSDT_1h_WFA_Report.docx)
    # ═══════════════════════════════════════════════════════════

    # 1h SHORT #1 — Score 23.27 | 전체 최고 스코어, 9윈도우 생존
    # 진입: RSI(14)>70 AND WR(14)>-20
    # 필터: ADX(14)>25 (강추세에서만)
    "S11_1h_ADX_RSI_WILLR": {
        "id":             "S11_1h_ADX_RSI_WILLR",
        "symbol":         "BTC/USDT",
        "timeframe":      "1h",
        "direction":      "short",
        "entry_fn":       "entry_short_1h_adx_rsi_willr",
        "score":          23.27,
        "survived_windows": 9,
        "avg_calmar":     16.0208,
        "min_calmar":     0.8108,
        "leverage":       17,       # 이론: 1/(0.04+0.005)=22.2x, 권장: 17x (min<1.5→완화 없음)
        "max_leverage":   22,       # 이론: floor(1/(0.04+0.005))=22
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.04,      # SL 4.0%
        "base_mdd":       0.04,
        "max_hold_bars":  48,        # 48봉 (2일)
    },

    # 1h SHORT #2 — Score 22.44 | avg_calmar 22.77 (극고 수익)
    # 진입: RSI(14)>70
    # 필터: ADX(14)>25 AND Vol≤SMA(20)*1.5
    "S12_1h_ADX_RSI_VOL_INV": {
        "id":             "S12_1h_ADX_RSI_VOL_INV",
        "symbol":         "BTC/USDT",
        "timeframe":      "1h",
        "direction":      "short",
        "entry_fn":       "entry_short_1h_adx_rsi_vol_inv",
        "score":          22.44,
        "survived_windows": 8,
        "avg_calmar":     22.7672,
        "min_calmar":     1.0915,
        "leverage":       17,       # 이론: 22.2x, 권장: 17x (min<1.5)
        "max_leverage":   22,       # 이론: floor(1/(0.04+0.005))=22
        "tp_type":        "fixed",
        "tp_mult":        0.05,      # TP 5.0%
        "sl_mult":        0.04,      # SL 4.0%
        "base_mdd":       0.04,
        "max_hold_bars":  48,        # 48봉 (2일)
    },

    # 1h SHORT #3 — Score 22.18 | 최고 안정성 (min_calmar 2.70)
    # 진입: MACD<Sig(12,26,9) AND STD↑&Close<SMA(20)
    # 필터: Vol≤SMA(20)*1.5
    "S13_1h_MACD_STDDEV_VOL_INV": {
        "id":             "S13_1h_MACD_STDDEV_VOL_INV",
        "symbol":         "BTC/USDT",
        "timeframe":      "1h",
        "direction":      "short",
        "entry_fn":       "entry_short_1h_macd_stddev_vol_inv",
        "score":          22.18,
        "survived_windows": 6,
        "avg_calmar":     6.8640,
        "min_calmar":     2.7046,
        "leverage":       20,       # 이론: 1/(0.025+0.005)=33.3x, 권장: 26+2→상한20x
        "max_leverage":   33,       # 이론: floor(1/(0.025+0.005))=33
        "tp_type":        "fixed",
        "tp_mult":        0.05,      # TP 5.0%
        "sl_mult":        0.025,     # SL 2.5%
        "base_mdd":       0.025,
        "max_hold_bars":  48,        # 48봉 (2일)
    },

    # 1h SHORT #4 — Score 22.11 | 최고 min_calmar 2.82, 고RR
    # 진입: Close>BB_hi(20,2) AND MFI(14)>80
    # 필터: ADX(14)≤25 (횡보장)
    "S14_1h_BB_MFI_ADX_INV": {
        "id":             "S14_1h_BB_MFI_ADX_INV",
        "symbol":         "BTC/USDT",
        "timeframe":      "1h",
        "direction":      "short",
        "entry_fn":       "entry_short_1h_bb_mfi_adx_inv",
        "score":          22.11,
        "survived_windows": 6,
        "avg_calmar":     4.1547,
        "min_calmar":     2.8221,
        "leverage":       20,       # 이론: 1/(0.01+0.005)=66.7x, 권장: 53+2→상한20x
        "max_leverage":   66,       # 이론: floor(1/(0.01+0.005))=66
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.01,      # SL 1.0%
        "base_mdd":       0.01,
        "max_hold_bars":  48,        # 48봉 (2일)
    },

    # 1h SHORT #5 — Score 20.80 | EMA 역배열 + CCI 과매수
    # 진입: CCI(20)>+100 AND EMA5<EMA26<EMA50
    "S15_1h_CCI_EMA_STACK": {
        "id":             "S15_1h_CCI_EMA_STACK",
        "symbol":         "BTC/USDT",
        "timeframe":      "1h",
        "direction":      "short",
        "entry_fn":       "entry_short_1h_cci_ema_stack",
        "score":          20.80,
        "survived_windows": 7,
        "avg_calmar":     8.6982,
        "min_calmar":     1.5108,
        "leverage":       20,       # 이론: 1/(0.015+0.005)=50x, 권장: 40+2→상한20x
        "max_leverage":   50,       # 이론: floor(1/(0.015+0.005))=50
        "tp_type":        "fixed",
        "tp_mult":        0.02,      # TP 2.0%
        "sl_mult":        0.015,     # SL 1.5%
        "base_mdd":       0.015,
        "max_hold_bars":  48,        # 48봉 (2일)
    },

    # ═══════════════════════════════════════════════════════════
    # 4시간봉 LONG 전략 — 상위 5개 (BTCUSDT_4h_WFA_Report.docx)
    # 황금기준: surv≥6, avg_calmar≥2, min_calmar≥0.5
    # 4h 특성: 1,894개 중 443개(23.4%) 통과 — 전 TF 최고 강건성
    # 레버리지: 이론 = 1/(SL%+MMR0.5%), 권장 = 이론×80% (상한20x)
    # ═══════════════════════════════════════════════════════════

    # 4h LONG #1 — Score 23.02 | 거래량+VWAP+변동성 3중 확인
    # 진입: Close>VWAP(20) AND STD↑&Close>SMA(20) AND Vol>SMA(20)*1.5
    "L16_4h_VOLUME_VWAP_STDDEV": {
        "id":             "L16_4h_VOLUME_VWAP_STDDEV",
        "symbol":         "BTC/USDT",
        "timeframe":      "4h",
        "direction":      "long",
        "entry_fn":       "entry_long_4h_volume_vwap_stddev",
        "score":          23.02,
        "survived_windows": 7,
        "avg_calmar":     5.303,
        "min_calmar":     2.393,
        "leverage":       20,       # 이론: 1/(0.01+0.005)=66.7x, 권장: →상한20x
        "max_leverage":   66,       # 이론: floor(1/(0.01+0.005))=66
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.01,      # SL 1.0%
        "base_mdd":       0.01,
        "max_hold_bars":  48,        # 48봉 (8일)
    },

    # 4h LONG #2 — Score 23.01 | 10윈도우 생존 (최다), 횡보장 돌파
    # 진입: AroonUp(25)>70 AND Vol>SMA(20)*1.5
    # 필터: ADX(14)≤25
    "L17_4h_AROON_VOLUME_ADX_INV": {
        "id":             "L17_4h_AROON_VOLUME_ADX_INV",
        "symbol":         "BTC/USDT",
        "timeframe":      "4h",
        "direction":      "long",
        "entry_fn":       "entry_long_4h_aroon_volume_adx_inv",
        "score":          23.01,
        "survived_windows": 10,
        "avg_calmar":     3.455,
        "min_calmar":     0.506,
        "leverage":       17,       # 이론: 1/(0.04+0.005)=22.2x, 권장: 17x
        "max_leverage":   22,       # 이론: floor(1/(0.04+0.005))=22
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.04,      # SL 4.0%
        "base_mdd":       0.04,
        "max_hold_bars":  12,        # 12봉 (2일)
    },

    # 4h LONG #3 — Score 22.48 | 최고 안정성 min_calmar 2.938
    # 진입: Close>VWAP(20) AND ATR>ATR_SMA(20) AND Vol>SMA(20)*1.5
    "L18_4h_ATR_SIG_VOLUME_VWAP": {
        "id":             "L18_4h_ATR_SIG_VOLUME_VWAP",
        "symbol":         "BTC/USDT",
        "timeframe":      "4h",
        "direction":      "long",
        "entry_fn":       "entry_long_4h_atr_sig_volume_vwap",
        "score":          22.48,
        "survived_windows": 6,
        "avg_calmar":     4.291,
        "min_calmar":     2.938,
        "leverage":       20,       # 이론: 1/(0.03+0.005)=28.6x, 권장: →상한20x
        "max_leverage":   28,       # 이론: floor(1/(0.03+0.005))=28
        "tp_type":        "fixed",
        "tp_mult":        0.05,      # TP 5.0%
        "sl_mult":        0.03,      # SL 3.0%
        "base_mdd":       0.03,
        "max_hold_bars":  24,        # 24봉 (4일)
    },

    # 4h LONG #4 — Score 21.90 | 9윈도우, EMA 정배열+거래량+ATR 저변동
    # 진입: EMA5>EMA26>EMA50 AND Vol>SMA(20)*1.5
    # 필터: ATR(14)≤ATR_SMA(20)
    "L19_4h_VOLUME_EMA_STACK_ATR_INV": {
        "id":             "L19_4h_VOLUME_EMA_STACK_ATR_INV",
        "symbol":         "BTC/USDT",
        "timeframe":      "4h",
        "direction":      "long",
        "entry_fn":       "entry_long_4h_volume_ema_stack_atr_inv",
        "score":          21.90,
        "survived_windows": 9,
        "avg_calmar":     2.439,
        "min_calmar":     0.887,
        "leverage":       20,       # 이론: 1/(0.015+0.005)=50x, 권장: →상한20x
        "max_leverage":   50,       # 이론: floor(1/(0.015+0.005))=50
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.015,     # SL 1.5%
        "base_mdd":       0.015,
        "max_hold_bars":  12,        # 12봉 (2일)
    },

    # 4h LONG #5 — Score 21.90 | #4 ATR 필터 없는 버전, 동일 성능
    # 진입: EMA5>EMA26>EMA50 AND Vol>SMA(20)*1.5
    "L20_4h_VOLUME_EMA_STACK": {
        "id":             "L20_4h_VOLUME_EMA_STACK",
        "symbol":         "BTC/USDT",
        "timeframe":      "4h",
        "direction":      "long",
        "entry_fn":       "entry_long_4h_volume_ema_stack",
        "score":          21.90,
        "survived_windows": 9,
        "avg_calmar":     2.439,
        "min_calmar":     0.887,
        "leverage":       20,       # 이론: 50x, 권장: →상한20x
        "max_leverage":   50,       # 이론: floor(1/(0.015+0.005))=50
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.015,     # SL 1.5%
        "base_mdd":       0.015,
        "max_hold_bars":  12,        # 12봉 (2일)
    },

    # ═══════════════════════════════════════════════════════════
    # 4시간봉 SHORT 전략 — 상위 5개 (BTCUSDT_4h_WFA_Report.docx)
    # ═══════════════════════════════════════════════════════════

    # 4h SHORT #1 — Score 29.53 | 전체 최고 스코어, min_calmar 5.005
    # 진입: WR(14)>-20 AND ATR>ATR_SMA(20) AND MFI(14)>80
    "S16_4h_WILLR_ATR_SIG_MFI": {
        "id":             "S16_4h_WILLR_ATR_SIG_MFI",
        "symbol":         "BTC/USDT",
        "timeframe":      "4h",
        "direction":      "short",
        "entry_fn":       "entry_short_4h_willr_atr_sig_mfi",
        "score":          29.53,
        "survived_windows": 6,
        "avg_calmar":     11.338,
        "min_calmar":     5.005,
        "leverage":       20,       # 이론: 1/(0.005+0.005)=100x, 권장: →상한20x
        "max_leverage":   100,      # 이론: floor(1/(0.005+0.005))=100
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  48,        # 48봉 (8일)
    },

    # 4h SHORT #2 — Score 24.03 | 9윈도우, WR+BB+CCI 3중 과매수
    # 진입: WR(14)>-20 AND Close>BB_hi(20,2) AND CCI(20)>+100
    "S17_4h_WILLR_BB_CCI": {
        "id":             "S17_4h_WILLR_BB_CCI",
        "symbol":         "BTC/USDT",
        "timeframe":      "4h",
        "direction":      "short",
        "entry_fn":       "entry_short_4h_willr_bb_cci",
        "score":          24.03,
        "survived_windows": 9,
        "avg_calmar":     23.314,
        "min_calmar":     0.947,
        "leverage":       14,       # 이론: 1/(0.05+0.005)=18.2x, 권장: 14x
        "max_leverage":   18,       # 이론: floor(1/(0.05+0.005))=18
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.05,      # SL 5.0%
        "base_mdd":       0.05,
        "max_hold_bars":  24,        # 24봉 (4일)
    },

    # 4h SHORT #3 — Score 22.54 | 9윈도우, 단순 WR+BB 2지표
    # 진입: WR(14)>-20 AND Close>BB_hi(20,2)
    "S18_4h_WILLR_BB": {
        "id":             "S18_4h_WILLR_BB",
        "symbol":         "BTC/USDT",
        "timeframe":      "4h",
        "direction":      "short",
        "entry_fn":       "entry_short_4h_willr_bb",
        "score":          22.54,
        "survived_windows": 9,
        "avg_calmar":     3.154,
        "min_calmar":     1.040,
        "leverage":       20,       # 이론: 1/(0.025+0.005)=33.3x, 권장: →상한20x
        "max_leverage":   33,       # 이론: floor(1/(0.025+0.005))=33
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.025,     # SL 2.5%
        "base_mdd":       0.025,
        "max_hold_bars":  24,        # 24봉 (4일)
    },

    # 4h SHORT #4 — Score 22.54 | #3 ATR 필터 추가 (저변동 진입)
    # 진입: WR(14)>-20 AND Close>BB_hi(20,2)
    # 필터: ATR(14)≤ATR_SMA(20)
    "S19_4h_WILLR_BB_ATR_INV": {
        "id":             "S19_4h_WILLR_BB_ATR_INV",
        "symbol":         "BTC/USDT",
        "timeframe":      "4h",
        "direction":      "short",
        "entry_fn":       "entry_short_4h_willr_bb_atr_inv",
        "score":          22.54,
        "survived_windows": 9,
        "avg_calmar":     3.154,
        "min_calmar":     1.040,
        "leverage":       20,       # 이론: 33.3x, 권장: →상한20x
        "max_leverage":   33,       # 이론: floor(1/(0.025+0.005))=33
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.025,     # SL 2.5%
        "base_mdd":       0.025,
        "max_hold_bars":  24,        # 24봉 (4일)
    },

    # 4h SHORT #5 — Score 22.34 | 최고 min_calmar 2.803, CMF 자금흐름
    # 진입: ADX(14)>25 AND CMF(20)<-0.1 AND Vol≤SMA(20)*1.5
    "S20_4h_ADX_CMF_VOL_INV": {
        "id":             "S20_4h_ADX_CMF_VOL_INV",
        "symbol":         "BTC/USDT",
        "timeframe":      "4h",
        "direction":      "short",
        "entry_fn":       "entry_short_4h_adx_cmf_vol_inv",
        "score":          22.34,
        "survived_windows": 6,
        "avg_calmar":     5.924,
        "min_calmar":     2.803,
        "leverage":       16,       # 이론: 1/(0.05+0.005)=18.2x, 권장: 14+2(min≥1.5)=16x
        "max_leverage":   18,       # 이론: floor(1/(0.05+0.005))=18
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.05,      # SL 5.0%
        "base_mdd":       0.05,
        "max_hold_bars":  24,        # 24봉 (4일)
    },

    # ═══════════════════════════════════════════════════════════
    # ETHUSDT 5분봉 LONG 전략 — 상위 5개 (ETHUSDT_5m_WFA_Report.docx)
    # 742개 전략, 완화기준(surv≥4, avg≥1.5, min≥0.4) 102개(13.7%)
    # 레버리지: 이론=1/(SL%+0.5%), 권장=이론×80% (상한20x, SL<1% 슬리피지 감안)
    # ═══════════════════════════════════════════════════════════

    # ETH 5m LONG #1 — Score 22.84 | 전체 1위 LONG, min_calmar 3.515
    # 진입: WR(14)<-80 AND Tenkan>Kijun AND AroonUp(25)>70
    "EL1_eth5m_WILLR_ICHIMOKU_AROON": {
        "id":             "EL1_eth5m_WILLR_ICHIMOKU_AROON",
        "symbol":         "ETH/USDT",
        "timeframe":      "5m",
        "direction":      "long",
        "entry_fn":       "entry_long_eth5m_willr_ichimoku_aroon",
        "score":          22.84,
        "survived_windows": 5,
        "avg_calmar":     8.9222,
        "min_calmar":     3.5150,
        "leverage":       20,       # 이론: 1/(0.015+0.005)=50x, 권장: →상한20x
        "max_leverage":   50,       # 이론: floor(1/(0.015+0.005))=50
        "tp_type":        "fixed",
        "tp_mult":        0.04,      # TP 4.0%
        "sl_mult":        0.015,     # SL 1.5%
        "base_mdd":       0.015,
        "max_hold_bars":  24,        # 24봉 (2시간)
    },

    # ETH 5m LONG #2 — Score 19.17 | min_calmar 3.153 (최고 안정성)
    # 진입: Stoch %K(14)<20 상향전환 AND EMA5>EMA26>EMA50
    # 필터: ADX(14)>25
    "EL2_eth5m_ADX_STOCH_EMA_STACK": {
        "id":             "EL2_eth5m_ADX_STOCH_EMA_STACK",
        "symbol":         "ETH/USDT",
        "timeframe":      "5m",
        "direction":      "long",
        "entry_fn":       "entry_long_eth5m_adx_stoch_ema_stack",
        "score":          19.17,
        "survived_windows": 4,
        "avg_calmar":     4.5390,
        "min_calmar":     3.1525,
        "leverage":       20,       # 이론: 1/(0.03+0.005)=28.6x, 권장: →상한20x
        "max_leverage":   28,       # 이론: floor(1/(0.03+0.005))=28
        "tp_type":        "fixed",
        "tp_mult":        0.04,      # TP 4.0%
        "sl_mult":        0.03,      # SL 3.0%
        "base_mdd":       0.03,
        "max_hold_bars":  48,        # 48봉 (4시간)
    },

    # ETH 5m LONG #3 — Score 17.60 | 6윈도우 최다 생존
    # 진입: SMA10>SMA20 AND SAR↑(0.02,0.2)
    # 필터: ADX(14)>25
    "EL3_eth5m_SMA_ADX_PSAR": {
        "id":             "EL3_eth5m_SMA_ADX_PSAR",
        "symbol":         "ETH/USDT",
        "timeframe":      "5m",
        "direction":      "long",
        "entry_fn":       "entry_long_eth5m_sma_adx_psar",
        "score":          17.60,
        "survived_windows": 6,
        "avg_calmar":     3.9353,
        "min_calmar":     1.3361,
        "leverage":       20,       # 이론: 1/(0.025+0.005)=33.3x, 권장: →상한20x
        "max_leverage":   33,       # 이론: floor(1/(0.025+0.005))=33
        "tp_type":        "fixed",
        "tp_mult":        0.05,      # TP 5.0%
        "sl_mult":        0.025,     # SL 2.5%
        "base_mdd":       0.025,
        "max_hold_bars":  48,        # 48봉 (4시간)
    },

    # ETH 5m LONG #4 — Score 17.24 | avg_calmar 19.91 (극고 수익)
    # 진입: Close<BB_lo(20,2) AND EMA5>EMA26>EMA50
    # 필터: ATR(14)>ATR_SMA(20)
    "EL4_eth5m_BB_ATR_SIG_EMA_STACK": {
        "id":             "EL4_eth5m_BB_ATR_SIG_EMA_STACK",
        "symbol":         "ETH/USDT",
        "timeframe":      "5m",
        "direction":      "long",
        "entry_fn":       "entry_long_eth5m_bb_atr_sig_ema_stack",
        "score":          17.24,
        "survived_windows": 5,
        "avg_calmar":     19.9093,
        "min_calmar":     1.3998,
        "leverage":       20,       # 이론: 33.3x, 권장: →상한20x
        "max_leverage":   33,       # 이론: floor(1/(0.025+0.005))=33
        "tp_type":        "fixed",
        "tp_mult":        0.05,      # TP 5.0%
        "sl_mult":        0.025,     # SL 2.5%
        "base_mdd":       0.025,
        "max_hold_bars":  48,        # 48봉 (4시간)
    },

    # ETH 5m LONG #5 — Score 16.62 | 단순 2지표, 고RR
    # 진입: RSI(14)<30 AND EMA5>EMA26>EMA50
    "EL5_eth5m_RSI_EMA_STACK": {
        "id":             "EL5_eth5m_RSI_EMA_STACK",
        "symbol":         "ETH/USDT",
        "timeframe":      "5m",
        "direction":      "long",
        "entry_fn":       "entry_long_eth5m_rsi_ema_stack",
        "score":          16.62,
        "survived_windows": 4,
        "avg_calmar":     3.6307,
        "min_calmar":     2.3631,
        "leverage":       20,       # 이론: 1/(0.01+0.005)=66.7x, 권장: →상한20x
        "max_leverage":   66,       # 이론: floor(1/(0.01+0.005))=66
        "tp_type":        "fixed",
        "tp_mult":        0.02,      # TP 2.0%
        "sl_mult":        0.01,      # SL 1.0%
        "base_mdd":       0.01,
        "max_hold_bars":  48,        # 48봉 (4시간)
    },

    # ═══════════════════════════════════════════════════════════
    # ETHUSDT 5분봉 SHORT 전략 — 상위 5개 (ETHUSDT_5m_WFA_Report.docx)
    # ═══════════════════════════════════════════════════════════

    # ETH 5m SHORT #1 — Score 19.89 | SHORT 종합 1위
    # 진입: Stoch %K(14)>80 하향전환 AND OBV<OBV_SMA(20) AND MFI(14)>80
    "ES1_eth5m_STOCH_OBV_MFI": {
        "id":             "ES1_eth5m_STOCH_OBV_MFI",
        "symbol":         "ETH/USDT",
        "timeframe":      "5m",
        "direction":      "short",
        "entry_fn":       "entry_short_eth5m_stoch_obv_mfi",
        "score":          19.89,
        "survived_windows": 5,
        "avg_calmar":     8.1146,
        "min_calmar":     2.5611,
        "leverage":       20,       # 이론: 1/(0.02+0.005)=40x, 권장: →상한20x
        "max_leverage":   40,       # 이론: floor(1/(0.02+0.005))=40
        "tp_type":        "fixed",
        "tp_mult":        0.05,      # TP 5.0%
        "sl_mult":        0.02,      # SL 2.0%
        "base_mdd":       0.02,
        "max_hold_bars":  48,        # 48봉 (4시간)
    },

    # ETH 5m SHORT #2 — Score 17.23 | 타이트 SL 0.5%
    # 진입: SMA10<SMA20 AND MACD<Sig(12,26,9) AND STD↑&Close<SMA(20)
    "ES2_eth5m_SMA_MACD_STDDEV": {
        "id":             "ES2_eth5m_SMA_MACD_STDDEV",
        "symbol":         "ETH/USDT",
        "timeframe":      "5m",
        "direction":      "short",
        "entry_fn":       "entry_short_eth5m_sma_macd_stddev",
        "score":          17.23,
        "survived_windows": 5,
        "avg_calmar":     3.0151,
        "min_calmar":     1.9473,
        "leverage":       10,       # 이론: 1/(0.005+0.005)=100x, 권장: 10x (SL<1% 슬리피지 감안)
        "max_leverage":   100,      # 이론: floor(1/(0.005+0.005))=100
        "tp_type":        "fixed",
        "tp_mult":        0.05,      # TP 5.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  48,        # 48봉 (4시간)
    },

    # ETH 5m SHORT #3 — Score 16.34 | ADX 추세 강도 필터
    # 진입: RSI(14)>70 AND EMA5<EMA26<EMA50
    # 필터: ADX(14)>25
    "ES3_eth5m_ADX_RSI_EMA_STACK": {
        "id":             "ES3_eth5m_ADX_RSI_EMA_STACK",
        "symbol":         "ETH/USDT",
        "timeframe":      "5m",
        "direction":      "short",
        "entry_fn":       "entry_short_eth5m_adx_rsi_ema_stack",
        "score":          16.34,
        "survived_windows": 5,
        "avg_calmar":     6.9775,
        "min_calmar":     1.4210,
        "leverage":       12,       # 이론: 1/(0.008+0.005)=76.9x, 권장: 12x (SL<1% 슬리피지 감안)
        "max_leverage":   76,       # 이론: floor(1/(0.008+0.005))=76
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.008,     # SL 0.8%
        "base_mdd":       0.008,
        "max_hold_bars":  48,        # 48봉 (4시간)
    },

    # ETH 5m SHORT #4 — Score 16.16 | 6윈도우 최다 생존
    # 진입: AroonDown(25)>70 AND CCI(20)>+100 AND EMA5<EMA26<EMA50
    "ES4_eth5m_AROON_CCI_EMA_STACK": {
        "id":             "ES4_eth5m_AROON_CCI_EMA_STACK",
        "symbol":         "ETH/USDT",
        "timeframe":      "5m",
        "direction":      "short",
        "entry_fn":       "entry_short_eth5m_aroon_cci_ema_stack",
        "score":          16.16,
        "survived_windows": 6,
        "avg_calmar":     2.5762,
        "min_calmar":     0.9614,
        "leverage":       14,       # 이론: 1/(0.05+0.005)=18.2x, 권장: 14x
        "max_leverage":   18,       # 이론: floor(1/(0.05+0.005))=18
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.05,      # SL 5.0%
        "base_mdd":       0.05,
        "max_hold_bars":  24,        # 24봉 (2시간)
    },

    # ETH 5m SHORT #5 — Score 15.38 | 6윈도우, 이치모쿠+PSAR
    # 진입: SAR↓(0.02,0.2) AND Tenkan<Kijun
    # 필터: ADX(14)>25
    "ES5_eth5m_ADX_PSAR_ICHIMOKU": {
        "id":             "ES5_eth5m_ADX_PSAR_ICHIMOKU",
        "symbol":         "ETH/USDT",
        "timeframe":      "5m",
        "direction":      "short",
        "entry_fn":       "entry_short_eth5m_adx_psar_ichimoku",
        "score":          15.38,
        "survived_windows": 6,
        "avg_calmar":     2.6877,
        "min_calmar":     0.6929,
        "leverage":       20,       # 이론: 1/(0.02+0.005)=40x, 권장: →상한20x
        "max_leverage":   40,       # 이론: floor(1/(0.02+0.005))=40
        "tp_type":        "fixed",
        "tp_mult":        0.04,      # TP 4.0%
        "sl_mult":        0.02,      # SL 2.0%
        "base_mdd":       0.02,
        "max_hold_bars":  48,        # 48봉 (4시간)
    },

    # ═══════════════════════════════════════════════════════════
    # ETHUSDT 15분봉 LONG 전략 — 상위 5개 (ETHUSDT_15m_WFA_Report.docx)
    # 3,239개 전략, IQR×3 제거 후 447개 → Score 상위 5개 선별
    # 레버리지: 이론=1/(SL%+0.5%), 권장=이론×80% (상한20x, min_calmar≥1.0→×1.05)
    # ═══════════════════════════════════════════════════════════

    # ETH 15m LONG #1 — Score 20.41 | 전체 1위, min_calmar 1.427
    # 진입: CCI(20)<-100 AND MOM(10)>0
    # 필터: Vol≤SMA(20)*1.5
    "EL6_eth15m_CCI_MOM_VOL_INV": {
        "id":             "EL6_eth15m_CCI_MOM_VOL_INV",
        "symbol":         "ETH/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_eth15m_cci_mom_vol_inv",
        "score":          20.41,
        "survived_windows": 7,
        "avg_calmar":     7.4048,
        "min_calmar":     1.4269,
        "leverage":       19,       # 이론: 1/(0.04+0.005)=22.2x, safe=17.8x, ×1.05→18.7→19x
        "max_leverage":   22,       # 이론: floor(1/(0.04+0.005))=22
        "tp_type":        "fixed",
        "tp_mult":        0.05,      # TP 5.0%
        "sl_mult":        0.04,      # SL 4.0%
        "base_mdd":       0.04,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # ETH 15m LONG #2 — Score 19.72 | survived=8 최고 생존
    # 진입: SMA10>SMA20 AND MACD>Sig(12,26,9)
    # 필터: ATR(14)≤ATR_SMA
    "EL7_eth15m_SMA_MACD_ATR_INV": {
        "id":             "EL7_eth15m_SMA_MACD_ATR_INV",
        "symbol":         "ETH/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_eth15m_sma_macd_atr_inv",
        "score":          19.72,
        "survived_windows": 8,
        "avg_calmar":     1.6062,
        "min_calmar":     0.9206,
        "leverage":       20,       # 이론: 1/(0.02+0.005)=40x, safe=32x, →상한20x
        "max_leverage":   40,       # 이론: floor(1/(0.02+0.005))=40
        "tp_type":        "fixed",
        "tp_mult":        0.03,      # TP 3.0%
        "sl_mult":        0.02,      # SL 2.0%
        "base_mdd":       0.02,
        "max_hold_bars":  12,        # 12봉 (3시간)
    },

    # ETH 15m LONG #3 — Score 19.26 | survived=8, RR 6배
    # 진입: Close<BB_lo(20,2) AND EMA5>EMA26>EMA50
    # 필터: ADX(14)>25
    "EL8_eth15m_ADX_BB_EMA_STACK": {
        "id":             "EL8_eth15m_ADX_BB_EMA_STACK",
        "symbol":         "ETH/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_eth15m_adx_bb_ema_stack",
        "score":          19.26,
        "survived_windows": 8,
        "avg_calmar":     3.2983,
        "min_calmar":     0.6013,
        "leverage":       20,       # 이론: 40x, safe=32x, →상한20x
        "max_leverage":   40,       # 이론: floor(1/(0.02+0.005))=40
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.02,      # SL 2.0%
        "base_mdd":       0.02,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # ETH 15m LONG #4 — Score 19.24 | survived=8, 자금흐름+추세
    # 진입: WR(14)<-80 AND CMF(20)>0.1 AND AroonUp(25)>70
    "EL9_eth15m_WILLR_CMF_AROON": {
        "id":             "EL9_eth15m_WILLR_CMF_AROON",
        "symbol":         "ETH/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_eth15m_willr_cmf_aroon",
        "score":          19.24,
        "survived_windows": 8,
        "avg_calmar":     2.6708,
        "min_calmar":     0.6473,
        "leverage":       20,       # 이론: 1/(0.03+0.005)=28.6x, safe=22.9x, →상한20x
        "max_leverage":   28,       # 이론: floor(1/(0.03+0.005))=28
        "tp_type":        "fixed",
        "tp_mult":        0.04,      # TP 4.0%
        "sl_mult":        0.03,      # SL 3.0%
        "base_mdd":       0.03,
        "max_hold_bars":  24,        # 24봉 (6시간)
    },

    # ETH 15m LONG #5 — Score 19.12 | SMA+이치모쿠+CMF 삼중
    # 진입: SMA10>SMA20 AND Tenkan>Kijun AND CMF(20)>0.1
    "EL10_eth15m_SMA_ICHIMOKU_CMF": {
        "id":             "EL10_eth15m_SMA_ICHIMOKU_CMF",
        "symbol":         "ETH/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_eth15m_sma_ichimoku_cmf",
        "score":          19.12,
        "survived_windows": 7,
        "avg_calmar":     5.2551,
        "min_calmar":     1.0943,
        "leverage":       20,       # 이론: 40x, safe=32x, ×1.05→상한20x
        "max_leverage":   40,       # 이론: floor(1/(0.02+0.005))=40
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.02,      # SL 2.0%
        "base_mdd":       0.02,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # ═══════════════════════════════════════════════════════════
    # ETHUSDT 15분봉 SHORT 전략 — 상위 5개 (ETHUSDT_15m_WFA_Report.docx)
    # ═══════════════════════════════════════════════════════════

    # ETH 15m SHORT #1 — Score 19.24 | 최고 min_calmar 2.509
    # 진입: MFI(14)>80 AND MOM(10)<0 AND Close<VWAP(20)
    "ES6_eth15m_MFI_MOM_VWAP": {
        "id":             "ES6_eth15m_MFI_MOM_VWAP",
        "symbol":         "ETH/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_eth15m_mfi_mom_vwap",
        "score":          19.24,
        "survived_windows": 5,
        "avg_calmar":     4.5441,
        "min_calmar":     2.5089,
        "leverage":       15,       # 이론: 1/(0.05+0.005)=18.2x, safe=14.5x, ×1.05→15.2→15x
        "max_leverage":   18,       # 이론: floor(1/(0.05+0.005))=18
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.05,      # SL 5.0%
        "base_mdd":       0.05,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # ETH 15m SHORT #2 — Score 19.12 | survived=8 최고 생존, RR 12.5배
    # 진입: EMA12<EMA26 AND EMA5<EMA26<EMA50
    # 필터: ATR(14)>ATR_SMA
    "ES7_eth15m_EMA_ATR_SIG_EMA_STACK": {
        "id":             "ES7_eth15m_EMA_ATR_SIG_EMA_STACK",
        "symbol":         "ETH/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_eth15m_ema_atr_sig_ema_stack",
        "score":          19.12,
        "survived_windows": 8,
        "avg_calmar":     1.7243,
        "min_calmar":     0.7047,
        "leverage":       20,       # 이론: 1/(0.008+0.005)=76.9x, 슬리피지 감안→상한20x
        "max_leverage":   76,       # 이론: floor(1/(0.008+0.005))=76
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.008,     # SL 0.8%
        "base_mdd":       0.008,
        "max_hold_bars":  24,        # 24봉 (6시간)
    },

    # ETH 15m SHORT #3 — Score 18.71 | SMA+이치모쿠+EMA 삼중
    # 진입: SMA10<SMA20 AND Tenkan<Kijun AND EMA5<EMA26<EMA50
    "ES8_eth15m_SMA_ICHIMOKU_EMA_STACK": {
        "id":             "ES8_eth15m_SMA_ICHIMOKU_EMA_STACK",
        "symbol":         "ETH/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_eth15m_sma_ichimoku_ema_stack",
        "score":          18.71,
        "survived_windows": 7,
        "avg_calmar":     3.0854,
        "min_calmar":     1.1020,
        "leverage":       19,       # 이론: 22.2x, safe=17.8x, ×1.05→18.7→19x
        "max_leverage":   22,       # 이론: floor(1/(0.04+0.005))=22
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.04,      # SL 4.0%
        "base_mdd":       0.04,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # ETH 15m SHORT #4 — Score 18.29 | ADX+이치모쿠+EMA 필터
    # 진입: Tenkan<Kijun AND EMA5<EMA26<EMA50
    # 필터: ADX(14)>25
    "ES9_eth15m_ADX_ICHIMOKU_EMA_STACK": {
        "id":             "ES9_eth15m_ADX_ICHIMOKU_EMA_STACK",
        "symbol":         "ETH/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_eth15m_adx_ichimoku_ema_stack",
        "score":          18.29,
        "survived_windows": 7,
        "avg_calmar":     4.0802,
        "min_calmar":     0.8880,
        "leverage":       20,       # 이론: 76.9x, 슬리피지 감안→상한20x
        "max_leverage":   76,       # 이론: floor(1/(0.008+0.005))=76
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.008,     # SL 0.8%
        "base_mdd":       0.008,
        "max_hold_bars":  48,        # 48봉 (12시간)
    },

    # ETH 15m SHORT #5 — Score 17.88 | CMF+MFI 이중 자금흐름
    # 진입: CMF(20)<-0.1 AND MFI(14)>80 AND Close<VWAP(20)
    "ES10_eth15m_CMF_MFI_VWAP": {
        "id":             "ES10_eth15m_CMF_MFI_VWAP",
        "symbol":         "ETH/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_eth15m_cmf_mfi_vwap",
        "score":          17.88,
        "survived_windows": 5,
        "avg_calmar":     3.2116,
        "min_calmar":     2.1475,
        "leverage":       20,       # 이론: 1/(0.01+0.005)=66.7x, safe=53.3x, ×1.05→상한20x
        "max_leverage":   66,       # 이론: floor(1/(0.01+0.005))=66
        "tp_type":        "fixed",
        "tp_mult":        0.04,      # TP 4.0%
        "sl_mult":        0.01,      # SL 1.0%
        "base_mdd":       0.01,
        "max_hold_bars":  24,        # 24봉 (6시간)
    },

    # ═══════════════════════════════════════════════════════════
    # ETHUSDT 1시간봉 LONG 전략 — 상위 5개 (ETHUSDT_1h_WFA_Report.docx)
    # 3,231개 전략, IQR×3 제거 후 1,216개 → Score 상위 5개씩 선별
    # 레버리지: 이론=1/(SL%+0.5%), 권장=이론×80% (상한20x, min_calmar≥1.0→×1.05)
    # ═══════════════════════════════════════════════════════════

    # ETH 1h LONG #1 — Score 22.77 | survived=8, SMA 추세+거래량 확장+횡보 역발상
    # 진입: SMA10>SMA20 | 필터: Vol>SMA(20)*1.5 AND ADX(14)≤25
    "EL11_eth1h_SMA_VOLUME_ADX_INV": {
        "id":             "EL11_eth1h_SMA_VOLUME_ADX_INV",
        "symbol":         "ETH/USDT",
        "timeframe":      "1h",
        "direction":      "long",
        "entry_fn":       "entry_long_eth1h_sma_volume_adx_inv",
        "score":          22.77,
        "survived_windows": 8,
        "avg_calmar":     3.0141,
        "min_calmar":     1.7940,
        "leverage":       20,       # 이론: 1/(0.01+0.005)=66.7x, safe=53.3x, ×1.05→상한20x
        "max_leverage":   66,       # 이론: floor(1/(0.01+0.005))=66
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.01,      # SL 1.0%
        "base_mdd":       0.01,
        "max_hold_bars":  24,        # 24봉 (24시간)
    },

    # ETH 1h LONG #2 — Score 22.62 | survived=9 시리즈 최고, MACD+ADX+ROC 3중 모멘텀
    # 진입: MACD>Sig(12,26,9) AND ROC(10)>0% | 필터: ADX(14)>25
    "EL12_eth1h_MACD_ADX_ROC": {
        "id":             "EL12_eth1h_MACD_ADX_ROC",
        "symbol":         "ETH/USDT",
        "timeframe":      "1h",
        "direction":      "long",
        "entry_fn":       "entry_long_eth1h_macd_adx_roc",
        "score":          22.62,
        "survived_windows": 9,
        "avg_calmar":     2.6447,
        "min_calmar":     1.1097,
        "leverage":       20,       # 이론: 1/(0.03+0.005)=28.6x, safe=22.9x, ×1.05→상한20x
        "max_leverage":   28,       # 이론: floor(1/(0.03+0.005))=28
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.03,      # SL 3.0%
        "base_mdd":       0.03,
        "max_hold_bars":  24,        # 24봉 (24시간)
    },

    # ETH 1h LONG #3 — Score 22.58 | min_calmar 2.940, SMA+STDDEV+ADX_INV 횡보 탈출
    # 진입: SMA10>SMA20 AND STD↑&Close>SMA(20) | 필터: ADX(14)≤25
    "EL13_eth1h_SMA_STDDEV_ADX_INV": {
        "id":             "EL13_eth1h_SMA_STDDEV_ADX_INV",
        "symbol":         "ETH/USDT",
        "timeframe":      "1h",
        "direction":      "long",
        "entry_fn":       "entry_long_eth1h_sma_stddev_adx_inv",
        "score":          22.58,
        "survived_windows": 6,
        "avg_calmar":     4.8197,
        "min_calmar":     2.9403,
        "leverage":       20,       # 이론: 1/(0.015+0.005)=50x, safe=40x, ×1.05→상한20x
        "max_leverage":   50,       # 이론: floor(1/(0.015+0.005))=50
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.015,     # SL 1.5%
        "base_mdd":       0.015,
        "max_hold_bars":  48,        # 48봉 (48시간)
    },

    # ETH 1h LONG #4 — Score 22.14 | min_calmar 3.465 LONG 최고 안정, SMA+EMA 이중추세
    # 진입: SMA10>SMA20 AND EMA5>EMA26>EMA50 | 필터: ATR(14)>ATR_SMA
    "EL14_eth1h_SMA_ATR_SIG_EMA_STACK": {
        "id":             "EL14_eth1h_SMA_ATR_SIG_EMA_STACK",
        "symbol":         "ETH/USDT",
        "timeframe":      "1h",
        "direction":      "long",
        "entry_fn":       "entry_long_eth1h_sma_atr_sig_ema_stack",
        "score":          22.14,
        "survived_windows": 5,
        "avg_calmar":     4.7330,
        "min_calmar":     3.4648,
        "leverage":       20,       # 이론: 1/(0.005+0.005)=100x, SL 타이트→상한20x
        "max_leverage":   100,      # 이론: floor(1/(0.005+0.005))=100
        "tp_type":        "fixed",
        "tp_mult":        0.03,      # TP 3.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  12,        # 12봉 (12시간)
    },

    # ETH 1h LONG #5 — Score 21.73 | OBV+VWAP+ATR_INV 자금흐름 3중 확인
    # 진입: OBV>OBV_SMA(20) AND Close>VWAP(20) | 필터: ATR(14)≤ATR_SMA
    "EL15_eth1h_OBV_VWAP_ATR_INV": {
        "id":             "EL15_eth1h_OBV_VWAP_ATR_INV",
        "symbol":         "ETH/USDT",
        "timeframe":      "1h",
        "direction":      "long",
        "entry_fn":       "entry_long_eth1h_obv_vwap_atr_inv",
        "score":          21.73,
        "survived_windows": 6,
        "avg_calmar":     5.0107,
        "min_calmar":     2.6462,
        "leverage":       19,       # 이론: 1/(0.04+0.005)=22.2x, safe=17.8x, ×1.05→18.7→19x
        "max_leverage":   22,       # 이론: floor(1/(0.04+0.005))=22
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.04,      # SL 4.0%
        "base_mdd":       0.04,
        "max_hold_bars":  48,        # 48봉 (48시간)
    },

    # ═══════════════════════════════════════════════════════════
    # ETHUSDT 1시간봉 SHORT 전략 — 상위 5개 (ETHUSDT_1h_WFA_Report.docx)
    # ═══════════════════════════════════════════════════════════

    # ETH 1h SHORT #1 — Score 24.90 | 전 시리즈 최고 Score, survived=10 유일
    # 진입: SAR↓(0.02,0.2) AND AroonDn(25)>70 | 필터: ATR(14)>ATR_SMA
    "ES11_eth1h_PSAR_ATR_SIG_AROON": {
        "id":             "ES11_eth1h_PSAR_ATR_SIG_AROON",
        "symbol":         "ETH/USDT",
        "timeframe":      "1h",
        "direction":      "short",
        "entry_fn":       "entry_short_eth1h_psar_atr_sig_aroon",
        "score":          24.90,
        "survived_windows": 10,
        "avg_calmar":     4.2767,
        "min_calmar":     1.0798,
        "leverage":       13,       # 이론: 1/(0.06+0.005)=15.4x, safe=12.3x, ×1.05→12.9→13x
        "max_leverage":   15,       # 이론: floor(1/(0.06+0.005))=15
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.06,      # SL 6.0%
        "base_mdd":       0.06,
        "max_hold_bars":  24,        # 24봉 (24시간)
    },

    # ETH 1h SHORT #2 — Score 24.58 | min_calmar 4.195 전시리즈 최고 안정
    # 진입: Close>BB_hi(20,2) AND CMF(20)<-0.1 | 필터: Vol>SMA(20)*1.5
    "ES12_eth1h_BB_CMF_VOLUME": {
        "id":             "ES12_eth1h_BB_CMF_VOLUME",
        "symbol":         "ETH/USDT",
        "timeframe":      "1h",
        "direction":      "short",
        "entry_fn":       "entry_short_eth1h_bb_cmf_volume",
        "score":          24.58,
        "survived_windows": 5,
        "avg_calmar":     6.3417,
        "min_calmar":     4.1950,
        "leverage":       20,       # 이론: 1/(0.01+0.005)=66.7x, safe=53.3x, ×1.05→상한20x
        "max_leverage":   66,       # 이론: floor(1/(0.01+0.005))=66
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.01,      # SL 1.0%
        "base_mdd":       0.01,
        "max_hold_bars":  48,        # 48봉 (48시간)
    },

    # ETH 1h SHORT #3 — Score 24.11 | survived=8, PSAR+STDDEV+ATR_INV 저변동 역발상
    # 진입: SAR↓(0.02,0.2) AND STD↑&Close<SMA(20) | 필터: ATR(14)≤ATR_SMA
    "ES13_eth1h_PSAR_STDDEV_ATR_INV": {
        "id":             "ES13_eth1h_PSAR_STDDEV_ATR_INV",
        "symbol":         "ETH/USDT",
        "timeframe":      "1h",
        "direction":      "short",
        "entry_fn":       "entry_short_eth1h_psar_stddev_atr_inv",
        "score":          24.11,
        "survived_windows": 8,
        "avg_calmar":     4.2453,
        "min_calmar":     2.1512,
        "leverage":       20,       # 이론: 1/(0.01+0.005)=66.7x, safe=53.3x, ×1.05→상한20x
        "max_leverage":   66,       # 이론: floor(1/(0.01+0.005))=66
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.01,      # SL 1.0%
        "base_mdd":       0.01,
        "max_hold_bars":  48,        # 48봉 (48시간)
    },

    # ETH 1h SHORT #4 — Score 23.95 | survived=9, WR 과매수+횡보+저거래량 이중 역발상
    # 진입: WR(14)>-20 | 필터: ADX(14)≤25 AND Vol≤SMA(20)*1.5
    "ES14_eth1h_WILLR_ADX_INV_VOL_INV": {
        "id":             "ES14_eth1h_WILLR_ADX_INV_VOL_INV",
        "symbol":         "ETH/USDT",
        "timeframe":      "1h",
        "direction":      "short",
        "entry_fn":       "entry_short_eth1h_willr_adx_inv_vol_inv",
        "score":          23.95,
        "survived_windows": 9,
        "avg_calmar":     2.6355,
        "min_calmar":     1.5525,
        "leverage":       19,       # 이론: 1/(0.04+0.005)=22.2x, safe=17.8x, ×1.05→18.7→19x
        "max_leverage":   22,       # 이론: floor(1/(0.04+0.005))=22
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.04,      # SL 4.0%
        "base_mdd":       0.04,
        "max_hold_bars":  48,        # 48봉 (48시간)
    },

    # ETH 1h SHORT #5 — Score 23.84 | survived=9, PSAR+거래량 폭발+하방 STDDEV
    # 진입: SAR↓(0.02,0.2) AND STD↑&Close<SMA(20) | 필터: Vol>SMA(20)*1.5
    "ES15_eth1h_PSAR_VOLUME_STDDEV": {
        "id":             "ES15_eth1h_PSAR_VOLUME_STDDEV",
        "symbol":         "ETH/USDT",
        "timeframe":      "1h",
        "direction":      "short",
        "entry_fn":       "entry_short_eth1h_psar_volume_stddev",
        "score":          23.84,
        "survived_windows": 9,
        "avg_calmar":     3.7774,
        "min_calmar":     1.4244,
        "leverage":       20,       # 이론: 1/(0.03+0.005)=28.6x, safe=22.9x, ×1.05→상한20x
        "max_leverage":   28,       # 이론: floor(1/(0.03+0.005))=28
        "tp_type":        "fixed",
        "tp_mult":        0.05,      # TP 5.0%
        "sl_mult":        0.03,      # SL 3.0%
        "base_mdd":       0.03,
        "max_hold_bars":  48,        # 48봉 (48시간)
    },

    # ═══════════════════════════════════════════════════════════════
    # ETHUSDT 4시간봉 LONG 전략 (5개) — ETHUSDT_4h_WFA_Report.docx
    # 1,870개 전략 → IQR×3 제거 885개 → Score 상위 5개
    # ═══════════════════════════════════════════════════════════════

    # ETH 4h LONG #1 — Score 29.73 | survived=9, 변동성 확대+고거래량+횡보 제거
    # 진입: STD↑&Close>SMA(20) | 필터: Vol>SMA(20)×1.5 AND ADX(14)≤25
    "EL16_eth4h_VOLUME_STDDEV_ADX_INV": {
        "id":             "EL16_eth4h_VOLUME_STDDEV_ADX_INV",
        "symbol":         "ETH/USDT",
        "timeframe":      "4h",
        "direction":      "long",
        "entry_fn":       "entry_long_eth4h_volume_stddev_adx_inv",
        "score":          29.73,
        "survived_windows": 9,
        "avg_calmar":     7.1764,
        "min_calmar":     1.2820,
        "leverage":       20,       # min((1-0.005)/0.015×0.8, 20)=20x
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.015,     # SL 1.5%
        "base_mdd":       0.015,
        "max_hold_bars":  48,        # 48봉 (192시간)
    },

    # ETH 4h LONG #2 — Score 29.12 | survived=9, 일목+OBV+VWAP 3중 확인 단기형
    # 진입: Tenkan>Kijun AND OBV>OBV_SMA(20) AND Close>VWAP(20)
    "EL17_eth4h_ICHIMOKU_OBV_VWAP": {
        "id":             "EL17_eth4h_ICHIMOKU_OBV_VWAP",
        "symbol":         "ETH/USDT",
        "timeframe":      "4h",
        "direction":      "long",
        "entry_fn":       "entry_long_eth4h_ichimoku_obv_vwap",
        "score":          29.12,
        "survived_windows": 9,
        "avg_calmar":     7.1764,
        "min_calmar":     1.4965,
        "leverage":       20,       # min((1-0.005)/0.02×0.8, 20)=20x
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.02,      # SL 2.0%
        "base_mdd":       0.02,
        "max_hold_bars":  4,         # 4봉 (16시간)
    },

    # ETH 4h LONG #3 — Score 29.03 | survived=9, MACD+VWAP+저거래량 조용한 추세
    # 진입: MACD>Sig(12,26,9) AND Close>VWAP(20) | 필터: Vol≤SMA(20)×1.5
    "EL18_eth4h_MACD_VWAP_VOL_INV": {
        "id":             "EL18_eth4h_MACD_VWAP_VOL_INV",
        "symbol":         "ETH/USDT",
        "timeframe":      "4h",
        "direction":      "long",
        "entry_fn":       "entry_long_eth4h_macd_vwap_vol_inv",
        "score":          29.03,
        "survived_windows": 9,
        "avg_calmar":     4.9635,
        "min_calmar":     0.8906,
        "leverage":       20,       # min((1-0.005)/0.01×0.8, 20)=20x (상한)
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.01,      # SL 1.0%
        "base_mdd":       0.01,
        "max_hold_bars":  24,        # 24봉 (96시간)
    },

    # ETH 4h LONG #4 — Score 28.13 | survived=9, 일목+VWAP 2지표 단순 안정형
    # 진입: Tenkan>Kijun AND Close>VWAP(20)
    "EL19_eth4h_ICHIMOKU_VWAP": {
        "id":             "EL19_eth4h_ICHIMOKU_VWAP",
        "symbol":         "ETH/USDT",
        "timeframe":      "4h",
        "direction":      "long",
        "entry_fn":       "entry_long_eth4h_ichimoku_vwap",
        "score":          28.13,
        "survived_windows": 9,
        "avg_calmar":     2.9437,
        "min_calmar":     1.6028,
        "leverage":       20,       # min((1-0.005)/0.01×0.8, 20)=20x (상한)
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.01,      # SL 1.0%
        "base_mdd":       0.01,
        "max_hold_bars":  24,        # 24봉 (96시간)
    },

    # ETH 4h LONG #5 — Score 28.13 | survived=9, 일목+VWAP+ATR 저변동성 필터
    # 진입: Tenkan>Kijun AND Close>VWAP(20) | 필터: ATR(14)≤ATR_SMA
    "EL20_eth4h_ICHIMOKU_VWAP_ATR_INV": {
        "id":             "EL20_eth4h_ICHIMOKU_VWAP_ATR_INV",
        "symbol":         "ETH/USDT",
        "timeframe":      "4h",
        "direction":      "long",
        "entry_fn":       "entry_long_eth4h_ichimoku_vwap_atr_inv",
        "score":          28.13,
        "survived_windows": 9,
        "avg_calmar":     2.9437,
        "min_calmar":     1.6028,
        "leverage":       20,       # min((1-0.005)/0.01×0.8, 20)=20x (상한)
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.01,      # SL 1.0%
        "base_mdd":       0.01,
        "max_hold_bars":  24,        # 24봉 (96시간)
    },

    # ═══════════════════════════════════════════════════════════════
    # ETHUSDT 4시간봉 SHORT 전략 (5개) — ETHUSDT_4h_WFA_Report.docx
    # ═══════════════════════════════════════════════════════════════

    # ETH 4h SHORT #1 — Score 29.09 | survived=11 (전체 데이터셋 최고), 일목+VWAP 앵커
    # 진입: Tenkan<Kijun AND Close<VWAP(20)
    "ES16_eth4h_ICHIMOKU_VWAP": {
        "id":             "ES16_eth4h_ICHIMOKU_VWAP",
        "symbol":         "ETH/USDT",
        "timeframe":      "4h",
        "direction":      "short",
        "entry_fn":       "entry_short_eth4h_ichimoku_vwap",
        "score":          29.09,
        "survived_windows": 11,
        "avg_calmar":     2.2982,
        "min_calmar":     1.1119,
        "leverage":       19,       # min((1-0.005)/0.04×0.8, 20)=19.8→19x
        "max_leverage":   24,
        "tp_type":        "fixed",
        "tp_mult":        0.05,      # TP 5.0%
        "sl_mult":        0.04,      # SL 4.0%
        "base_mdd":       0.04,
        "max_hold_bars":  24,        # 24봉 (96시간)
    },

    # ETH 4h SHORT #2 — Score 29.09 | survived=11 (전체 데이터셋 최고), ATR 저변동 필터
    # 진입: Tenkan<Kijun AND Close<VWAP(20) | 필터: ATR(14)≤ATR_SMA
    "ES17_eth4h_ICHIMOKU_VWAP_ATR_INV": {
        "id":             "ES17_eth4h_ICHIMOKU_VWAP_ATR_INV",
        "symbol":         "ETH/USDT",
        "timeframe":      "4h",
        "direction":      "short",
        "entry_fn":       "entry_short_eth4h_ichimoku_vwap_atr_inv",
        "score":          29.09,
        "survived_windows": 11,
        "avg_calmar":     2.2982,
        "min_calmar":     1.1119,
        "leverage":       19,       # min((1-0.005)/0.04×0.8, 20)=19.8→19x
        "max_leverage":   24,
        "tp_type":        "fixed",
        "tp_mult":        0.05,      # TP 5.0%
        "sl_mult":        0.04,      # SL 4.0%
        "base_mdd":       0.04,
        "max_hold_bars":  24,        # 24봉 (96시간)
    },

    # ETH 4h SHORT #3 — Score 27.14 | survived=9, OBV 매도세 확인 추가
    # 진입: Tenkan<Kijun AND OBV<OBV_SMA(20) AND Close<VWAP(20)
    "ES18_eth4h_ICHIMOKU_OBV_VWAP": {
        "id":             "ES18_eth4h_ICHIMOKU_OBV_VWAP",
        "symbol":         "ETH/USDT",
        "timeframe":      "4h",
        "direction":      "short",
        "entry_fn":       "entry_short_eth4h_ichimoku_obv_vwap",
        "score":          27.14,
        "survived_windows": 9,
        "avg_calmar":     6.7298,
        "min_calmar":     0.6361,
        "leverage":       19,       # min((1-0.005)/0.04×0.8, 20)=19.8→19x
        "max_leverage":   24,
        "tp_type":        "fixed",
        "tp_mult":        0.05,      # TP 5.0%
        "sl_mult":        0.04,      # SL 4.0%
        "base_mdd":       0.04,
        "max_hold_bars":  24,        # 24봉 (96시간)
    },

    # ETH 4h SHORT #4 — Score 26.84 | survived=8, PSAR+ADX 역발상 횡보 수익
    # 진입: SAR↓(0.02,0.2) | 필터: ADX(14)≤25
    "ES19_eth4h_PSAR_ADX_INV": {
        "id":             "ES19_eth4h_PSAR_ADX_INV",
        "symbol":         "ETH/USDT",
        "timeframe":      "4h",
        "direction":      "short",
        "entry_fn":       "entry_short_eth4h_psar_adx_inv",
        "score":          26.84,
        "survived_windows": 8,
        "avg_calmar":     4.4092,
        "min_calmar":     1.8360,
        "leverage":       20,       # min((1-0.005)/0.02×0.8, 20)=20x
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.02,      # SL 2.0%
        "base_mdd":       0.02,
        "max_hold_bars":  48,        # 48봉 (192시간)
    },

    # ETH 4h SHORT #5 — Score 26.84 | survived=8, PSAR+ADX+ATR 이중 역필터 보수적
    # 진입: SAR↓(0.02,0.2) | 필터: ADX(14)≤25 AND ATR(14)≤ATR_SMA
    "ES20_eth4h_PSAR_ADX_INV_ATR_INV": {
        "id":             "ES20_eth4h_PSAR_ADX_INV_ATR_INV",
        "symbol":         "ETH/USDT",
        "timeframe":      "4h",
        "direction":      "short",
        "entry_fn":       "entry_short_eth4h_psar_adx_inv_atr_inv",
        "score":          26.84,
        "survived_windows": 8,
        "avg_calmar":     4.4092,
        "min_calmar":     1.8360,
        "leverage":       20,       # min((1-0.005)/0.02×0.8, 20)=20x
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.02,      # SL 2.0%
        "base_mdd":       0.02,
        "max_hold_bars":  48,        # 48봉 (192시간)
    },

    # ═══════════════════════════════════════════════════════════════
    # XRPUSDT 5분봉 LONG 전략 (5개) — XRPUSDT_5m_WFA_Report.docx
    # 1,100개 전략 → IQR×3 제거 206개 → Score 상위 5개
    # surv≥4 완화 적용 (최대 7윈도우)
    # ═══════════════════════════════════════════════════════════════

    # XRP 5m LONG #1 — Score 23.22 | survived=6, OBV+CCI과매도+MFI저조 3중 확인
    # 진입: OBV>OBV_SMA(20) AND CCI(20)<-100 AND MFI(14)<20
    "XL1_xrp5m_OBV_CCI_MFI": {
        "id":             "XL1_xrp5m_OBV_CCI_MFI",
        "symbol":         "XRP/USDT",
        "timeframe":      "5m",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp5m_obv_cci_mfi",
        "score":          23.22,
        "survived_windows": 6,
        "avg_calmar":     2.2543,
        "min_calmar":     1.5191,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  48,        # 48봉 (240분 = 4시간)
    },

    # XRP 5m LONG #2 — Score 21.97 | survived=6, 스토캐스틱+OBV+MFI 반전형
    # 진입: %K(14)<20 AND OBV>OBV_SMA(20) AND MFI(14)<20
    "XL2_xrp5m_STOCH_OBV_MFI": {
        "id":             "XL2_xrp5m_STOCH_OBV_MFI",
        "symbol":         "XRP/USDT",
        "timeframe":      "5m",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp5m_stoch_obv_mfi",
        "score":          21.97,
        "survived_windows": 6,
        "avg_calmar":     2.3346,
        "min_calmar":     1.1318,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  48,        # 48봉 (240분)
    },

    # XRP 5m LONG #3 — Score 20.49 | survived=4, SMA+EMA+PSAR 고전 추세추종
    # 진입: SMA10>SMA20 AND EMA12>EMA26 AND SAR↑(0.02,0.2)
    "XL3_xrp5m_SMA_EMA_PSAR": {
        "id":             "XL3_xrp5m_SMA_EMA_PSAR",
        "symbol":         "XRP/USDT",
        "timeframe":      "5m",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp5m_sma_ema_psar",
        "score":          20.49,
        "survived_windows": 4,
        "avg_calmar":     5.4664,
        "min_calmar":     1.7833,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  48,        # 48봉 (240분)
    },

    # XRP 5m LONG #4 — Score 20.49 | survived=5, 일목+ADX 강추세+볼륨 폭발
    # 진입: Tenkan>Kijun | 필터: ADX(14)>25 AND Vol>SMA(20)×1.5
    "XL4_xrp5m_ADX_ICHIMOKU_VOLUME": {
        "id":             "XL4_xrp5m_ADX_ICHIMOKU_VOLUME",
        "symbol":         "XRP/USDT",
        "timeframe":      "5m",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp5m_adx_ichimoku_volume",
        "score":          20.49,
        "survived_windows": 5,
        "avg_calmar":     3.4301,
        "min_calmar":     1.0436,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.008,     # SL 0.8%
        "base_mdd":       0.008,
        "max_hold_bars":  48,        # 48봉 (240분)
    },

    # XRP 5m LONG #5 — Score 20.29 | survived=4, SMA+돈치안 돌파+STDDEV 확대
    # 진입: SMA10>SMA20 AND Close>DC_hi(20) AND STD↑&Close>SMA(20)
    "XL5_xrp5m_SMA_DONCHIAN_STDDEV": {
        "id":             "XL5_xrp5m_SMA_DONCHIAN_STDDEV",
        "symbol":         "XRP/USDT",
        "timeframe":      "5m",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp5m_sma_donchian_stddev",
        "score":          20.29,
        "survived_windows": 4,
        "avg_calmar":     5.8510,
        "min_calmar":     0.4101,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  48,        # 48봉 (240분)
    },

    # ═══════════════════════════════════════════════════════════════
    # XRPUSDT 5분봉 SHORT 전략 (5개) — XRPUSDT_5m_WFA_Report.docx
    # ═══════════════════════════════════════════════════════════════

    # XRP 5m SHORT #1 — Score 21.13 | survived=6, SMA+CCI과매수+횡보 역추세
    # 진입: SMA10<SMA20 AND CCI(20)>+100 | 필터: ADX(14)≤25
    "XS1_xrp5m_SMA_CCI_ADX_INV": {
        "id":             "XS1_xrp5m_SMA_CCI_ADX_INV",
        "symbol":         "XRP/USDT",
        "timeframe":      "5m",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp5m_sma_cci_adx_inv",
        "score":          21.13,
        "survived_windows": 6,
        "avg_calmar":     3.7476,
        "min_calmar":     0.6839,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.02,      # TP 2.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  48,        # 48봉 (240분)
    },

    # XRP 5m SHORT #2 — Score 20.94 | survived=6, RSI+WR 이중과매수+EMA 하락
    # 진입: RSI(14)>70 AND WR(14)>-20 AND EMA5<EMA26<EMA50
    "XS2_xrp5m_RSI_WILLR_EMA_STACK": {
        "id":             "XS2_xrp5m_RSI_WILLR_EMA_STACK",
        "symbol":         "XRP/USDT",
        "timeframe":      "5m",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp5m_rsi_willr_ema_stack",
        "score":          20.94,
        "survived_windows": 6,
        "avg_calmar":     3.1885,
        "min_calmar":     0.4380,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.01,      # SL 1.0%
        "base_mdd":       0.01,
        "max_hold_bars":  48,        # 48봉 (240분)
    },

    # XRP 5m SHORT #3 — Score 20.27 | survived=6, SMA+EMA 하락+볼륨 급증
    # 진입: SMA10<SMA20 AND EMA12<EMA26 | 필터: Vol>SMA(20)×1.5
    "XS3_xrp5m_SMA_EMA_VOLUME": {
        "id":             "XS3_xrp5m_SMA_EMA_VOLUME",
        "symbol":         "XRP/USDT",
        "timeframe":      "5m",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp5m_sma_ema_volume",
        "score":          20.27,
        "survived_windows": 6,
        "avg_calmar":     3.2819,
        "min_calmar":     1.2684,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.04,      # TP 4.0%
        "sl_mult":        0.03,      # SL 3.0%
        "base_mdd":       0.03,
        "max_hold_bars":  48,        # 48봉 (240분)
    },

    # XRP 5m SHORT #4 — Score 19.85 | survived=5, OBV 매도+CCI과매수+MOM 하락
    # 진입: OBV<OBV_SMA(20) AND CCI(20)>+100 AND MOM(10)<0
    "XS4_xrp5m_OBV_CCI_MOM": {
        "id":             "XS4_xrp5m_OBV_CCI_MOM",
        "symbol":         "XRP/USDT",
        "timeframe":      "5m",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp5m_obv_cci_mom",
        "score":          19.85,
        "survived_windows": 5,
        "avg_calmar":     2.0004,
        "min_calmar":     1.3455,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  48,        # 48봉 (240분)
    },

    # XRP 5m SHORT #5 — Score 19.85 | survived=5, OBV 매도+CCI과매수+ROC 하락
    # 진입: OBV<OBV_SMA(20) AND CCI(20)>+100 AND ROC(10)<0%
    "XS5_xrp5m_OBV_CCI_ROC": {
        "id":             "XS5_xrp5m_OBV_CCI_ROC",
        "symbol":         "XRP/USDT",
        "timeframe":      "5m",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp5m_obv_cci_roc",
        "score":          19.85,
        "survived_windows": 5,
        "avg_calmar":     2.0004,
        "min_calmar":     1.3455,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  48,        # 48봉 (240분)
    },

    # ═══════════════════════════════════════════════════════════════
    # XRPUSDT 15분봉 LONG 전략 (5개) — XRPUSDT_15m_WFA_Report.docx
    # 3,227개 전략 → 필터 후 460개 → Score 상위 5개
    # surv≥5, avg_calmar≥1.5, min_calmar≥0.4 기준
    # ═══════════════════════════════════════════════════════════════

    # XRP 15m LONG #1 — Score 27.36 | survived=9, %K과매도+AroonUp 모멘텀
    # 진입: %K(14)<20 AND AroonUp(25)>70
    "XL6_xrp15m_STOCH_AROON": {
        "id":             "XL6_xrp15m_STOCH_AROON",
        "symbol":         "XRP/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp15m_stoch_aroon",
        "score":          27.36,
        "survived_windows": 9,
        "avg_calmar":     1.8865,
        "min_calmar":     0.6691,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.008,     # SL 0.8%
        "base_mdd":       0.008,
        "max_hold_bars":  48,        # 48봉 (720분 = 12시간)
    },

    # XRP 15m LONG #2 — Score 27.36 | survived=9, %K+WR 이중과매도+AroonUp
    # 진입: %K(14)<20 AND WR(14)<-80 AND AroonUp(25)>70
    "XL7_xrp15m_STOCH_WILLR_AROON": {
        "id":             "XL7_xrp15m_STOCH_WILLR_AROON",
        "symbol":         "XRP/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp15m_stoch_willr_aroon",
        "score":          27.36,
        "survived_windows": 9,
        "avg_calmar":     1.8865,
        "min_calmar":     0.6691,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.008,     # SL 0.8%
        "base_mdd":       0.008,
        "max_hold_bars":  48,        # 48봉 (720분 = 12시간)
    },

    # XRP 15m LONG #3 — Score 27.36 | survived=9, %K+AroonUp+ATR저변동 필터
    # 진입: %K(14)<20 AND AroonUp(25)>70 [F]ATR(14)≤ATR_SMA
    "XL8_xrp15m_STOCH_AROON_ATR_INV": {
        "id":             "XL8_xrp15m_STOCH_AROON_ATR_INV",
        "symbol":         "XRP/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp15m_stoch_aroon_atr_inv",
        "score":          27.36,
        "survived_windows": 9,
        "avg_calmar":     1.8865,
        "min_calmar":     0.6691,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.008,     # SL 0.8%
        "base_mdd":       0.008,
        "max_hold_bars":  48,        # 48봉 (720분 = 12시간)
    },

    # XRP 15m LONG #4 — Score 24.19 | survived=7, MACD+AroonUp+돈치안 돌파
    # 진입: MACD>Signal AND AroonUp(25)>70 AND Close>DC_hi(20)
    "XL9_xrp15m_MACD_AROON_DONCHIAN": {
        "id":             "XL9_xrp15m_MACD_AROON_DONCHIAN",
        "symbol":         "XRP/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp15m_macd_aroon_donchian",
        "score":          24.19,
        "survived_windows": 7,
        "avg_calmar":     3.3524,
        "min_calmar":     1.3655,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.015,     # SL 1.5%
        "base_mdd":       0.015,
        "max_hold_bars":  48,        # 48봉 (720분 = 12시간)
    },

    # XRP 15m LONG #5 — Score 23.96 | survived=8, EMA+일목+볼륨폭발
    # 진입: EMA12>EMA26 AND Tenkan>Kijun [F]Vol>SMA(20)×1.5
    "XL10_xrp15m_EMA_ICHIMOKU_VOLUME": {
        "id":             "XL10_xrp15m_EMA_ICHIMOKU_VOLUME",
        "symbol":         "XRP/USDT",
        "timeframe":      "15m",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp15m_ema_ichimoku_volume",
        "score":          23.96,
        "survived_windows": 8,
        "avg_calmar":     3.6758,
        "min_calmar":     0.4086,
        "leverage":       19,
        "max_leverage":   19,
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.04,      # SL 4.0%
        "base_mdd":       0.04,
        "max_hold_bars":  48,        # 48봉 (720분 = 12시간)
    },

    # ═══════════════════════════════════════════════════════════════
    # XRPUSDT 15분봉 SHORT 전략 (5개) — XRPUSDT_15m_WFA_Report.docx
    # ═══════════════════════════════════════════════════════════════

    # XRP 15m SHORT #1 — Score 24.55 | survived=8, SMA+EMA 하락+ATR확대
    # 진입: SMA10<SMA20 AND EMA12<EMA26 [F]ATR(14)>ATR_SMA
    "XS6_xrp15m_SMA_EMA_ATR_SIG": {
        "id":             "XS6_xrp15m_SMA_EMA_ATR_SIG",
        "symbol":         "XRP/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp15m_sma_ema_atr_sig",
        "score":          24.55,
        "survived_windows": 8,
        "avg_calmar":     2.1182,
        "min_calmar":     0.5206,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.01,      # SL 1.0%
        "base_mdd":       0.01,
        "max_hold_bars":  48,        # 48봉 (720분 = 12시간)
    },

    # XRP 15m SHORT #2 — Score 24.20 | survived=8, SMA+EMA+STDDEV 확대
    # 진입: SMA10<SMA20 AND EMA12<EMA26 AND STD↑&Close<SMA(20)
    "XS7_xrp15m_SMA_EMA_STDDEV": {
        "id":             "XS7_xrp15m_SMA_EMA_STDDEV",
        "symbol":         "XRP/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp15m_sma_ema_stddev",
        "score":          24.20,
        "survived_windows": 8,
        "avg_calmar":     2.2338,
        "min_calmar":     0.4603,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.01,      # SL 1.0%
        "base_mdd":       0.01,
        "max_hold_bars":  48,        # 48봉 (720분 = 12시간)
    },

    # XRP 15m SHORT #3 — Score 23.79 | survived=7, %K과매수+CMF유출+횡보
    # 진입: %K(14)>80 AND CMF(20)<-0.1 [F]ADX(14)≤25
    "XS8_xrp15m_STOCH_CMF_ADX_INV": {
        "id":             "XS8_xrp15m_STOCH_CMF_ADX_INV",
        "symbol":         "XRP/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp15m_stoch_cmf_adx_inv",
        "score":          23.79,
        "survived_windows": 7,
        "avg_calmar":     2.9286,
        "min_calmar":     1.0025,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.04,      # TP 4.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  48,        # 48봉 (720분 = 12시간)
    },

    # XRP 15m SHORT #4 — Score 23.71 | survived=8, RSI+BB+MFI 3중과매수
    # 진입: RSI(14)>70 AND Close>BB_hi(20,2) AND MFI(14)>80
    "XS9_xrp15m_RSI_BB_MFI": {
        "id":             "XS9_xrp15m_RSI_BB_MFI",
        "symbol":         "XRP/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp15m_rsi_bb_mfi",
        "score":          23.71,
        "survived_windows": 8,
        "avg_calmar":     2.1080,
        "min_calmar":     0.7376,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.03,      # SL 3.0%
        "base_mdd":       0.03,
        "max_hold_bars":  48,        # 48봉 (720분 = 12시간)
    },

    # XRP 15m SHORT #5 — Score 23.47 | survived=8, BB+켈트너 이중상단+MFI과매수
    # 진입: Close>BB_hi(20,2) AND Close>KC_hi(20,2) AND MFI(14)>80
    "XS10_xrp15m_BB_KELTNER_MFI": {
        "id":             "XS10_xrp15m_BB_KELTNER_MFI",
        "symbol":         "XRP/USDT",
        "timeframe":      "15m",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp15m_bb_keltner_mfi",
        "score":          23.47,
        "survived_windows": 8,
        "avg_calmar":     2.5318,
        "min_calmar":     0.8741,
        "leverage":       15,
        "max_leverage":   15,
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.05,      # SL 5.0%
        "base_mdd":       0.05,
        "max_hold_bars":  48,        # 48봉 (720분 = 12시간)
    },

    # ═══════════════════════════════════════════════════════════════
    # XRPUSDT 1시간봉 LONG 전략 (5개) — XRPUSDT_1h_WFA_Report.docx
    # 3,234개 전략 → 필터 후 1,139개 → Score 상위 5개
    # surv≥5, avg_calmar≥1.5, min_calmar≥0.4 기준
    # ═══════════════════════════════════════════════════════════════

    # XRP 1h LONG #1 — Score 26.97 | survived=7, PSAR+EMA스택+저거래량
    "XL11_xrp1h_PSAR_EMA_STACK_VOL_INV": {
        "id":             "XL11_xrp1h_PSAR_EMA_STACK_VOL_INV",
        "symbol":         "XRP/USDT",
        "timeframe":      "1h",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp1h_psar_ema_stack_vol_inv",
        "score":          26.97,
        "survived_windows": 7,
        "avg_calmar":     3.9881,
        "min_calmar":     1.9927,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.05,      # TP 5.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  12,        # 12봉 (12시간)
    },

    # XRP 1h LONG #2 — Score 26.29 | survived=6, %K+WR이중과매도+ATR확대
    "XL12_xrp1h_STOCH_WILLR_ATR_SIG": {
        "id":             "XL12_xrp1h_STOCH_WILLR_ATR_SIG",
        "symbol":         "XRP/USDT",
        "timeframe":      "1h",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp1h_stoch_willr_atr_sig",
        "score":          26.29,
        "survived_windows": 6,
        "avg_calmar":     4.7808,
        "min_calmar":     1.5612,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.008,     # SL 0.8%
        "base_mdd":       0.008,
        "max_hold_bars":  48,        # 48봉 (48시간)
    },

    # XRP 1h LONG #3 — Score 26.29 | survived=6, %K과매도+ATR확대
    "XL13_xrp1h_STOCH_ATR_SIG": {
        "id":             "XL13_xrp1h_STOCH_ATR_SIG",
        "symbol":         "XRP/USDT",
        "timeframe":      "1h",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp1h_stoch_atr_sig",
        "score":          26.29,
        "survived_windows": 6,
        "avg_calmar":     4.7808,
        "min_calmar":     1.5612,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.008,     # SL 0.8%
        "base_mdd":       0.008,
        "max_hold_bars":  48,        # 48봉 (48시간)
    },

    # XRP 1h LONG #4 — Score 26.26 | survived=7, PSAR+CMF+Aroon 3중
    "XL14_xrp1h_PSAR_CMF_AROON": {
        "id":             "XL14_xrp1h_PSAR_CMF_AROON",
        "symbol":         "XRP/USDT",
        "timeframe":      "1h",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp1h_psar_cmf_aroon",
        "score":          26.26,
        "survived_windows": 7,
        "avg_calmar":     3.7254,
        "min_calmar":     1.5854,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  24,        # 24봉 (24시간)
    },

    # XRP 1h LONG #5 — Score 26.18 | survived=8, SMA+OBV+ATR확대
    "XL15_xrp1h_SMA_OBV_ATR_SIG": {
        "id":             "XL15_xrp1h_SMA_OBV_ATR_SIG",
        "symbol":         "XRP/USDT",
        "timeframe":      "1h",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp1h_sma_obv_atr_sig",
        "score":          26.18,
        "survived_windows": 8,
        "avg_calmar":     3.7044,
        "min_calmar":     0.5639,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.008,     # SL 0.8%
        "base_mdd":       0.008,
        "max_hold_bars":  24,        # 24봉 (24시간)
    },

    # ═══════════════════════════════════════════════════════════════
    # XRPUSDT 1시간봉 SHORT 전략 (5개) — XRPUSDT_1h_WFA_Report.docx
    # SHORT #1 Score 32.16 전체 최고, SHORT #2 surv=12 XRP 전체 최고
    # ═══════════════════════════════════════════════════════════════

    # XRP 1h SHORT #1 — Score 32.16 | survived=9, MACD+ADX+Aroon 추세확인
    "XS11_xrp1h_MACD_ADX_AROON": {
        "id":             "XS11_xrp1h_MACD_ADX_AROON",
        "symbol":         "XRP/USDT",
        "timeframe":      "1h",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp1h_macd_adx_aroon",
        "score":          32.16,
        "survived_windows": 9,
        "avg_calmar":     5.5064,
        "min_calmar":     1.4486,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  12,        # 12봉 (12시간)
    },

    # XRP 1h SHORT #2 — Score 30.10 | survived=12 (XRP 전체 최고!)
    "XS12_xrp1h_SMA_VWAP_AD": {
        "id":             "XS12_xrp1h_SMA_VWAP_AD",
        "symbol":         "XRP/USDT",
        "timeframe":      "1h",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp1h_sma_vwap_ad",
        "score":          30.10,
        "survived_windows": 12,
        "avg_calmar":     2.6568,
        "min_calmar":     0.5578,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.04,      # TP 4.0%
        "sl_mult":        0.025,     # SL 2.5%
        "base_mdd":       0.025,
        "max_hold_bars":  48,        # 48봉 (48시간)
    },

    # XRP 1h SHORT #3 — Score 30.07 | survived=11, SMA+AD+EMA스택
    "XS13_xrp1h_SMA_AD_EMA_STACK": {
        "id":             "XS13_xrp1h_SMA_AD_EMA_STACK",
        "symbol":         "XRP/USDT",
        "timeframe":      "1h",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp1h_sma_ad_ema_stack",
        "score":          30.07,
        "survived_windows": 11,
        "avg_calmar":     2.7315,
        "min_calmar":     0.7370,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.025,     # SL 2.5%
        "base_mdd":       0.025,
        "max_hold_bars":  24,        # 24봉 (24시간)
    },

    # XRP 1h SHORT #4 — Score 29.98 | survived=7, SMA+AD+ATR확대
    "XS14_xrp1h_SMA_ATR_SIG_AD": {
        "id":             "XS14_xrp1h_SMA_ATR_SIG_AD",
        "symbol":         "XRP/USDT",
        "timeframe":      "1h",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp1h_sma_atr_sig_ad",
        "score":          29.98,
        "survived_windows": 7,
        "avg_calmar":     5.6855,
        "min_calmar":     2.2259,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.02,      # SL 2.0%
        "base_mdd":       0.02,
        "max_hold_bars":  12,        # 12봉 (12시간)
    },

    # XRP 1h SHORT #5 — Score 29.76 | survived=10, MACD+STDDEV+ATR저변동
    "XS15_xrp1h_MACD_STDDEV_ATR_INV": {
        "id":             "XS15_xrp1h_MACD_STDDEV_ATR_INV",
        "symbol":         "XRP/USDT",
        "timeframe":      "1h",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp1h_macd_stddev_atr_inv",
        "score":          29.76,
        "survived_windows": 10,
        "avg_calmar":     5.6045,
        "min_calmar":     0.6770,
        "leverage":       19,
        "max_leverage":   19,
        "tp_type":        "fixed",
        "tp_mult":        0.06,      # TP 6.0%
        "sl_mult":        0.05,      # SL 5.0%
        "base_mdd":       0.05,
        "max_hold_bars":  12,        # 12봉 (12시간)
    },

    # ═══════════════════════════════════════════════════════════════
    # XRPUSDT 4시간봉 LONG 전략 (5개) — XRPUSDT_4h_WFA_Report.docx
    # 1,957개 전략 → 필터 후 → Score 상위 5개씩 선별
    # 선별 기준: surv≥5, avg_calmar≥1.5, min_calmar≥0.4
    # ═══════════════════════════════════════════════════════════════

    # XRP 4h LONG #1 — Score 26.23 | survived=6, ATR확대+켈트너하단+거래량폭증
    "XL16_xrp4h_ATR_SIG_KELTNER_VOLUME": {
        "id":             "XL16_xrp4h_ATR_SIG_KELTNER_VOLUME",
        "symbol":         "XRP/USDT",
        "timeframe":      "4h",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp4h_atr_sig_keltner_volume",
        "score":          26.23,
        "survived_windows": 6,
        "avg_calmar":     4.2129,
        "min_calmar":     1.9575,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.10,      # TP 10.0%
        "sl_mult":        0.005,     # SL 0.5%
        "base_mdd":       0.005,
        "max_hold_bars":  48,        # 48봉 (192시간)
    },

    # XRP 4h LONG #2 — Score 25.71 | survived=7, EMA+OBV+AD 3중
    "XL17_xrp4h_EMA_OBV_AD": {
        "id":             "XL17_xrp4h_EMA_OBV_AD",
        "symbol":         "XRP/USDT",
        "timeframe":      "4h",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp4h_ema_obv_ad",
        "score":          25.71,
        "survived_windows": 7,
        "avg_calmar":     4.5099,
        "min_calmar":     0.4715,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.015,     # SL 1.5%
        "base_mdd":       0.015,
        "max_hold_bars":  48,        # 48봉 (192시간)
    },

    # XRP 4h LONG #3 — Score 23.91 | survived=6, 일목+VWAP+ADX저변동
    "XL18_xrp4h_ICHIMOKU_VWAP_ADX_INV": {
        "id":             "XL18_xrp4h_ICHIMOKU_VWAP_ADX_INV",
        "symbol":         "XRP/USDT",
        "timeframe":      "4h",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp4h_ichimoku_vwap_adx_inv",
        "score":          23.91,
        "survived_windows": 6,
        "avg_calmar":     3.7891,
        "min_calmar":     1.1120,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.015,     # SL 1.5%
        "base_mdd":       0.015,
        "max_hold_bars":  48,        # 48봉 (192시간)
    },

    # XRP 4h LONG #4 — Score 23.73 | survived=6, 일목+VWAP+AD
    "XL19_xrp4h_ICHIMOKU_VWAP_AD": {
        "id":             "XL19_xrp4h_ICHIMOKU_VWAP_AD",
        "symbol":         "XRP/USDT",
        "timeframe":      "4h",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp4h_ichimoku_vwap_ad",
        "score":          23.73,
        "survived_windows": 6,
        "avg_calmar":     3.0822,
        "min_calmar":     1.8055,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.02,      # SL 2.0%
        "base_mdd":       0.02,
        "max_hold_bars":  24,        # 24봉 (96시간)
    },

    # XRP 4h LONG #5 — Score 23.64 | survived=5, EMA+MOM+저거래량
    "XL20_xrp4h_EMA_MOM_VOL_INV": {
        "id":             "XL20_xrp4h_EMA_MOM_VOL_INV",
        "symbol":         "XRP/USDT",
        "timeframe":      "4h",
        "direction":      "long",
        "entry_fn":       "entry_long_xrp4h_ema_mom_vol_inv",
        "score":          23.64,
        "survived_windows": 5,
        "avg_calmar":     4.6431,
        "min_calmar":     1.3364,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.01,      # SL 1.0%
        "base_mdd":       0.01,
        "max_hold_bars":  48,        # 48봉 (192시간)
    },

    # ═══════════════════════════════════════════════════════════════
    # XRPUSDT 4시간봉 SHORT 전략 (5개) — XRPUSDT_4h_WFA_Report.docx
    # SHORT #1 Score 26.85 최고, SHORT #3·#4·#5 동일 성과 (Score 26.24)
    # ═══════════════════════════════════════════════════════════════

    # XRP 4h SHORT #1 — Score 26.85 | survived=6, RSI+ADX저+저거래량
    "XS16_xrp4h_RSI_ADX_INV_VOL_INV": {
        "id":             "XS16_xrp4h_RSI_ADX_INV_VOL_INV",
        "symbol":         "XRP/USDT",
        "timeframe":      "4h",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp4h_rsi_adx_inv_vol_inv",
        "score":          26.85,
        "survived_windows": 6,
        "avg_calmar":     4.3567,
        "min_calmar":     2.1589,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.015,     # SL 1.5%
        "base_mdd":       0.015,
        "max_hold_bars":  48,        # 48봉 (192시간)
    },

    # XRP 4h SHORT #2 — Score 26.35 | survived=5, OBV+Aroon+EMA스택
    "XS17_xrp4h_OBV_AROON_EMA_STACK": {
        "id":             "XS17_xrp4h_OBV_AROON_EMA_STACK",
        "symbol":         "XRP/USDT",
        "timeframe":      "4h",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp4h_obv_aroon_ema_stack",
        "score":          26.35,
        "survived_windows": 5,
        "avg_calmar":     4.8333,
        "min_calmar":     2.5517,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.08,      # TP 8.0%
        "sl_mult":        0.015,     # SL 1.5%
        "base_mdd":       0.015,
        "max_hold_bars":  48,        # 48봉 (192시간)
    },

    # XRP 4h SHORT #3 — Score 26.24 | survived=5, MOM+EMA스택+ATR저
    "XS18_xrp4h_MOM_EMA_STACK_ATR_INV": {
        "id":             "XS18_xrp4h_MOM_EMA_STACK_ATR_INV",
        "symbol":         "XRP/USDT",
        "timeframe":      "4h",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp4h_mom_ema_stack_atr_inv",
        "score":          26.24,
        "survived_windows": 5,
        "avg_calmar":     4.8390,
        "min_calmar":     2.4893,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.015,     # SL 1.5%
        "base_mdd":       0.015,
        "max_hold_bars":  48,        # 48봉 (192시간)
    },

    # XRP 4h SHORT #4 — Score 26.24 | survived=5, MOM+ROC+EMA스택
    "XS19_xrp4h_MOM_ROC_EMA_STACK": {
        "id":             "XS19_xrp4h_MOM_ROC_EMA_STACK",
        "symbol":         "XRP/USDT",
        "timeframe":      "4h",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp4h_mom_roc_ema_stack",
        "score":          26.24,
        "survived_windows": 5,
        "avg_calmar":     4.8390,
        "min_calmar":     2.4893,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.015,     # SL 1.5%
        "base_mdd":       0.015,
        "max_hold_bars":  48,        # 48봉 (192시간)
    },

    # XRP 4h SHORT #5 — Score 26.24 | survived=5, MOM+EMA스택 (최단순)
    "XS20_xrp4h_MOM_EMA_STACK": {
        "id":             "XS20_xrp4h_MOM_EMA_STACK",
        "symbol":         "XRP/USDT",
        "timeframe":      "4h",
        "direction":      "short",
        "entry_fn":       "entry_short_xrp4h_mom_ema_stack",
        "score":          26.24,
        "survived_windows": 5,
        "avg_calmar":     4.8390,
        "min_calmar":     2.4893,
        "leverage":       20,
        "max_leverage":   20,
        "tp_type":        "fixed",
        "tp_mult":        0.12,      # TP 12.0%
        "sl_mult":        0.015,     # SL 1.5%
        "base_mdd":       0.015,
        "max_hold_bars":  48,        # 48봉 (192시간)
    },
}