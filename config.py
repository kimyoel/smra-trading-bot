"""
config.py — 전략 목록, 자본배분, MIN_NOTIONAL, 수수료 설정 (v4.0)

[v4.0] 백테스트 검증 전략으로 전면 교체
  - 기존 13개 → 17개 (S등급 5, A등급 12)
  - 5m 전략 전면 제거 (평균 OOS 0.4859, 수익률 -38.10%)
  - ETH 전략 0→6개 추가 → 자본배분 재조정
  - 변경 근거: TASK.md 참조
"""

# ── 17개 전략 전체 목록 (S/A등급만) ────────────────────────
ALL_STRATEGIES = [
    # S등급 (OOS >= 0.90) — 5개
    "XRP_1h_SHORT_AD",              # OOS 0.9837, 수익률 943.59%
    "ETH_1h_LONG_OBV_VWAP",        # OOS 0.9442, 수익률 769.25%
    "XRP_1h_SHORT_VWAP_AD",        # OOS 0.9430, 수익률 770.37%
    "BTC_1h_LONG_ADX",             # OOS 0.9110, 수익률 430.08%
    "BTC_15m_LONG_STDDEV_AD_ADX",  # OOS 0.9017, 수익률 300.87%
    # A등급 (OOS 0.80~0.89) — 12개
    "BTC_1h_LONG_MOM",             # OOS 0.8871, 수익률 329.19%
    "BTC_1h_LONG_ROC",             # OOS 0.8871, 수익률 329.19%
    "BTC_15m_LONG_AROON_AD_ATR_SIG",  # OOS 0.8847, 수익률 220.92%
    "BTC_1h_SHORT_OBV_MOM",        # OOS 0.8674, 수익률 231.60%
    "ETH_1h_SHORT_CMF",            # OOS 0.8668, 수익률 254.37%
    "BTC_1h_SHORT_OBV_VWAP",       # OOS 0.8649, 수익률 247.46%
    "ETH_1h_LONG_OBV_VWAP_32",     # OOS 0.8418, 수익률  74.34%
    "ETH_4h_LONG_ADX",             # OOS 0.8322, 수익률 237.64%
    "XRP_4h_LONG_MOM_VWAP",        # OOS 0.8283, 수익률 236.43%
    "XRP_15m_SHORT_CMF_CCI",       # OOS 0.8206, 수익률 144.82%
    "XRP_4h_SHORT_MOM",            # OOS 0.8141, 수익률 116.00%
    "XRP_1h_SHORT_AD_2",           # OOS 0.8100, 수익률 426.48%
]

# ── 심볼별 최소 명목가치 (거래소 제약 + 여유) ─────────────────
MIN_NOTIONAL = {
    "BTC/USDT": 100.0,
    "ETH/USDT": 20.0,
    "XRP/USDT": 5.0,
}

# ── 심볼별 자본 배분 비율 (합계 1.0) ─────────────────────────
# [v4.1] 총 자산 기준 고정 배분 (전략 수 무관)
#   BTC 40% — 시가총액 1위, 유동성 최대
#   ETH 30% — S등급 전략 보유, 유동성 양호
#   XRP 30% — S등급 1위(OOS 0.9837) 전략 보유
CAPITAL_ALLOCATION = {
    "BTC/USDT": 0.40,
    "ETH/USDT": 0.30,
    "XRP/USDT": 0.30,
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
