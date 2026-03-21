"""
config.py — 전략 목록, 자본배분, MIN_NOTIONAL, 수수료 설정 (v5.0)

[v5.0] WFA OOS 백테스트 보고서 기반 전면 교체
  - 기존 17개 다심볼(BTC/ETH/XRP) 전략 → BTCUSDT 15m 전용 10개 전략
  - LONG 5개 + SHORT 5개 (WFA 황금기준 통과 상위 전략)
  - 자본배분: BTC/USDT 100% (단일 심볼)
  - 충돌 해소: Score 기반 (survived_windows×2 + min_calmar×3 + ln(1+avg_calmar))
  - 데이터 출처: BTCUSDT_15m_WFA_Report.docx (2026-03-21)
"""

# ── 10개 전략 전체 목록 (WFA Score 순위별 정렬) ─────────────
# 충돌 시 이 리스트 순서(= Score 순위)대로 우선권 부여
ALL_STRATEGIES = [
    # === SHORT 전략 (Score 상위) ===
    "S1_WILLR_BB_OBV",              # Score 20.36, SHORT 1위, 전체 1위
    # === LONG 전략 ===
    "L1_WILLR_BB_EMA_STACK",        # Score 19.21, LONG 1위, 전체 2위
    # === SHORT 전략 ===
    "S2_SMA_ICHIMOKU_STDDEV",       # Score 19.36, SHORT 2위, 전체 3위
    "S3_OBV_KELTNER_ADX_INV",       # Score 18.98, SHORT 3위, 전체 4위
    # === LONG 전략 ===
    "L2_ADX_WILLR_EMA_STACK",       # Score 18.73, LONG 2위, 전체 5위
    # === SHORT 전략 ===
    "S4_BB_EMA_STACK",              # Score 18.73, SHORT 4위, 전체 6위
    "S5_BB_EMA_STACK_ATR_INV",      # Score 18.73, SHORT 5위, 전체 7위
    # === LONG 전략 ===
    "L3_AROON_DONCHIAN_VOL_INV",    # Score 15.97, LONG 3위, 전체 8위
    "L4_EMA_MACD_PSAR",             # Score 15.64, LONG 4위, 전체 9위
    "L5_EMA_PSAR_MOM",              # Score 15.53, LONG 5위, 전체 10위
]

# ── 심볼별 최소 명목가치 (거래소 제약 + 여유) ─────────────────
MIN_NOTIONAL = {
    "BTC/USDT": 100.0,
}

# ── 심볼별 자본 배분 비율 (합계 0.90) ────────────────────────
# [v5.0] BTC/USDT 단일 심볼 90%, 10% 여유 버퍼
CAPITAL_ALLOCATION = {
    "BTC/USDT": 0.90,
}

# ── 수수료율 ─────────────────────────────────────────────────
TAKER_FEE = {
    "BTC/USDT": 0.0005,   # 0.05%
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
