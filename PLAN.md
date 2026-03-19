# PLAN.md — 백테스트 검증 지표 교체 작업 계획서

> 작성일: 2026-03-19  
> 상태: ✅ **작업 완료** (2026-03-19)

---

## 1. 목표

GitHub 레포 `kimyoel/smra-trading-bot`의 매매 로직에서 기존 미검증 지표/전략을  
**472개 백테스트 결과에서 B등급(OOS ≥ 0.70) 이상 검증된 지표/전략**으로 전면 교체한다.

추가로 다음 기능을 구현한다:
- ✅ **진입 타이밍 수정**: 조건 전환(False→True) 봉 확정 후 다음 봉 시가 1회만 진입
- ✅ **전략별 최적 TP/SL 매칭**: 백테스트 검증된 개별 TP/SL을 각 전략에 적용
- ✅ **Sharpe 기반 심볼 충돌 해소**: 동일 심볼 동시 신호 시 Sharpe 최고 전략만 실행

---

## 2. 현재 상태 (AS-IS) 분석

### 2-1. 전략 구성
| 항목 | 현재 값 |
|------|---------|
| 전략 수 | 13개 |
| 타임프레임 | 5m: 9개 (69%), 15m: 1개, 1h: 2개 |
| 코인 배분 | BTC: 11개, XRP: 2개, **ETH: 0개** |
| 방향 | 모두 BOTH (롱/숏 구분 없음) |
| 주요 지표 | PSAR(9회), WILLR(7회), ICHIMOKU, RSI, EMA, SMA |
| TP/SL | ATR기반 + fixed 혼재 |

### 2-2. 백테스트 기준 현재 지표 성과
| 지표 | 평균 OOS | B+등급 진입 | 비고 |
|------|----------|-----------|------|
| PSAR | ~0.46 | 1회 | D등급 수준 |
| ICHIMOKU | 0.4605 | 0회 | 최악 |
| RSI | ~0.47 | 0회 | TOP50 등장 0회 |
| WILLR | ~0.46 | 0회 | RSI 중복 |
| SMA | 0.4914 | 0회 | - |
| EMA | ~0.46 | 2회 | XRP 15m만 |
| MACD | 0.4598 | 0회 | 수익률 -46.44% |

### 2-3. 진입 타이밍 버그
```
현재 동작:
  봉1: ADX=26 (>25) → "long" 반환 → 진입
  봉2: ADX=27 (>25) → "long" 반환 → 또 진입 시도 (심볼 중복 차단으로 막히지만 로직 오류)
  봉3: ADX=28 (>25) → "long" 반환 → 또 진입 시도
  ...ADX<25 될 때까지 매봉 신호 발생

올바른 동작 (백테스트 기준):
  봉1: ADX=23 (<25) → False
  봉2: ADX=26 (>25) → "long" → ← 조건 완성 봉 (이 봉 마감 확정 후)
  봉3: 시가에 진입    → ← 실제 진입 시점 (봇 루프 실행 시점)
  봉4: ADX=27 (>25) → 이미 True 유지 → 신호 없음 (전환 아님)
```

---

## 3. 교체 목표 (TO-BE)

### 3-1. 전략 구성
| 항목 | 교체 후 |
|------|---------|
| 전략 수 | 17개 (S등급 5, A등급 12) |
| 타임프레임 | **1h: 11개**, 15m: 3개, 4h: 3개, **5m: 0개** |
| 코인 배분 | BTC: 7개, ETH: 4개, XRP: 6개 |
| 방향 | LONG: 9개, SHORT: 8개 (명시적 분리) |
| 주요 지표 | OBV, AD, VWAP, CMF, ADX, MOM, STDDEV |
| TP/SL | **모두 fixed** (전략별 최적 조합) |

### 3-2. 17개 전략 목록 (전략별 최적 TP/SL)
| # | ID | 코인 | TF | 방향 | 지표 | OOS | 등급 | Sharpe | TP/SL |
|---|-----|------|-----|------|------|-----|------|--------|-------|
| 1 | XRP_1h_SHORT_AD | XRP | 1h | SHORT | AD | 0.9837 | S | 34.39 | 5.0/3.0 |
| 2 | ETH_1h_LONG_OBV_VWAP | ETH | 1h | LONG | OBV,VWAP | 0.9442 | S | 29.60 | 5.0/3.0 |
| 3 | XRP_1h_SHORT_VWAP_AD | XRP | 1h | SHORT | VWAP,AD | 0.9430 | S | 29.17 | 5.0/3.0 |
| 4 | BTC_1h_LONG_ADX | BTC | 1h | LONG | ADX | 0.9110 | S | 32.63 | **5.0/1.5** |
| 5 | BTC_15m_LONG_STDDEV_AD_ADX | BTC | 15m | LONG | STDDEV,AD,ADX | 0.9017 | S | 36.04 | 5.0/3.0 |
| 6 | BTC_1h_LONG_MOM | BTC | 1h | LONG | MOM | 0.8871 | A | 29.84 | **5.0/2.0** |
| 7 | BTC_1h_LONG_ROC | BTC | 1h | LONG | ROC | 0.8871 | A | 29.84 | **5.0/2.0** |
| 8 | BTC_15m_LONG_AROON_AD_ATR_SIG | BTC | 15m | LONG | AROON,AD,ATR_SIG | 0.8847 | A | 34.20 | 5.0/3.0 |
| 9 | BTC_1h_SHORT_OBV_MOM | BTC | 1h | SHORT | OBV,MOM | 0.8674 | A | 28.48 | 5.0/3.0 |
| 10 | ETH_1h_SHORT_CMF | ETH | 1h | SHORT | CMF | 0.8668 | A | 26.76 | **3.0/2.0** |
| 11 | BTC_1h_SHORT_OBV_VWAP | BTC | 1h | SHORT | OBV,VWAP | 0.8649 | A | 27.06 | 5.0/3.0 |
| 12 | ETH_1h_LONG_OBV_VWAP_32 | ETH | 1h | LONG | OBV,VWAP | 0.8418 | A | 26.60 | **3.0/2.0** |
| 13 | ETH_4h_LONG_ADX | ETH | 4h | LONG | ADX | 0.8322 | A | 16.93 | **5.0/2.0** |
| 14 | XRP_4h_LONG_MOM_VWAP | XRP | 4h | LONG | MOM,VWAP | 0.8283 | A | 16.40 | 5.0/3.0 |
| 15 | XRP_15m_SHORT_CMF_CCI | XRP | 15m | SHORT | CMF,CCI | 0.8206 | A | 17.85 | 5.0/3.0 |
| 16 | XRP_4h_SHORT_MOM | XRP | 4h | SHORT | MOM | 0.8141 | A | 17.07 | 5.0/3.0 |
| 17 | XRP_1h_SHORT_AD_2 | XRP | 1h | SHORT | AD | 0.8100 | A | 30.00 | **5.0/2.0** |

> **TP/SL 차이점**: 전략마다 백테스트 최적 조합이 다름  
> - 대부분: TP 5.0% / SL 3.0% (10개)  
> - BTC_1h_LONG_ADX: SL **1.5%** (낮은 MDD -1.68%)  
> - BTC_1h_LONG_MOM/ROC, ETH_4h_LONG_ADX, XRP_1h_SHORT_AD_2: SL **2.0%** (4개)  
> - ETH_1h_SHORT_CMF, ETH_1h_LONG_OBV_VWAP_32: TP **3.0%** / SL **2.0%** (2개)

### 3-3. 진입 타이밍 수정
```
수정 로직 (signal_generator.py):
  1. df_full = fetch_ohlcv(100봉)
  2. df_prev = df_full.iloc[:-1]     # 직전 봉까지
  3. df_curr = df_full               # 현재(마지막) 봉까지
  4. result_prev = indicator(df_prev) # 직전 봉 기준 신호
  5. result_curr = indicator(df_curr) # 현재 봉 기준 신호
  6. 크로스 판단:
     - result_prev == False AND result_curr == "long"  → 신호 발생 ✅
     - result_prev == "long" AND result_curr == "long"  → 유지 중 → 무시 ❌
     - result_prev == "short" AND result_curr == "long" → 방향 전환 → 신호 발생 ✅
```

### 3-4. Sharpe 기반 심볼 충돌 해소
```
시나리오: XRP/USDT에 3개 전략 동시 신호 발생
  XRP_1h_SHORT_AD       Sharpe 34.39  ← 승자 (실행)
  XRP_1h_SHORT_AD_2     Sharpe 30.00  ← 제외 (SKIP-SHARPE-CONFLICT)
  XRP_15m_SHORT_CMF_CCI Sharpe 17.85  ← 제외 (SKIP-SHARPE-CONFLICT)

이유: 1심볼 1포지션 규칙 → Sharpe 높은 전략이 위험 대비 수익 최대
구현 위치: core/signal_arbiter.py v2.5
```

---

## 4. 수정 대상 파일 및 작업 단계

### Phase 1: 문서 작성
| 단계 | 작업 | 상태 |
|------|------|------|
| 1-1 | PLAN.md 작성 (이 문서) | ✅ |
| 1-2 | TASK.md 작성 (코딩 이유 설명) | ✅ |

### Phase 2: 코드 수정 — 지표/전략 교체
| 단계 | 파일 | 수정 내용 | 상태 |
|------|------|----------|------|
| 2-1 | `config.py` | ALL_STRATEGIES 17개로 교체, CAPITAL_ALLOCATION 조정 | ✅ |
| 2-2 | `strategies/registry.py` | 백테스트 보고서 기준 17개 전략 재정의 (전략별 TP/SL 포함) | ✅ |
| 2-3 | `core/signal_generator.py` | ① MIN_BARS 정리 ② **크로스 감지 로직** ③ direction 필터 | ✅ |
| 2-4 | `main.py` | TF_HOURS에 4h 추가, 버전 v2.13 | ✅ |

### Phase 3: 코드 수정 — TP/SL 매칭 + Sharpe 충돌 해소
| 단계 | 파일 | 수정 내용 | 상태 |
|------|------|----------|------|
| 3-1 | `core/signal_arbiter.py` | v2.5: 전략별 TP/SL 로그 명시 + **심볼별 Sharpe 중복 제거** | ✅ |
| 3-2 | `main.py` | v2.13: arbiter v2.5 연계 설명 추가, 버전 업데이트 | ✅ |

### Phase 4: 검증 및 배포
| 단계 | 작업 | 상태 |
|------|------|------|
| 4-1 | 문법 테스트 (6개 파일 AST 파싱) | ✅ |
| 4-2 | Config-Registry 일관성 검증 | ✅ |
| 4-3 | TP/SL 계산 정확성 단위 테스트 | ✅ |
| 4-4 | Sharpe 충돌 해소 단위 테스트 | ✅ |
| 4-5 | Order Manager TP/SL 흐름 검증 | ✅ |
| 4-6 | Git 커밋 + PR 업데이트 | ✅ |
| 4-7 | PLAN.md 완료 표시 업데이트 | ✅ |

---

## 5. 자본 배분 계획

| 코인 | AS-IS | TO-BE | 이유 |
|------|-------|-------|------|
| BTC/USDT | 50% | **40%** | 시가총액 1위, 유동성 최대 |
| ETH/USDT | 15% | **30%** ↑ | S등급 전략 보유, 유동성 양호 |
| XRP/USDT | 35% | **30%** | S등급 1위 전략 보유 |

---

## 6. TP/SL 매칭 흐름 (end-to-end)

```
registry.py (전략별 TP/SL 정의)
  예: BTC_1h_LONG_ADX → tp_mult=0.050, sl_mult=0.015
  예: ETH_1h_SHORT_CMF → tp_mult=0.030, sl_mult=0.020
      ↓
signal_arbiter.py → calc_tp_sl(entry, atr, strategy, direction)
  → tp_mult = strategy.get("tp_mult")  ← 전략 고유값 사용
  → sl_mult = strategy.get("sl_mult")  ← 전략 고유값 사용
  → tp, sl = entry 기반 가격 계산
      ↓
  Sharpe 기반 심볼 충돌 해소 (심볼당 1개만 반환)
      ↓
main.py → execute_order(sig)
  → sig["tp"] / sig["sl"] 전달
      ↓
order_manager.py → execute_order(sig)
  → 실제 체결가 확인 후 strat.get("tp_mult")/strat.get("sl_mult")로 재계산
  → Binance Algo Order API로 TP/SL 등록
```

---

## 7. 위험 관리 참고

- ⚠ OOS 윈도우 1개 전략 (BTC 1h S_ADX): 과최적화 가능성 → 모니터링
- ⚠ BTC 15m 높은 Sharpe (36~37): 비정상적 → 포워드 테스트 권장
- ⚠ 5m 전략 전면 제거: 최소 TF가 15m → CANDLE_TF_SEC=300은 유지 (15m은 5m 배수)
- ⚠ 모든 전략 fixed TP/SL: update_atr_tp_sl()은 ATR 전략 없으므로 자동 스킵 (안전)
- ⚠ 동일 심볼 LONG/SHORT 동시 신호 시: Sharpe 기반 1개만 실행 (방향 전환 시 포지션 충돌 방지)
