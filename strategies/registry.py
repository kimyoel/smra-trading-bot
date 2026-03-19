"""
strategies/registry.py — 백테스트 검증 전략 레지스트리 (v4.2)

[v4.2] backtest_report_final.docx 기반 MAX HOLD 매칭
  - 각 전략별 max_hold_bars 필드 추가
  - 백테스트 보고서의 MAX HOLD 컬럼에서 추출
  - 16개 전략: 48봉, 1개 전략(XRP_4h_SHORT_MOM): 16봉
  - main.py의 고정 24봉 강제청산 → 전략별 max_hold_bars 동적 적용
  - XRP_1h_SHORT_AD_2: 보고서에 TP5/SL2 없음 → S_AD(TP5/SL3) max_hold=48 적용

[v4.1] leverage_v3_final.csv 기반 레버리지 매칭
  - 기존 고정 레버리지(3~5) → CSV rec_lev 값으로 교체
  - Kelly Criterion + 등급/신뢰도 기반 레버리지 산출
  - S등급 scale=1.0, A등급 scale=0.75
  - max_leverage = leverage (CSV 권장값이 상한)
  - XRP_1h_SHORT_AD_2: CSV에 TP5/SL2 없음 → S_AD(TP5/SL3) rec_lev=4 적용 (보수적)

[v4.0] 472개 전략 백테스트 결과 기반 전면 교체
  - 기존 13개 → 17개 (S등급 5, A등급 12)
  - 5m 전략 전면 제거 (평균 OOS 0.4859, 수익률 -38.10%)
  - BOTH 방향 제거 → LONG/SHORT 명시적 분리
  - TP/SL: 모두 fixed (백테스트 최적 조합)
  - 모든 전략에 direction 필드 추가
  - 변경 근거: TASK.md 참조
  - 데이터 출처: backtest_report.docx, leverage_v3_final.csv

TP/SL 타입:
  tp_type: "fixed" (고정 %)
  tp_mult: TP 비율 (소수, 예: 0.05 = 5%)
  sl_mult: SL 비율 (소수, 예: 0.03 = 3%)

등급 기준 (OOS = Out-of-Sample 점수):
  S등급: OOS >= 0.90  (5개)
  A등급: OOS 0.80~0.89 (12개)

레버리지 출처: leverage_v3_final.csv (rec_lev 컬럼)
  - Kelly Criterion 기반 full_kelly_lev에 등급/신뢰도 스케일 적용
  - S등급: scale=1.0 x trust (0.89~0.93)
  - A등급: scale=0.75 x trust (0.88~0.92)

MAX HOLD 출처: backtest_report_final.docx (MAX HOLD 컬럼)
  - 백테스트시 포지션 최대 보유 봉수
  - 강제청산 기준: max_hold_bars x timeframe_hours
  - 16개 전략: 48봉, 1개 전략(XRP_4h_SHORT_MOM): 16봉
"""

STRATEGY_REGISTRY = {

    # ═══════════════════════════════════════════════════════════
    # Tier 1: S등급 (OOS >= 0.90) — 5개
    # ═══════════════════════════════════════════════════════════

    # #1 — 전체 최고 OOS (0.9837) + 최고 수익률 (943.59%)
    # 보고서: XRP 1h SHORT S_AD | Sharpe 34.39 | MDD -3.18%
    # 레버리지: rec_lev=4, S_scale=1.0_trust=0.89
    "XRP_1h_SHORT_AD": {
        "id":         "XRP_1h_SHORT_AD",
        "symbol":     "XRP/USDT",
        "timeframe":  "1h",
        "direction":  "short",
        "indicators": ["AD"],
        "sharpe":     34.39,
        "win_rate":   0.521,
        "leverage":   4,
        "max_leverage": 4,
        "tp_type":    "fixed",
        "tp_mult":    0.050,     # TP 5.0%
        "sl_mult":    0.030,     # SL 3.0%
        "base_mdd":   0.0318,
        "max_hold_bars": 48,   # MAX HOLD 48봉 (1h x 48 = 48h)
    },

    # #2 — ETH S등급 최고, 수익률 769.25%
    # 보고서: ETH 1h LONG 2_OBV_VWAP | Sharpe 29.60 | MDD -3.18%
    # 레버리지: rec_lev=4, S_scale=1.0_trust=0.89
    "ETH_1h_LONG_OBV_VWAP": {
        "id":         "ETH_1h_LONG_OBV_VWAP",
        "symbol":     "ETH/USDT",
        "timeframe":  "1h",
        "direction":  "long",
        "indicators": ["OBV", "VWAP"],
        "sharpe":     29.60,
        "win_rate":   0.546,
        "leverage":   4,
        "max_leverage": 4,
        "tp_type":    "fixed",
        "tp_mult":    0.050,     # TP 5.0%
        "sl_mult":    0.030,     # SL 3.0%
        "base_mdd":   0.0318,
        "max_hold_bars": 48,   # MAX HOLD 48봉 (1h x 48 = 48h)
    },

    # #3 — XRP S등급, 수익률 770.37%
    # 보고서: XRP 1h SHORT 2_VWAP_AD | Sharpe 29.17 | MDD -3.18%
    # 레버리지: rec_lev=4, S_scale=1.0_trust=0.89
    "XRP_1h_SHORT_VWAP_AD": {
        "id":         "XRP_1h_SHORT_VWAP_AD",
        "symbol":     "XRP/USDT",
        "timeframe":  "1h",
        "direction":  "short",
        "indicators": ["VWAP", "AD"],
        "sharpe":     29.17,
        "win_rate":   0.530,
        "leverage":   4,
        "max_leverage": 4,
        "tp_type":    "fixed",
        "tp_mult":    0.050,     # TP 5.0%
        "sl_mult":    0.030,     # SL 3.0%
        "base_mdd":   0.0318,
        "max_hold_bars": 48,   # MAX HOLD 48봉 (1h x 48 = 48h)
    },

    # #4 — BTC S등급, 수익률 430.08%, 최저 MDD -1.68%
    # 보고서: BTC 1h LONG S_ADX | Sharpe 32.63 | MDD -1.68%
    # 레버리지: rec_lev=9, S_scale=1.0_trust=0.93
    "BTC_1h_LONG_ADX": {
        "id":         "BTC_1h_LONG_ADX",
        "symbol":     "BTC/USDT",
        "timeframe":  "1h",
        "direction":  "long",
        "indicators": ["ADX"],
        "sharpe":     32.63,
        "win_rate":   0.404,
        "leverage":   9,
        "max_leverage": 9,
        "tp_type":    "fixed",
        "tp_mult":    0.050,     # TP 5.0%
        "sl_mult":    0.015,     # SL 1.5%
        "base_mdd":   0.0168,
        "max_hold_bars": 48,   # MAX HOLD 48봉 (1h x 48 = 48h)
    },

    # #5 — BTC 15m S등급, 수익률 300.87%, 최고 Sharpe 36.04
    # 보고서: BTC 15m LONG 3_STDDEV_AD_ADX | Sharpe 36.04 | MDD -3.18%
    # 레버리지: rec_lev=4, S_scale=1.0_trust=0.89
    "BTC_15m_LONG_STDDEV_AD_ADX": {
        "id":         "BTC_15m_LONG_STDDEV_AD_ADX",
        "symbol":     "BTC/USDT",
        "timeframe":  "15m",
        "direction":  "long",
        "indicators": ["STDDEV", "AD", "ADX"],
        "sharpe":     36.04,
        "win_rate":   0.482,
        "leverage":   4,
        "max_leverage": 4,
        "tp_type":    "fixed",
        "tp_mult":    0.050,     # TP 5.0%
        "sl_mult":    0.030,     # SL 3.0%
        "base_mdd":   0.0318,
        "max_hold_bars": 48,   # MAX HOLD 48봉 (15m x 48 = 12h)
    },

    # ═══════════════════════════════════════════════════════════
    # Tier 2: A등급 상위 (OOS 0.85+) — 7개
    # ═══════════════════════════════════════════════════════════

    # #6 — BTC A등급, MOM 단독, 수익률 329.19%
    # 보고서: BTC 1h LONG S_MOM | Sharpe 29.84 | MDD -2.18%
    # 레버리지: rec_lev=7, S_scale=1.0_trust=0.89
    "BTC_1h_LONG_MOM": {
        "id":         "BTC_1h_LONG_MOM",
        "symbol":     "BTC/USDT",
        "timeframe":  "1h",
        "direction":  "long",
        "indicators": ["MOM"],
        "sharpe":     29.84,
        "win_rate":   0.422,
        "leverage":   7,
        "max_leverage": 7,
        "tp_type":    "fixed",
        "tp_mult":    0.050,     # TP 5.0%
        "sl_mult":    0.020,     # SL 2.0%
        "base_mdd":   0.0218,
        "max_hold_bars": 48,   # MAX HOLD 48봉 (1h x 48 = 48h)
    },

    # #7 — BTC A등급, ROC 단독 (MOM과 동일 성과, 비율 버전)
    # 보고서: BTC 1h LONG S_ROC | OOS 0.8871 | Sharpe 29.84
    # 레버리지: rec_lev=7, S_scale=1.0_trust=0.89
    "BTC_1h_LONG_ROC": {
        "id":         "BTC_1h_LONG_ROC",
        "symbol":     "BTC/USDT",
        "timeframe":  "1h",
        "direction":  "long",
        "indicators": ["ROC"],
        "sharpe":     29.84,
        "win_rate":   0.422,
        "leverage":   7,
        "max_leverage": 7,
        "tp_type":    "fixed",
        "tp_mult":    0.050,     # TP 5.0%
        "sl_mult":    0.020,     # SL 2.0%
        "base_mdd":   0.0218,
        "max_hold_bars": 48,   # MAX HOLD 48봉 (1h x 48 = 48h)
    },

    # #8 — BTC 15m A등급, 3지표 조합, 수익률 220.92%
    # 보고서: BTC 15m LONG 3_AROON_AD_ATR_SIG | Sharpe 34.20 | MDD -3.18%
    # 레버리지: rec_lev=4, S_scale=1.0_trust=0.89
    "BTC_15m_LONG_AROON_AD_ATR_SIG": {
        "id":         "BTC_15m_LONG_AROON_AD_ATR_SIG",
        "symbol":     "BTC/USDT",
        "timeframe":  "15m",
        "direction":  "long",
        "indicators": ["AROON", "AD", "ATR_SIG"],
        "sharpe":     34.20,
        "win_rate":   0.472,
        "leverage":   4,
        "max_leverage": 4,
        "tp_type":    "fixed",
        "tp_mult":    0.050,     # TP 5.0%
        "sl_mult":    0.030,     # SL 3.0%
        "base_mdd":   0.0318,
        "max_hold_bars": 48,   # MAX HOLD 48봉 (15m x 48 = 12h)
    },

    # #9 — BTC SHORT A등급, 수익률 231.60%
    # 보고서: BTC 1h SHORT 2_OBV_MOM | Sharpe 28.48 | MDD -3.18%
    # 레버리지: rec_lev=4, S_scale=1.0_trust=0.89
    "BTC_1h_SHORT_OBV_MOM": {
        "id":         "BTC_1h_SHORT_OBV_MOM",
        "symbol":     "BTC/USDT",
        "timeframe":  "1h",
        "direction":  "short",
        "indicators": ["OBV", "MOM"],
        "sharpe":     28.48,
        "win_rate":   0.498,
        "leverage":   4,
        "max_leverage": 4,
        "tp_type":    "fixed",
        "tp_mult":    0.050,     # TP 5.0%
        "sl_mult":    0.030,     # SL 3.0%
        "base_mdd":   0.0318,
        "max_hold_bars": 48,   # MAX HOLD 48봉 (1h x 48 = 48h)
    },

    # #10 — ETH SHORT A등급, CMF 단독, 수익률 254.37%
    # 보고서: ETH 1h SHORT S_CMF | Sharpe 26.76 | MDD -2.18%
    # 레버리지: rec_lev=7, S_scale=1.0_trust=0.89
    "ETH_1h_SHORT_CMF": {
        "id":         "ETH_1h_SHORT_CMF",
        "symbol":     "ETH/USDT",
        "timeframe":  "1h",
        "direction":  "short",
        "indicators": ["CMF"],
        "sharpe":     26.76,
        "win_rate":   0.511,
        "leverage":   7,
        "max_leverage": 7,
        "tp_type":    "fixed",
        "tp_mult":    0.030,     # TP 3.0%
        "sl_mult":    0.020,     # SL 2.0%
        "base_mdd":   0.0218,
        "max_hold_bars": 48,   # MAX HOLD 48봉 (1h x 48 = 48h)
    },

    # #11 — BTC SHORT A등급, 수익률 247.46%
    # 보고서: BTC 1h SHORT 2_OBV_VWAP | Sharpe 27.06 | MDD -3.18%
    # 레버리지: rec_lev=4, S_scale=1.0_trust=0.93
    "BTC_1h_SHORT_OBV_VWAP": {
        "id":         "BTC_1h_SHORT_OBV_VWAP",
        "symbol":     "BTC/USDT",
        "timeframe":  "1h",
        "direction":  "short",
        "indicators": ["OBV", "VWAP"],
        "sharpe":     27.06,
        "win_rate":   0.506,
        "leverage":   4,
        "max_leverage": 4,
        "tp_type":    "fixed",
        "tp_mult":    0.050,     # TP 5.0%
        "sl_mult":    0.030,     # SL 3.0%
        "base_mdd":   0.0318,
        "max_hold_bars": 48,   # MAX HOLD 48봉 (1h x 48 = 48h)
    },

    # ═══════════════════════════════════════════════════════════
    # Tier 3: A등급 하위 (OOS 0.80~0.85) — 5개
    # ═══════════════════════════════════════════════════════════

    # #12 — ETH LONG A등급, 같은 지표 다른 TP/SL (3.0/2.0)
    # 보고서: ETH 1h LONG 2_OBV_VWAP (TP3/SL2) | OOS 0.8418 | Sharpe 26.60
    # 레버리지: rec_lev=6, S_scale=1.0_trust=0.89
    "ETH_1h_LONG_OBV_VWAP_32": {
        "id":         "ETH_1h_LONG_OBV_VWAP_32",
        "symbol":     "ETH/USDT",
        "timeframe":  "1h",
        "direction":  "long",
        "indicators": ["OBV", "VWAP"],
        "sharpe":     26.60,
        "win_rate":   0.456,
        "leverage":   6,
        "max_leverage": 6,
        "tp_type":    "fixed",
        "tp_mult":    0.030,     # TP 3.0%
        "sl_mult":    0.020,     # SL 2.0%
        "base_mdd":   0.0218,
        "max_hold_bars": 48,   # MAX HOLD 48봉 (1h x 48 = 48h)
    },

    # #13 — ETH 4h LONG A등급, ADX 단독, 수익률 237.64%
    # 보고서: ETH 4h LONG S_ADX | OOS 0.8322 | Sharpe 16.93 | MDD -2.18%
    # 레버리지: rec_lev=5, A_scale=0.75_trust=0.88
    "ETH_4h_LONG_ADX": {
        "id":         "ETH_4h_LONG_ADX",
        "symbol":     "ETH/USDT",
        "timeframe":  "4h",
        "direction":  "long",
        "indicators": ["ADX"],
        "sharpe":     16.93,
        "win_rate":   0.393,
        "leverage":   5,
        "max_leverage": 5,
        "tp_type":    "fixed",
        "tp_mult":    0.050,     # TP 5.0%
        "sl_mult":    0.020,     # SL 2.0%
        "base_mdd":   0.0218,
        "max_hold_bars": 48,   # MAX HOLD 48봉 (4h x 48 = 192h)
    },

    # #14 — XRP 4h LONG A등급, 수익률 236.43%
    # 보고서: XRP 4h LONG 2_MOM_VWAP | OOS 0.8283 | Sharpe 16.40 | MDD -3.18%
    # 레버리지: rec_lev=4, A_scale=0.75_trust=0.88
    "XRP_4h_LONG_MOM_VWAP": {
        "id":         "XRP_4h_LONG_MOM_VWAP",
        "symbol":     "XRP/USDT",
        "timeframe":  "4h",
        "direction":  "long",
        "indicators": ["MOM", "VWAP"],
        "sharpe":     16.40,
        "win_rate":   0.524,
        "leverage":   4,
        "max_leverage": 4,
        "tp_type":    "fixed",
        "tp_mult":    0.050,     # TP 5.0%
        "sl_mult":    0.030,     # SL 3.0%
        "base_mdd":   0.0318,
        "max_hold_bars": 48,   # MAX HOLD 48봉 (4h x 48 = 192h)
    },

    # #15 — XRP 15m SHORT A등급, 수익률 144.82%
    # 보고서: XRP 15m SHORT 2_CMF_CCI | OOS 0.8206 | Sharpe 17.85 | MDD -3.18%
    # 레버리지: rec_lev=4, A_scale=0.75_trust=0.92
    "XRP_15m_SHORT_CMF_CCI": {
        "id":         "XRP_15m_SHORT_CMF_CCI",
        "symbol":     "XRP/USDT",
        "timeframe":  "15m",
        "direction":  "short",
        "indicators": ["CMF", "CCI"],
        "sharpe":     17.85,
        "win_rate":   0.577,
        "leverage":   4,
        "max_leverage": 4,
        "tp_type":    "fixed",
        "tp_mult":    0.050,     # TP 5.0%
        "sl_mult":    0.030,     # SL 3.0%
        "base_mdd":   0.0318,
        "max_hold_bars": 48,   # MAX HOLD 48봉 (15m x 48 = 12h)
    },

    # #16 — XRP 4h SHORT A등급, MOM 단독, 수익률 116.00%
    # 보고서: XRP 4h SHORT S_MOM | OOS 0.8141 | Sharpe 17.07 | MDD -3.18%
    # 레버리지: rec_lev=3, A_scale=0.75_trust=0.88
    "XRP_4h_SHORT_MOM": {
        "id":         "XRP_4h_SHORT_MOM",
        "symbol":     "XRP/USDT",
        "timeframe":  "4h",
        "direction":  "short",
        "indicators": ["MOM"],
        "sharpe":     17.07,
        "win_rate":   0.474,
        "leverage":   3,
        "max_leverage": 3,
        "tp_type":    "fixed",
        "tp_mult":    0.050,     # TP 5.0%
        "sl_mult":    0.030,     # SL 3.0%
        "base_mdd":   0.0318,
        "max_hold_bars": 16,   # MAX HOLD 16봉 (4h x 16 = 64h)
    },

    # #17 — XRP 1h SHORT A등급, AD 단독 (다른 TP/SL: 5.0/2.0)
    # 보고서: XRP 1h SHORT S_AD (TP5/SL2) | 수익률 426.48%
    # 레버리지: rec_lev=4, CSV에 TP5/SL2 없음 -> S_AD(TP5/SL3) rec_lev=4 적용
    "XRP_1h_SHORT_AD_2": {
        "id":         "XRP_1h_SHORT_AD_2",
        "symbol":     "XRP/USDT",
        "timeframe":  "1h",
        "direction":  "short",
        "indicators": ["AD"],
        "sharpe":     30.00,
        "win_rate":   0.510,
        "leverage":   4,
        "max_leverage": 4,
        "tp_type":    "fixed",
        "tp_mult":    0.050,     # TP 5.0%
        "sl_mult":    0.020,     # SL 2.0%
        "base_mdd":   0.0218,
        "max_hold_bars": 48,   # MAX HOLD 48봉 (1h x 48 = 48h) — 보고서에 TP5/SL2 없음, S_AD(TP5/SL3) 값 적용
    },
}
