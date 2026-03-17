"""
config.py — 전략 목록, 자본배분, MIN_NOTIONAL, 수수료 설정
Phase 없음. 13개 전략 항상 전수 감시.
"""

# ── 13개 전략 전체 목록 ──────────────────────────────────────
ALL_STRATEGIES = [
    "XRP_1h_RSI",
    "XRP_1h_PSAR",
    "BTC_15m_ICHI",
    "BTC_5m_PSAR_ROC",
    "BTC_5m_PSAR_MOM",
    "BTC_5m_ATR_ROC",
    "BTC_5m_ATR_MOM",
    "BTC_5m_PSAR_OBV",
    "BTC_5m_PSAR_CMF",
    "BTC_5m_SMA_PSAR",
    "BTC_5m_PSAR_AROON",
    "BTC_5m_PSAR_MFI",
    "ETH_5m_EMA_ADX",
]

# ── 심볼별 최소 명목가치 (거래소 제약 + 여유) ─────────────────
MIN_NOTIONAL = {
    "BTC/USDT": 100.0,
    "ETH/USDT": 20.0,
    "XRP/USDT": 5.0,
}

# ── 심볼별 자본 배분 비율 (합계 1.0) ─────────────────────────
CAPITAL_ALLOCATION = {
    "BTC/USDT": 0.50,
    "ETH/USDT": 0.15,
    "XRP/USDT": 0.35,
}

# ── 수수료율 ─────────────────────────────────────────────────
TAKER_FEE = {
    "BTC/USDT": 0.0005,   # 0.05%
    "ETH/USDT": 0.0005,
    "XRP/USDT": 0.0007,   # 0.07%
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
