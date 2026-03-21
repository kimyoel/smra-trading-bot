"""
config.py — 전략 목록, 자본배분, MIN_NOTIONAL, 수수료 설정 (v5.5)

[v5.5] ETHUSDT 5분봉 WFA 전략 10개 추가
  - BTC(5m+15m+1h+4h) 40개 + ETH(5m) 10개 = 총 50개 전략
  - ETH 5m: 742개 전략, 완화기준 102개(13.7%), 황금기준 20개(2.7%)
  - 자본배분: BTC 60%, ETH 30%, 여유 10%
  - 충돌 시 큰 타임프레임 우선 (4h > 1h > 15m > 5m), 동일 TF 내 Score 기반
  - 동일 심볼 내에서만 충돌 해소 (BTC↔ETH 독립 진입 가능)
"""

# ── 50개 전략 전체 목록 (타임프레임 우선 정렬) ──
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
]

# ── 심볼별 최소 명목가치 (거래소 제약 + 여유) ─────────────────
MIN_NOTIONAL = {
    "BTC/USDT": 100.0,
    "ETH/USDT": 20.0,
}

# ── 심볼별 자본 배분 비율 (합계 0.90) ────────────────────────
# [v5.5] BTC 60%, ETH 30%, 여유 10%
CAPITAL_ALLOCATION = {
    "BTC/USDT": 0.60,
    "ETH/USDT": 0.30,
}

# ── 수수료율 ─────────────────────────────────────────────────
TAKER_FEE = {
    "BTC/USDT": 0.0005,   # 0.05%
    "ETH/USDT": 0.0005,   # 0.05%
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
