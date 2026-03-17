"""
strategies/registry.py — 13개 전략 딕셔너리 (v2.9)

TP/SL 변경:
  이전: tp_sl: "H08"  (코드 문자열)
  이후: tp_type / tp_mult / sl_mult  (직접 수치)
  
tp_type: "atr" (ATR 배수) | "fixed" (고정 %)
tp_mult: TP 배수 (ATR형: ATR 배수, fixed형: 소수 예 0.02 = 2%)
sl_mult: SL 배수 (ATR형: ATR 배수, fixed형: 소수)

참조 backtest_metadata.json:
  H01 = fixed  TP 1.0%  / SL 0.5%
  H06 = fixed  TP 3.0%  / SL 3.0%
  H07 = atr    TP ×1.5  / SL ×0.75
  H08 = atr    TP ×2.0  / SL ×1.0
  H09 = atr    TP ×3.0  / SL ×1.0  ← 추가 (백테스트 최고 성능)
  H10 = atr    TP ×4.0  / SL ×1.5
"""

STRATEGY_REGISTRY = {

    # ── XRP 전략 ─────────────────────────────────────────────
    # H07 = ATR ×1.5 TP / ×0.75 SL (2:1 동적)
    "XRP_1h_RSI": {
        "id":         "XRP_1h_RSI",
        "symbol":     "XRP/USDT",
        "timeframe":  "1h",
        "indicators": ["RSI", "AROON", "MFI"],
        "sharpe":     4.74,
        "win_rate":   1.00,
        "leverage":   6,
        "max_leverage": 6,
        "tp_type":    "atr",
        "tp_mult":    1.5,      # ATR × 1.5
        "sl_mult":    0.75,     # ATR × 0.75
        "base_mdd":   0.049,
    },
    "XRP_1h_PSAR": {
        "id":         "XRP_1h_PSAR",
        "symbol":     "XRP/USDT",
        "timeframe":  "1h",
        "indicators": ["PSAR", "MFI", "OBV"],
        "sharpe":     2.12,
        "win_rate":   0.619,
        "leverage":   4,
        "max_leverage": 4,
        "tp_type":    "atr",
        "tp_mult":    1.5,      # ATR × 1.5  (H07)
        "sl_mult":    0.75,     # ATR × 0.75
        "base_mdd":   0.093,
    },

    # ── BTC 15m 전략 ─────────────────────────────────────────
    # H08 = ATR ×2.0 TP / ×1.0 SL (2:1 동적)
    "BTC_15m_ICHI": {
        "id":         "BTC_15m_ICHI",
        "symbol":     "BTC/USDT",
        "timeframe":  "15m",
        "indicators": ["ICHIMOKU", "WILLR", "VWAP"],
        "sharpe":     3.47,
        "win_rate":   0.90,
        "leverage":   7,
        "max_leverage": 7,
        "tp_type":    "atr",
        "tp_mult":    2.0,      # ATR × 2.0  (H08)
        "sl_mult":    1.0,      # ATR × 1.0
        "base_mdd":   0.055,
    },

    # ── BTC 5m 전략 ──────────────────────────────────────────
    # H01 = Fixed TP +1.0% / SL -0.5%
    "BTC_5m_PSAR_ROC": {
        "id":         "BTC_5m_PSAR_ROC",
        "symbol":     "BTC/USDT",
        "timeframe":  "5m",
        "indicators": ["PSAR", "WILLR", "ROC"],
        "sharpe":     1.69,
        "win_rate":   0.725,
        "leverage":   10,
        "max_leverage": 10,
        "tp_type":    "fixed",
        "tp_mult":    0.010,    # +1.0%  (H01)
        "sl_mult":    0.005,    # -0.5%
        "base_mdd":   0.039,
    },
    "BTC_5m_PSAR_MOM": {
        "id":         "BTC_5m_PSAR_MOM",
        "symbol":     "BTC/USDT",
        "timeframe":  "5m",
        "indicators": ["PSAR", "WILLR", "MOM"],
        "sharpe":     1.69,
        "win_rate":   0.725,
        "leverage":   10,
        "max_leverage": 10,
        "tp_type":    "fixed",
        "tp_mult":    0.010,    # +1.0%  (H01)
        "sl_mult":    0.005,    # -0.5%
        "base_mdd":   0.039,
    },
    # H10 = ATR ×4.0 TP / ×1.5 SL
    "BTC_5m_ATR_ROC": {
        "id":         "BTC_5m_ATR_ROC",
        "symbol":     "BTC/USDT",
        "timeframe":  "5m",
        "indicators": ["ATR_SIG", "WILLR", "ROC"],
        "sharpe":     1.49,
        "win_rate":   0.738,
        "leverage":   7,
        "max_leverage": 7,
        "tp_type":    "atr",
        "tp_mult":    4.0,      # ATR × 4.0  (H10)
        "sl_mult":    1.5,      # ATR × 1.5
        "base_mdd":   0.044,
    },
    "BTC_5m_ATR_MOM": {
        "id":         "BTC_5m_ATR_MOM",
        "symbol":     "BTC/USDT",
        "timeframe":  "5m",
        "indicators": ["ATR_SIG", "WILLR", "MOM"],
        "sharpe":     1.49,
        "win_rate":   0.738,
        "leverage":   7,
        "max_leverage": 7,
        "tp_type":    "atr",
        "tp_mult":    4.0,      # ATR × 4.0  (H10)
        "sl_mult":    1.5,      # ATR × 1.5
        "base_mdd":   0.044,
    },
    # H06 = Fixed TP +3.0% / SL -3.0%
    "BTC_5m_PSAR_OBV": {
        "id":         "BTC_5m_PSAR_OBV",
        "symbol":     "BTC/USDT",
        "timeframe":  "5m",
        "indicators": ["PSAR", "WILLR", "OBV"],
        "sharpe":     1.37,
        "win_rate":   0.675,
        "leverage":   3,
        "max_leverage": 3,
        "tp_type":    "fixed",
        "tp_mult":    0.030,    # +3.0%  (H06)
        "sl_mult":    0.030,    # -3.0%
        "base_mdd":   0.084,
    },
    "BTC_5m_PSAR_CMF": {
        "id":         "BTC_5m_PSAR_CMF",
        "symbol":     "BTC/USDT",
        "timeframe":  "5m",
        "indicators": ["PSAR", "WILLR", "CMF"],
        "sharpe":     1.31,
        "win_rate":   0.613,
        "leverage":   3,
        "max_leverage": 3,  # v2.9: 2x→3x (명목 $102 > MIN $100, SL -3%로 파산 불가)
        "tp_type":    "fixed",
        "tp_mult":    0.030,    # +3.0%  (H06)
        "sl_mult":    0.030,    # -3.0%
        "base_mdd":   0.142,
    },
    "BTC_5m_SMA_PSAR": {
        "id":         "BTC_5m_SMA_PSAR",
        "symbol":     "BTC/USDT",
        "timeframe":  "5m",
        "indicators": ["SMA", "PSAR", "WILLR"],
        "sharpe":     1.07,
        "win_rate":   0.663,
        "leverage":   3,
        "max_leverage": 3,  # v2.9: 2x→3x (명목 $102 > MIN $100, SL -3%로 파산 불가)
        "tp_type":    "fixed",
        "tp_mult":    0.030,    # +3.0%  (H06)
        "sl_mult":    0.030,    # -3.0%
        "base_mdd":   0.107,
    },
    "BTC_5m_PSAR_AROON": {
        "id":         "BTC_5m_PSAR_AROON",
        "symbol":     "BTC/USDT",
        "timeframe":  "5m",
        "indicators": ["PSAR", "AROON", "WILLR"],
        "sharpe":     1.07,
        "win_rate":   0.725,
        "leverage":   3,
        "max_leverage": 3,  # v2.9: 2x→3x (명목 $102 > MIN $100, SL -3%로 파산 불가)
        "tp_type":    "fixed",
        "tp_mult":    0.030,    # +3.0%  (H06)
        "sl_mult":    0.030,    # -3.0%
        "base_mdd":   0.138,
    },
    # H07 = ATR ×1.5 TP / ×0.75 SL
    "BTC_5m_PSAR_MFI": {
        "id":         "BTC_5m_PSAR_MFI",
        "symbol":     "BTC/USDT",
        "timeframe":  "5m",
        "indicators": ["PSAR", "WILLR", "MFI"],
        "sharpe":     1.04,
        "win_rate":   0.675,
        "leverage":   3,
        "max_leverage": 3,
        "tp_type":    "atr",
        "tp_mult":    1.5,      # ATR × 1.5  (H07)
        "sl_mult":    0.75,     # ATR × 0.75
        "base_mdd":   0.080,
    },

    # ── ETH 전략 ─────────────────────────────────────────────
    # H08 = ATR ×2.0 TP / ×1.0 SL
    "ETH_5m_EMA_ADX": {
        "id":         "ETH_5m_EMA_ADX",
        "symbol":     "ETH/USDT",
        "timeframe":  "5m",
        "indicators": ["EMA", "ADX", "WILLR"],
        "sharpe":     0.63,
        "win_rate":   0.663,
        "leverage":   2,
        "max_leverage": 2,
        "tp_type":    "atr",
        "tp_mult":    2.0,      # ATR × 2.0  (H08)
        "sl_mult":    1.0,      # ATR × 1.0
        "base_mdd":   0.102,
    },
}
