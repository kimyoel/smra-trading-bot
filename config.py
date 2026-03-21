"""
config.py — 전략 목록, 자본배분, MIN_NOTIONAL, 수수료 설정 (v6.3.2)

[v6.3.2] 자본배분 방향별 15% 분할
  - CAPITAL_ALLOCATION: 심볼당 30% → 방향별 15% (LONG 15% + SHORT 15% = 30%/심볼)
  - 구조 변경: {"BTC/USDT": 0.30} → {("BTC/USDT","long"): 0.15, ("BTC/USDT","short"): 0.15, ...}
  - 동일 심볼 양방향 동시 진입 시 최대 30% (기존 60% 과다 노출 방지)

[v6.3] 헤지 모드(Hedge Mode) 전면 적용
  - 동일 심볼에 LONG + SHORT 독립 포지션 허용
  - positionSide="LONG"/"SHORT" 파라미터 전 주문에 적용
  - 전략 변경 없음 (120개 유지), 인프라 변경만

[v6.2] XRPUSDT 4시간봉 WFA 전략 10개 추가
  - BTC 40 + ETH 40 + XRP 40 = 총 120개 전략
  - 출처: XRPUSDT_4h_WFA_Report.docx (2026-03-21)
  - XRP 4h: 1,957개 전략 → 필터 후 → Score 상위 5개씩 선별
  - SHORT #3·#4·#5 동일 성과 (Score 26.24) — MOM+EMA_STACK 핵심 드라이버
  - 자본배분: BTC 30%, ETH 30%, XRP 30%, 여유 10%
  - 충돌 해소: 각 심볼 내 큰 타임프레임 우선 (4h > 1h > 15m > 5m)
  - BTC↔ETH↔XRP 독립 진입 가능

[v6.1] XRPUSDT 1시간봉 WFA 전략 10개 추가
[v6.0] XRPUSDT 15분봉 WFA 전략 10개 추가
[v5.9] XRPUSDT 5분봉 WFA 전략 10개 추가
[v5.8] ETHUSDT 4시간봉 WFA 전략 10개 추가
[v5.7] ETHUSDT 1시간봉 WFA 전략 10개 추가
[v5.6] ETHUSDT 15분봉 WFA 전략 10개 추가
[v5.5] ETHUSDT 5분봉 WFA 전략 10개 추가
"""

# ── 120개 전략 전체 목록 (타임프레임 우선 정렬) ──
ALL_STRATEGIES = [
    # === BTC 4h 전략 ===
    "S16_4h_WILLR_ATR_SIG_MFI",      # Score 29.53, 4h SHORT 1위
    "S17_4h_WILLR_BB_CCI",           # Score 24.03, 4h SHORT 2위
    "L16_4h_VOLUME_VWAP_STDDEV",     # Score 23.02, 4h LONG 1위
    "L17_4h_AROON_VOLUME_ADX_INV",   # Score 23.01, 4h LONG 2위
    "S18_4h_WILLR_BB",               # Score 22.54, 4h SHORT 3위
    "S19_4h_WILLR_BB_ATR_INV",       # Score 22.54, 4h SHORT 4위
    "L18_4h_ATR_SIG_VOLUME_VWAP",    # Score 22.48, 4h LONG 3위
    "S20_4h_ADX_CMF_VOL_INV",        # Score 22.34, 4h SHORT 5위
    "L19_4h_VOLUME_EMA_STACK_ATR_INV", # Score 21.90, 4h LONG 4위
    "L20_4h_VOLUME_EMA_STACK",       # Score 21.90, 4h LONG 5위
    # === BTC 1h 전략 ===
    "S11_1h_ADX_RSI_WILLR",          # Score 23.27, 1h SHORT 1위
    "L11_1h_SMA_STDDEV_EMA_STACK",   # Score 22.99, 1h LONG 1위
    "S12_1h_ADX_RSI_VOL_INV",        # Score 22.44, 1h SHORT 2위
    "L12_1h_EMA_STDDEV_ADX_INV",     # Score 22.40, 1h LONG 2위
    "L13_1h_PSAR_AROON_MOM",         # Score 22.25, 1h LONG 3위
    "L14_1h_PSAR_AROON_VWAP",        # Score 22.25, 1h LONG 4위
    "L15_1h_PSAR_AROON_ROC",         # Score 22.25, 1h LONG 5위
    "S13_1h_MACD_STDDEV_VOL_INV",    # Score 22.18, 1h SHORT 3위
    "S14_1h_BB_MFI_ADX_INV",         # Score 22.11, 1h SHORT 4위
    "S15_1h_CCI_EMA_STACK",          # Score 20.80, 1h SHORT 5위
    # === BTC 15m 전략 ===
    "S1_WILLR_BB_OBV",               # Score 20.36, 15m SHORT 1위
    "L1_WILLR_BB_EMA_STACK",         # Score 19.21, 15m LONG 1위
    "S2_SMA_ICHIMOKU_STDDEV",        # Score 19.36, 15m SHORT 2위
    "S3_OBV_KELTNER_ADX_INV",        # Score 18.98, 15m SHORT 3위
    "L2_ADX_WILLR_EMA_STACK",        # Score 18.73, 15m LONG 2위
    "S4_BB_EMA_STACK",               # Score 18.73, 15m SHORT 4위
    "S5_BB_EMA_STACK_ATR_INV",       # Score 18.73, 15m SHORT 5위
    "L3_AROON_DONCHIAN_VOL_INV",     # Score 15.97, 15m LONG 3위
    "L4_EMA_MACD_PSAR",              # Score 15.64, 15m LONG 4위
    "L5_EMA_PSAR_MOM",               # Score 15.53, 15m LONG 5위
    # === BTC 5m 전략 ===
    "L6_5m_BB_EMA_STACK_VOL_INV",    # Score 14.28, 5m LONG 1위
    "S6_5m_RSI_WILLR_EMA_STACK",     # Score 13.26, 5m SHORT 1위
    "L7_5m_MACD_ICHIMOKU_STDDEV",    # Score 12.54, 5m LONG 2위
    "S7_5m_EMA_ICHIMOKU_VOLUME",     # Score 12.41, 5m SHORT 2위
    "L8_5m_STOCH_CCI_EMA_STACK",     # Score 12.07, 5m LONG 3위
    "S8_5m_RSI_EMA_STACK",           # Score 12.05, 5m SHORT 3위
    "S9_5m_RSI_EMA_STACK_ATR_INV",   # Score 12.05, 5m SHORT 4위
    "S10_5m_PSAR_MFI_STDDEV",        # Score 11.50, 5m SHORT 5위
    "L9_5m_CCI_VWAP_AD",             # Score 11.17, 5m LONG 4위
    "L10_5m_RSI_CCI_EMA_STACK",      # Score 11.04, 5m LONG 5위
    # === ETH 4h 전략 ===
    "EL16_eth4h_VOLUME_STDDEV_ADX_INV",   # Score 29.73, ETH 4h LONG 1위
    "EL17_eth4h_ICHIMOKU_OBV_VWAP",       # Score 29.12, ETH 4h LONG 2위
    "ES16_eth4h_ICHIMOKU_VWAP",           # Score 29.09, ETH 4h SHORT 1위 (surv=11 최고)
    "ES17_eth4h_ICHIMOKU_VWAP_ATR_INV",   # Score 29.09, ETH 4h SHORT 2위 (surv=11 최고)
    "EL18_eth4h_MACD_VWAP_VOL_INV",       # Score 29.03, ETH 4h LONG 3위
    "EL19_eth4h_ICHIMOKU_VWAP",           # Score 28.13, ETH 4h LONG 4위
    "EL20_eth4h_ICHIMOKU_VWAP_ATR_INV",   # Score 28.13, ETH 4h LONG 5위
    "ES18_eth4h_ICHIMOKU_OBV_VWAP",       # Score 27.14, ETH 4h SHORT 3위
    "ES19_eth4h_PSAR_ADX_INV",            # Score 26.84, ETH 4h SHORT 4위
    "ES20_eth4h_PSAR_ADX_INV_ATR_INV",    # Score 26.84, ETH 4h SHORT 5위
    # === ETH 1h 전략 ===
    "ES11_eth1h_PSAR_ATR_SIG_AROON",      # Score 24.90, ETH 1h SHORT 1위 (전시리즈 최고)
    "ES12_eth1h_BB_CMF_VOLUME",           # Score 24.58, ETH 1h SHORT 2위
    "ES13_eth1h_PSAR_STDDEV_ATR_INV",     # Score 24.11, ETH 1h SHORT 3위
    "ES14_eth1h_WILLR_ADX_INV_VOL_INV",   # Score 23.95, ETH 1h SHORT 4위
    "ES15_eth1h_PSAR_VOLUME_STDDEV",      # Score 23.84, ETH 1h SHORT 5위
    "EL11_eth1h_SMA_VOLUME_ADX_INV",      # Score 22.77, ETH 1h LONG 1위
    "EL12_eth1h_MACD_ADX_ROC",            # Score 22.62, ETH 1h LONG 2위
    "EL13_eth1h_SMA_STDDEV_ADX_INV",      # Score 22.58, ETH 1h LONG 3위
    "EL14_eth1h_SMA_ATR_SIG_EMA_STACK",   # Score 22.14, ETH 1h LONG 4위
    "EL15_eth1h_OBV_VWAP_ATR_INV",        # Score 21.73, ETH 1h LONG 5위
    # === ETH 15m 전략 ===
    "EL6_eth15m_CCI_MOM_VOL_INV",       # Score 20.41, ETH 15m LONG 1위
    "EL7_eth15m_SMA_MACD_ATR_INV",      # Score 19.72, ETH 15m LONG 2위
    "EL8_eth15m_ADX_BB_EMA_STACK",      # Score 19.26, ETH 15m LONG 3위
    "ES6_eth15m_MFI_MOM_VWAP",          # Score 19.24, ETH 15m SHORT 1위
    "EL9_eth15m_WILLR_CMF_AROON",       # Score 19.24, ETH 15m LONG 4위
    "EL10_eth15m_SMA_ICHIMOKU_CMF",     # Score 19.12, ETH 15m LONG 5위
    "ES7_eth15m_EMA_ATR_SIG_EMA_STACK", # Score 19.12, ETH 15m SHORT 2위
    "ES8_eth15m_SMA_ICHIMOKU_EMA_STACK",# Score 18.71, ETH 15m SHORT 3위
    "ES9_eth15m_ADX_ICHIMOKU_EMA_STACK",# Score 18.29, ETH 15m SHORT 4위
    "ES10_eth15m_CMF_MFI_VWAP",         # Score 17.88, ETH 15m SHORT 5위
    # === ETH 5m 전략 ===
    "EL1_eth5m_WILLR_ICHIMOKU_AROON",  # Score 22.84, ETH 5m LONG 1위
    "ES1_eth5m_STOCH_OBV_MFI",         # Score 19.89, ETH 5m SHORT 1위
    "EL2_eth5m_ADX_STOCH_EMA_STACK",   # Score 19.17, ETH 5m LONG 2위
    "EL3_eth5m_SMA_ADX_PSAR",          # Score 17.60, ETH 5m LONG 3위
    "EL4_eth5m_BB_ATR_SIG_EMA_STACK",  # Score 17.24, ETH 5m LONG 4위
    "ES2_eth5m_SMA_MACD_STDDEV",       # Score 17.23, ETH 5m SHORT 2위
    "EL5_eth5m_RSI_EMA_STACK",         # Score 16.62, ETH 5m LONG 5위
    "ES3_eth5m_ADX_RSI_EMA_STACK",     # Score 16.34, ETH 5m SHORT 3위
    "ES4_eth5m_AROON_CCI_EMA_STACK",   # Score 16.16, ETH 5m SHORT 4위
    "ES5_eth5m_ADX_PSAR_ICHIMOKU",     # Score 15.38, ETH 5m SHORT 5위
    # === XRP 5m 전략 ===
    "XL1_xrp5m_OBV_CCI_MFI",           # Score 23.22, XRP 5m LONG 1위
    "XS1_xrp5m_SMA_CCI_ADX_INV",       # Score 21.13, XRP 5m SHORT 1위
    "XL2_xrp5m_STOCH_OBV_MFI",         # Score 21.97, XRP 5m LONG 2위
    "XS2_xrp5m_RSI_WILLR_EMA_STACK",   # Score 20.94, XRP 5m SHORT 2위
    "XL3_xrp5m_SMA_EMA_PSAR",          # Score 20.49, XRP 5m LONG 3위
    "XL4_xrp5m_ADX_ICHIMOKU_VOLUME",   # Score 20.49, XRP 5m LONG 4위
    "XS3_xrp5m_SMA_EMA_VOLUME",        # Score 20.27, XRP 5m SHORT 3위
    "XL5_xrp5m_SMA_DONCHIAN_STDDEV",   # Score 20.29, XRP 5m LONG 5위
    "XS4_xrp5m_OBV_CCI_MOM",           # Score 19.85, XRP 5m SHORT 4위
    "XS5_xrp5m_OBV_CCI_ROC",           # Score 19.85, XRP 5m SHORT 5위
    # === XRP 15m 전략 ===
    "XL6_xrp15m_STOCH_AROON",           # Score 27.36, XRP 15m LONG 1위 (surv=9)
    "XL7_xrp15m_STOCH_WILLR_AROON",     # Score 27.36, XRP 15m LONG 2위 (surv=9)
    "XL8_xrp15m_STOCH_AROON_ATR_INV",   # Score 27.36, XRP 15m LONG 3위 (surv=9)
    "XS6_xrp15m_SMA_EMA_ATR_SIG",       # Score 24.55, XRP 15m SHORT 1위
    "XL9_xrp15m_MACD_AROON_DONCHIAN",   # Score 24.19, XRP 15m LONG 4위
    "XS7_xrp15m_SMA_EMA_STDDEV",        # Score 24.20, XRP 15m SHORT 2위
    "XL10_xrp15m_EMA_ICHIMOKU_VOLUME",  # Score 23.96, XRP 15m LONG 5위
    "XS8_xrp15m_STOCH_CMF_ADX_INV",     # Score 23.79, XRP 15m SHORT 3위
    "XS9_xrp15m_RSI_BB_MFI",            # Score 23.71, XRP 15m SHORT 4위
    "XS10_xrp15m_BB_KELTNER_MFI",       # Score 23.47, XRP 15m SHORT 5위
    # === XRP 1h 전략 ===
    "XS11_xrp1h_MACD_ADX_AROON",        # Score 32.16, XRP 1h SHORT 1위 (surv=9)
    "XS12_xrp1h_SMA_VWAP_AD",           # Score 30.10, XRP 1h SHORT 2위 (surv=12, XRP 최고)
    "XS13_xrp1h_SMA_AD_EMA_STACK",      # Score 30.07, XRP 1h SHORT 3위 (surv=11)
    "XS14_xrp1h_SMA_ATR_SIG_AD",        # Score 29.98, XRP 1h SHORT 4위
    "XS15_xrp1h_MACD_STDDEV_ATR_INV",   # Score 29.76, XRP 1h SHORT 5위 (surv=10)
    "XL11_xrp1h_PSAR_EMA_STACK_VOL_INV",# Score 26.97, XRP 1h LONG 1위
    "XL12_xrp1h_STOCH_WILLR_ATR_SIG",   # Score 26.29, XRP 1h LONG 2위
    "XL13_xrp1h_STOCH_ATR_SIG",         # Score 26.29, XRP 1h LONG 3위
    "XL14_xrp1h_PSAR_CMF_AROON",        # Score 26.26, XRP 1h LONG 4위
    "XL15_xrp1h_SMA_OBV_ATR_SIG",       # Score 26.18, XRP 1h LONG 5위 (surv=8)
    # === XRP 4h 전략 ===
    "XS16_xrp4h_RSI_ADX_INV_VOL_INV",   # Score 26.85, XRP 4h SHORT 1위 (최고 스코어)
    "XS17_xrp4h_OBV_AROON_EMA_STACK",   # Score 26.35, XRP 4h SHORT 2위
    "XS18_xrp4h_MOM_EMA_STACK_ATR_INV", # Score 26.24, XRP 4h SHORT 3위
    "XS19_xrp4h_MOM_ROC_EMA_STACK",     # Score 26.24, XRP 4h SHORT 4위
    "XS20_xrp4h_MOM_EMA_STACK",         # Score 26.24, XRP 4h SHORT 5위
    "XL16_xrp4h_ATR_SIG_KELTNER_VOLUME",# Score 26.23, XRP 4h LONG 1위 (RR 20.0)
    "XL17_xrp4h_EMA_OBV_AD",            # Score 25.71, XRP 4h LONG 2위 (surv=7)
    "XL18_xrp4h_ICHIMOKU_VWAP_ADX_INV", # Score 23.91, XRP 4h LONG 3위
    "XL19_xrp4h_ICHIMOKU_VWAP_AD",      # Score 23.73, XRP 4h LONG 4위
    "XL20_xrp4h_EMA_MOM_VOL_INV",       # Score 23.64, XRP 4h LONG 5위
]

# ── 심볼별 최소 명목가치 (거래소 제약 + 여유) ─────────────────
MIN_NOTIONAL = {
    "BTC/USDT": 100.0,
    "ETH/USDT": 20.0,
    "XRP/USDT": 5.0,
}

# ── 방향별 자본 배분 비율 (합계 0.90) ────────────────────────
# [v6.3.2] 방향별 15% 분할: LONG 15% + SHORT 15% = 심볼당 30%, 여유 10%
#   기존: 심볼당 30% → 양방향 동시 진입 시 60% 과다 노출
#   수정: 방향별 15% → 양방향 동시 진입 시 30% (의도대로)
CAPITAL_ALLOCATION = {
    ("BTC/USDT", "long"):  0.15,
    ("BTC/USDT", "short"): 0.15,
    ("ETH/USDT", "long"):  0.15,
    ("ETH/USDT", "short"): 0.15,
    ("XRP/USDT", "long"):  0.15,
    ("XRP/USDT", "short"): 0.15,
}

# ── 수수료율 ─────────────────────────────────────────────────
TAKER_FEE = {
    "BTC/USDT": 0.0005,   # 0.05%
    "ETH/USDT": 0.0005,   # 0.05%
    "XRP/USDT": 0.0005,   # 0.05%
}

# ── Circuit Breaker 파라미터 ──────────────────────────────────
CB_MAX_API_ERRORS     = 5       # 연속 API 오류 임계값
CB_FLASH_CRASH_PCT    = -0.15   # 15분 내 가격 변화율 임계값
CB_FLASH_PAUSE_SEC    = 1800    # 플래시 크래시 후 대기 시간 (30분)
CB_SPREAD_MAX         = 0.002   # 스프레드 임계값 (0.2%)
CB_FUNDING_MAX        = 0.003   # 펀딩비 임계값 (0.3%/8h)
CB_MDD_MULTIPLIER     = 2.0     # 백테스트 MDD 대비 실거래 MDD 배수

# ── 루프 간격 ────────────────────────────────────────────────
LOOP_INTERVAL_SEC = 60
