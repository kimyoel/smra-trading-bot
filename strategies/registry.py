"""
strategies/registry.py — WFA OOS 백테스트 검증 전략 레지스트리 (v5.5)

[v5.5] ETHUSDT 5분봉 WFA 전략 10개 추가
  - 출처: ETHUSDT_5m_WFA_Report.docx (2026-03-21)
  - LONG 5개 + SHORT 5개 (ETH 5분봉 완화기준: surv≥4, avg≥1.5, min≥0.4)
  - 742개 전략 중 102개(13.7%) 완화기준 통과, 20개(2.7%) 황금기준 통과
  - 레버리지: 이론 = 1/(SL%+0.5%), 권장 = 이론×80% (상한 20x, SL<1% 슬리피지 추가 감안)
  - 총 50개 전략: BTC(5m×10+15m×10+1h×10+4h×10) + ETH(5m×10)

[v5.4] BTCUSDT 4시간봉 WFA 전략 10개 추가
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
        "leverage":       27,       # recommended: floor(0.80/(0.025+0.004))=27
        "max_leverage":   34,       # theoretical: floor(1.00/(0.025+0.004))=34
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
        "leverage":       14,       # recommended: floor(0.80/(0.05+0.004))=14
        "max_leverage":   18,       # theoretical: floor(1.00/(0.05+0.004))=18
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
        "leverage":       12,       # recommended: floor(0.80/(0.06+0.004))=12
        "max_leverage":   15,       # theoretical: floor(1.00/(0.06+0.004))=15
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
        "leverage":       33,       # recommended: floor(0.80/(0.02+0.004))=33
        "max_leverage":   41,       # theoretical: floor(1.00/(0.02+0.004))=41
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
        "leverage":       88,       # recommended: floor(0.80/(0.005+0.004))=88
        "max_leverage":   111,      # theoretical: floor(1.00/(0.005+0.004))=111
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
        "leverage":       27,       # recommended: floor(0.80/(0.025+0.004))=27
        "max_leverage":   34,       # theoretical: floor(1.00/(0.025+0.004))=34
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
        "leverage":       18,       # recommended: floor(0.80/(0.04+0.004))=18
        "max_leverage":   22,       # theoretical: floor(1.00/(0.04+0.004))=22
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
        "leverage":       18,       # recommended: floor(0.80/(0.04+0.004))=18
        "max_leverage":   22,       # theoretical: floor(1.00/(0.04+0.004))=22
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
        "leverage":       23,       # recommended: floor(0.80/(0.03+0.004))=23
        "max_leverage":   29,       # theoretical: floor(1.00/(0.03+0.004))=29
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
        "leverage":       23,       # recommended: floor(0.80/(0.03+0.004))=23
        "max_leverage":   29,       # theoretical: floor(1.00/(0.03+0.004))=29
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
}
