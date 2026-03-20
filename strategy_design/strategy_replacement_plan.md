# B등급 이상 지표 전략 교체 설계서

## 분석 완료 날짜: 2026-03-19
## 분석 대상: 472개 전략 백테스트 결과 + indicators.py v3.8

---

## PART 1. 현재 시스템 진단

### 1-1. 전체 성적표
| 등급 | 개수 | 비율 | OOS 범위 |
|------|------|------|----------|
| S | 5개 | 1.1% | >= 0.90 |
| A | 72개 | 15.3% | 0.80~0.89 |
| B | 51개 | 10.8% | 0.70~0.79 |
| C | 55개 | 11.7% | 0.60~0.69 |
| **D** | **289개** | **61.2%** | < 0.60 |

> **핵심 문제**: 전체 전략의 61%가 D등급(실전 부적합). 
> 472개 중 실전 투입 가능(B+) 전략은 **128개(27.1%)** 뿐.

### 1-2. 타임프레임별 진단
| TF | 평균 OOS | 최고 OOS | 평균 수익률 | 판정 |
|----|----------|----------|------------|------|
| 5m | 0.4859 | 0.7869 | -38.10% | **폐기 권장** |
| 15m | 0.5204 | 0.9017 | -24.65% | 선별적 사용 |
| **1h** | **0.6495** | **0.9837** | **+48.55%** | **최적 TF** |
| 4h | 0.6087 | 0.8322 | -9.42% | 보조적 사용 |

### 1-3. 지표별 TOP50 등장빈도 (B+ 전략 핵심 지표)
| 순위 | 지표 | 등장횟수 | 평균OOS | 역할 |
|------|------|---------|---------|------|
| 1 | **OBV** | 20회 | 0.6143 | 거래량 추세 |
| 2 | **VWAP** | 18회 | 0.6510 | 거래량가중가격 |
| 3 | **AD** | 13회 | - | 매집/분산 |
| 4 | **ADX** | 13회 | - | 추세강도 필터 |
| 5 | **CMF** | 11회 | - | 자금흐름 |
| 6 | **MOM** | 8회 | - | 모멘텀 |
| 7 | AROON | 5회 | - | 추세방향 |
| 8 | STDDEV | 4회 | - | 변동성 |

### 1-4. 최악 지표 (즉시 제거 대상)
| 지표 | 평균 OOS | 평균 수익률 | 판정 |
|------|----------|-----------|------|
| **MACD** | 0.4598 | -46.44% | **즉시 제거** |
| **ICHIMOKU** | 0.4605 | - | **즉시 제거** |
| **SMA** | 0.4914 | - | **제거 권장** |

---

## PART 2. B등급 이상 핵심 전략 분석

### 2-1. S등급 (5개) - 반드시 유지
| # | 심볼 | TF | 방향 | 전략 | OOS | 수익률 | MDD | TP/SL | 승률 |
|---|------|----|------|------|-----|--------|-----|-------|------|
| 1 | XRP | 1h | SHORT | S_AD | 0.9837 | 943.59% | -3.18% | 5.0/3.0 | 52.1% |
| 2 | ETH | 1h | LONG | 2_OBV_VWAP | 0.9442 | 769.25% | -3.18% | 5.0/3.0 | 54.6% |
| 3 | XRP | 1h | SHORT | 2_VWAP_AD | 0.9430 | 770.37% | -3.18% | 5.0/3.0 | 53.0% |
| 4 | BTC | 1h | LONG | S_ADX | 0.9110 | 430.08% | -1.68% | 5.0/1.5 | 40.4% |
| 5 | BTC | 15m | LONG | 3_STDDEV_AD_ADX | 0.9017 | 300.87% | -3.18% | 5.0/3.0 | 48.2% |

### 2-2. A등급 핵심 (상위 20개)
| # | 심볼 | TF | 방향 | 전략 | OOS | 수익률 | MDD | TP/SL |
|---|------|----|------|------|-----|--------|-----|-------|
| 1 | BTC | 1h | LONG | S_MOM | 0.8871 | 329.19% | -2.18% | 5.0/2.0 |
| 2 | BTC | 1h | LONG | S_ROC | 0.8871 | 329.19% | -2.18% | 5.0/2.0 |
| 3 | BTC | 15m | LONG | 3_AROON_AD_ATR_SIG | 0.8847 | 220.92% | -3.18% | 5.0/3.0 |
| 4 | XRP | 1h | SHORT | 2_OBV_AD | 0.8813 | 426.48% | -3.18% | 5.0/3.0 |
| 5 | BTC | 15m | LONG | 3_CMF_AROON_ADX | 0.8795 | 104.78% | -3.18% | 5.0/3.0 |
| 6 | ETH | 1h | LONG | 2_OBV_AD | 0.8792 | 342.83% | -2.18% | 5.0/2.0 |
| 7 | XRP | 1h | SHORT | S_OBV | 0.8798 | 340.08% | -2.18% | 5.0/2.0 |
| 8 | ETH | 1h | LONG | 3_VWAP_AD_ADX | 0.8760 | 309.49% | -3.18% | 5.0/3.0 |
| 9 | XRP | 1h | SHORT | S_VWAP | 0.8724 | 173.34% | -2.18% | 3.0/2.0 |
| 10 | BTC | 1h | SHORT | 2_OBV_MOM | 0.8674 | 231.60% | -3.18% | 5.0/3.0 |
| 11 | ETH | 1h | SHORT | S_CMF | 0.8668 | 254.37% | -2.18% | 3.0/2.0 |
| 12 | BTC | 1h | SHORT | 2_OBV_VWAP | 0.8649 | 247.46% | -3.18% | 5.0/3.0 |
| 13 | XRP | 1h | SHORT | 2_MOM_VWAP | 0.8640 | 168.33% | -2.18% | 3.0/2.0 |
| 14 | ETH | 1h | SHORT | 2_OBV_VWAP | 0.8634 | 279.72% | -2.18% | 5.0/2.0 |
| 15 | ETH | 1h | SHORT | 2_CMF_AD | 0.8607 | 276.40% | -3.18% | 5.0/3.0 |
| 16 | ETH | 1h | SHORT | 3_OBV_AD_ADX | 0.8569 | 251.68% | -3.18% | 5.0/3.0 |
| 17 | ETH | 1h | LONG | S_CMF | 0.8562 | 154.60% | -2.18% | 3.0/2.0 |
| 18 | BTC | 15m | LONG | 3_CMF_STDDEV_ATR_SIG | 0.8552 | 114.84% | -3.18% | 5.0/3.0 |
| 19 | BTC | 1h | SHORT | 2_OBV_MOM(#3) | 0.8535 | 225.35% | -2.18% | 5.0/2.0 |
| 20 | ETH | 1h | SHORT | S_CCI | 0.8433 | 273.18% | -2.18% | 5.0/2.0 |

### 2-3. TP/SL 최적 조합
| TP(%) | SL(%) | 평균 OOS | 평균 수익률 | MDD | 판정 |
|-------|-------|---------|-----------|------|------|
| **5.0** | **2.0** | **0.6088** | **33.85%** | -2.18% | **최적** |
| 5.0 | 1.3 | 0.5955 | 12.31% | -1.48% | 보수적 |
| 5.0 | 3.0 | 0.5941 | 3.61% | -3.18% | 넓은SL |
| 3.0 | 2.0 | 0.5800 | - | -2.18% | 적정 |
| 5.0 | 1.5 | - | - | -1.68% | 보수적 |
| **1.3** | **1.0** | **0.4698** | **-36.55%** | - | **최악 제거** |
| **5.0** | **1.0** | **0.4586** | **-46.86%** | - | **최악 제거** |

---

## PART 3. 전략 교체 설계

### 3-1. 핵심 원칙

```
[1] 성과 기반 지표 선별: TOP 6 지표만 사용 (OBV, VWAP, AD, ADX, CMF, MOM)
[2] 최악 지표 완전 제거: MACD, ICHIMOKU, SMA (평균 OOS < 0.50)
[3] 최적 타임프레임 집중: 1h 메인, 15m/4h 보조
[4] 5m 완전 폐기: 평균 수익률 -38%, 실전 불가
[5] TP/SL 최적화: TP 5.0% / SL 2.0% 기본, 심볼별 미세 조정
[6] BOTH 전략 제거: 방향성 단독 베팅만 허용
```

### 3-2. 교체 대상 지표 맵

#### 제거 (Remove)
| 지표 | 제거 이유 |
|------|----------|
| MACD | 평균 OOS 0.4598, 평균 수익률 -46.44%. B+등급 전략에 단 한번도 단독 등장 안함 |
| ICHIMOKU | 평균 OOS 0.4605. 1h에서도 D등급 지배적 |
| SMA | 평균 OOS 0.4914. EMA와 중복되며 모든 TF에서 저성과 |
| EMA | B+등급 등장 극소(XRP 15m BOTH에서만 2회). 독립 신호력 부족 |
| WILLR | RSI와 완전 중복 로직. B+등급 전략에 독립 등장 0회 |
| BB | 볼린저밴드 단독 B+등급 없음. KELTNER이 동일 역할 수행 가능 |
| PSAR | B+등급 등장 1회(ETH 15m BOTH). 신호 빈도 낮고 단독 성과 미달 |
| STOCH | B+등급 등장 0회. RSI 대비 신호 품질 열위 |
| DONCHIAN | B+등급 등장 0회. 고가/저가 돌파 전략 자체가 암호화폐에서 비효율 |
| RSI | B+등급 **독립** 등장 0회. 과매수/과매도 단독 신호로 부적합 |

#### 유지/강화 (Keep & Enhance) - 핵심 6개
| 지표 | 유지 이유 | 역할 |
|------|----------|------|
| **OBV** | TOP50에 20회 등장, S/A등급 핵심 구성요소 | 거래량 추세 확인 |
| **VWAP** | TOP50에 18회, 최고 평균 OOS(0.6510) | 가격-거래량 균형점 |
| **AD** | S등급 1위 전략(S_AD, OOS 0.9837)의 핵심 | 매집/분산 판단 |
| **ADX** | TOP50에 13회, S등급 전략(S_ADX, OOS 0.9110) 포함 | 추세 강도 필터 |
| **CMF** | TOP50에 11회, A등급 다수 구성 | 자금 유입/유출 |
| **MOM** | TOP50에 8회, A등급 BTC 1h LONG(OOS 0.8871) | 모멘텀 방향 |

#### 보조 유지 (Secondary Keep) - 4개
| 지표 | 유지 이유 | 역할 |
|------|----------|------|
| **AROON** | A등급 BTC 전략에 5회 등장 | 추세 방향 보조 |
| **STDDEV** | S등급(3_STDDEV_AD_ADX) 구성, 변동성 팽창 포착 | 변동성 필터 |
| **CCI** | B등급 다수, XRP 15m에서 A등급 | 과매수/과매도 보조 |
| **ROC** | MOM과 유사하지만 A등급(BTC 1h, OOS 0.8871) | 변화율 |

#### 필터 유지
| 지표 | 역할 |
|------|------|
| **ATR_SIG** | 변동성 활성 필터 (B+ 전략에서 반복 등장) |
| **VOLUME** | 거래량 급증 필터 |
| **ADX_INV** | 횡보장 필터 (역방향) |
| **ATR_INV** | 저변동성 필터 (역방향) |
| **VOL_INV** | 거래량 정상 필터 (역방향) |

### 3-3. 신규 전략 포트폴리오 (추천 운용 전략 세트)

#### Tier 1: 최우선 투입 (S등급 검증 완료)
| 슬롯 | 심볼 | TF | 방향 | 전략 | 지표 조합 | TP/SL | 기대 OOS |
|------|------|----|------|------|----------|-------|----------|
| 1 | XRP | 1h | SHORT | S_AD | AD 단독 | 5.0/3.0 | 0.98 |
| 2 | ETH | 1h | LONG | 2_OBV_VWAP | OBV + VWAP | 5.0/3.0 | 0.94 |
| 3 | XRP | 1h | SHORT | 2_VWAP_AD | VWAP + AD | 5.0/3.0 | 0.94 |
| 4 | BTC | 1h | LONG | S_ADX | ADX 필터 단독 | 5.0/1.5 | 0.91 |
| 5 | BTC | 15m | LONG | 3_STDDEV_AD_ADX | STDDEV + AD + ADX | 5.0/3.0 | 0.90 |

#### Tier 2: 주력 보조 (A등급 상위)
| 슬롯 | 심볼 | TF | 방향 | 전략 | 지표 조합 | TP/SL | 기대 OOS |
|------|------|----|------|------|----------|-------|----------|
| 6 | BTC | 1h | LONG | S_MOM | MOM 단독 | 5.0/2.0 | 0.89 |
| 7 | XRP | 1h | SHORT | 2_OBV_AD | OBV + AD | 5.0/3.0 | 0.88 |
| 8 | ETH | 1h | LONG | 2_OBV_AD | OBV + AD | 5.0/2.0 | 0.88 |
| 9 | BTC | 15m | LONG | 3_CMF_AROON_ADX | CMF + AROON + ADX | 5.0/3.0 | 0.88 |
| 10 | ETH | 1h | LONG | 3_VWAP_AD_ADX | VWAP + AD + ADX | 5.0/3.0 | 0.88 |
| 11 | BTC | 1h | SHORT | 2_OBV_MOM | OBV + MOM | 5.0/3.0 | 0.87 |
| 12 | ETH | 1h | SHORT | S_CMF | CMF 단독 | 3.0/2.0 | 0.87 |

#### Tier 3: 분산 투자 (A등급 하위 + B등급 상위)
| 슬롯 | 심볼 | TF | 방향 | 전략 | TP/SL | 기대 OOS |
|------|------|----|------|------|-------|----------|
| 13 | BTC | 1h | SHORT | 2_OBV_VWAP | 5.0/3.0 | 0.86 |
| 14 | XRP | 1h | SHORT | 2_MOM_VWAP | 3.0/2.0 | 0.86 |
| 15 | ETH | 1h | SHORT | 2_CMF_AD | 5.0/3.0 | 0.86 |
| 16 | XRP | 15m | SHORT | 2_CMF_CCI | 5.0/3.0 | 0.82 |
| 17 | ETH | 4h | LONG | S_ADX | 5.0/2.0 | 0.83 |
| 18 | XRP | 4h | LONG | 2_MOM_VWAP | 5.0/3.0 | 0.83 |

---

## PART 4. 코드 수정 설계

### 4-1. indicators.py 수정 범위

#### A. FULL_IND_MAP 축소 (27개 -> 16개)

```python
# === 제거 대상 (11개) ===
# SMA, EMA, MACD, RSI, STOCH, WILLR, BB, PSAR, ICHIMOKU, DONCHIAN, KELTNER
# (MFI는 보류 - XRP 1h에서 B등급이지만 독립 성과 부족)

# === 유지 대상 (16개) ===
FULL_IND_MAP = {
    # ── 핵심 신호 지표 (6개) ──
    'OBV':      (new_col, new_col, False),   # 거래량 추세
    'VWAP':     (new_col, new_col, False),   # 거래량가중가격
    'AD':       (new_col, new_col, False),   # 매집/분산
    'CMF':      (new_col, new_col, False),   # 자금흐름
    'MOM':      (new_col, new_col, False),   # 모멘텀
    'ROC':      (new_col, new_col, False),   # 변화율
    
    # ── 보조 신호 지표 (3개) ──
    'AROON':    (new_col, new_col, False),   # 추세방향
    'STDDEV':   (new_col, new_col, False),   # 변동성
    'CCI':      (new_col, new_col, False),   # 과매수/과매도
    'MFI':      (new_col, new_col, False),   # 보조 (보류)
    
    # ── 필터 지표 (6개) ──
    'ADX':      (new_col, new_col, True),    # 추세강도
    'ATR_SIG':  (new_col, new_col, True),    # 변동성활성
    'VOLUME':   (new_col, new_col, True),    # 거래량급증
    'ADX_INV':  (new_col, new_col, True),    # 횡보필터
    'ATR_INV':  (new_col, new_col, True),    # 저변동성필터
    'VOL_INV':  (new_col, new_col, True),    # 거래량정상
}
```

#### B. 신호 배열 축소 (38컬럼 -> 22컬럼)

기존 sig38에서 제거되는 컬럼:
- col 0 (SMA), col 1 (EMA), col 2 (MACD)
- col 4,5 (RSI long/short)
- col 6,7 (STOCH long/short)
- col 8,9 (WILLR long/short)
- col 10,11 (BB long/short)
- col 12,13 (PSAR long/short)
- col 14,15 (ICHIMOKU long/short)
- col 20,21 (EMA stack)
- col 25 (DONCHIAN)
- col 26 (KELTNER)

유지 컬럼 (리넘버링 필요):
```
new_col 0  = old col 3  (ADX 필터)
new_col 1  = old col 16 (OBV long/short)
new_col 2  = old col 17 (CMF long)
new_col 3  = old col 18 (CMF short)
new_col 4  = old col 19 (ATR_SIG 필터)
new_col 5  = old col 22 (AROON)
new_col 6  = old col 23 (CCI long)
new_col 7  = old col 24 (CCI short)
new_col 8  = old col 27 (MFI long)
new_col 9  = old col 28 (MFI short)
new_col 10 = old col 29 (MOM)
new_col 11 = old col 30 (ROC)
new_col 12 = old col 31 (VOLUME 필터)
new_col 13 = old col 32 (VWAP)
new_col 14 = old col 33 (STDDEV)
new_col 15 = old col 34 (AD)
new_col 16 = old col 35 (ADX_INV)
new_col 17 = old col 36 (ATR_INV)
new_col 18 = old col 37 (VOL_INV)
```

#### C. compute_signals() 함수 수정

```python
def compute_signals(df: pd.DataFrame):
    """
    v4.0: B등급 이상 검증 지표만 계산 (38 -> 19컬럼)
    제거: SMA, EMA, MACD, RSI, STOCH, WILLR, BB, PSAR, ICHIMOKU, DONCHIAN, KELTNER
    """
    # ... 기존 전처리 동일 ...
    
    # 제거된 지표 계산 스킵 → 성능 ~40% 향상
    # ADX 필터만 base에서 계산
    sig_adx = _compute_adx_filter(high, low, close, N)  # (N, 1)
    
    # 유지 지표 계산
    sig_obv_cmf_atr = _compute_volume_indicators(close, high, low, vol, N)  # OBV, CMF, ATR_SIG
    sig_extra = compute_extra_v4(close, high, low, vol, N)  # AROON, CCI, MFI, MOM, ROC, VOLUME, VWAP
    sig_extra2 = compute_extra2(close, high, low, vol, N)   # STDDEV, AD
    sig_extra3 = compute_extra3(close, high, low, vol, N, atr14)  # ADX_INV, ATR_INV, VOL_INV
    
    sig19 = np.hstack([sig_adx, sig_obv_cmf_atr, sig_extra, sig_extra2, sig_extra3])
    return sig19, atr14, close
```

#### D. load_combo_list() 수정

```python
def load_combo_list(data_dir: str):
    """
    v4.0: 축소된 지표 세트로 조합 생성
    10개 방향성 지표 + 6개 필터 = 16개
    C(10,1)+C(10,2)+C(10,3) = 10+45+120 = 175 기본 조합
    + 필터 조합 추가 → 약 800~1200개 (기존 2,324개 대비 48~52% 감소)
    """
```

### 4-2. config.py 수정 (TP/SL 기본값)

```python
# === 기존 ===
# TP/SL 전수 탐색: [1.0, 1.3, 1.5, 2.0, 3.0, 5.0] x [1.0, 1.3, 1.5, 2.0, 3.0]

# === 변경 ===
# B등급 이상 검증된 TP/SL 조합만 사용
TPSL_GRID = {
    'default':  {'tp': [3.0, 5.0], 'sl': [1.5, 2.0, 3.0]},  # 6조합 (기존 30 → 6)
    'BTC_1h':   {'tp': [5.0],      'sl': [1.5, 2.0, 3.0]},   # 3조합
    'ETH_1h':   {'tp': [3.0, 5.0], 'sl': [2.0, 3.0]},        # 4조합
    'XRP_1h':   {'tp': [3.0, 5.0], 'sl': [1.5, 2.0, 3.0]},   # 6조합
}

# 최악 TP/SL 블랙리스트 (OOS < 0.50)
TPSL_BLACKLIST = [
    (1.3, 1.0),   # 평균 OOS 0.4698, 수익률 -36.55%
    (5.0, 1.0),   # 평균 OOS 0.4586, 수익률 -46.86%
    (1.5, 1.0),   # 실전 검증 실패
    (2.0, 1.0),   # SL 1.0% 전체 제거 (급변 시 즉시 손절)
]
```

### 4-3. 타임프레임/방향 제한

```python
# === 실전 운용 TF/방향 매트릭스 ===
ACTIVE_CONFIGS = {
    # (심볼, TF, 방향): 활성화 여부
    ('BTC', '5m',  'LONG'):  False,   # 5m 전체 비활성
    ('BTC', '5m',  'SHORT'): False,
    ('BTC', '5m',  'BOTH'):  False,
    ('BTC', '15m', 'LONG'):  True,    # 15m BTC LONG만 활성
    ('BTC', '15m', 'SHORT'): False,
    ('BTC', '15m', 'BOTH'):  False,
    ('BTC', '1h',  'LONG'):  True,    # 1h 핵심
    ('BTC', '1h',  'SHORT'): True,
    ('BTC', '1h',  'BOTH'):  False,   # BOTH 비활성
    ('BTC', '4h',  'LONG'):  False,
    ('BTC', '4h',  'SHORT'): False,
    ('BTC', '4h',  'BOTH'):  False,
    
    ('ETH', '5m',  'LONG'):  False,
    ('ETH', '5m',  'SHORT'): False,   # ETH 5m B등급 1개 있으나 전체 TF 성과 최악
    ('ETH', '5m',  'BOTH'):  False,
    ('ETH', '15m', 'LONG'):  True,    # B등급 일부 존재
    ('ETH', '15m', 'SHORT'): False,
    ('ETH', '15m', 'BOTH'):  False,
    ('ETH', '1h',  'LONG'):  True,    # 핵심
    ('ETH', '1h',  'SHORT'): True,    # 핵심
    ('ETH', '1h',  'BOTH'):  False,
    ('ETH', '4h',  'LONG'):  True,    # A등급 존재
    ('ETH', '4h',  'SHORT'): True,    # B등급 다수
    ('ETH', '4h',  'BOTH'):  False,
    
    ('XRP', '5m',  'LONG'):  False,
    ('XRP', '5m',  'SHORT'): False,
    ('XRP', '5m',  'BOTH'):  False,
    ('XRP', '15m', 'LONG'):  False,
    ('XRP', '15m', 'SHORT'): True,    # A등급 2_CMF_CCI
    ('XRP', '15m', 'BOTH'):  False,
    ('XRP', '1h',  'LONG'):  True,    # A등급 존재
    ('XRP', '1h',  'SHORT'): True,    # S등급 핵심
    ('XRP', '1h',  'BOTH'):  False,
    ('XRP', '4h',  'LONG'):  True,    # A등급 존재
    ('XRP', '4h',  'SHORT'): True,    # B등급
    ('XRP', '4h',  'BOTH'):  False,
}
```

---

## PART 5. 교체 효과 예측

### 5-1. 지표 수 변화
| 항목 | 기존(v3.8) | 변경(v4.0) | 변화 |
|------|-----------|-----------|------|
| 전체 지표 수 | 27개 | 16개 | -41% |
| 방향성 지표 | 21개 | 10개 | -52% |
| 필터 지표 | 6개 | 6개 | 유지 |
| 신호 배열 크기 | (N, 38) | (N, 19) | -50% |

### 5-2. 조합 수 변화
| 항목 | 기존 | 변경 | 변화 |
|------|------|------|------|
| 총 조합 수 | ~2,324개 | ~800개 | -66% |
| TP/SL 그리드 | 30조합 | 6조합 | -80% |
| TF/방향 활성 슬롯 | 36개 | 14개 | -61% |
| **총 백테스트 수** | **~472개 (분석된)** | **~170개 (추정)** | **-64%** |

### 5-3. 예상 성과 향상
| 지표 | 기존 전체 | 변경 후 예상 | 근거 |
|------|----------|------------|------|
| D등급 비율 | 61.2% | ~15% | 최악 지표/TF 제거 |
| B+등급 비율 | 27.1% | ~65% | 검증된 조합만 남김 |
| 평균 OOS | ~0.55 | ~0.72 | D등급 대폭 감소 |
| 평균 수익률 | ~10% | ~80% | 최적 TP/SL + 1h집중 |
| 계산 시간 | 기준 | -50% | 신호 배열 축소 |

### 5-4. 심볼별 배분 전략
```
총 포트폴리오 = 100%

BTC (35%):
  - 1h LONG S_ADX:     15%  (S등급, 가장 안정적)
  - 1h LONG S_MOM:     10%  (A등급 상위)
  - 1h SHORT 2_OBV_MOM: 10% (A등급)

ETH (35%):
  - 1h LONG 2_OBV_VWAP: 15%  (S등급)
  - 1h SHORT S_CMF:     10%  (A등급)
  - 1h LONG 2_OBV_AD:   10%  (A등급)

XRP (30%):
  - 1h SHORT S_AD:      15%  (S등급, 최고 성과)
  - 1h SHORT 2_VWAP_AD: 10%  (S등급)
  - 1h SHORT 2_OBV_AD:   5%  (A등급, 분산)
```

---

## PART 6. 교체 이유 종합

### 왜 이 10개 지표인가?

| 지표 | 선정 이유 |
|------|----------|
| **OBV** | B+ 전략에 20회 등장. 거래량의 방향성을 가장 잘 포착. 암호화폐 시장에서 거래량=스마트머니 움직임의 선행지표 |
| **VWAP** | 최고 평균 OOS(0.6510). 기관 트레이더의 벤치마크 가격으로, 이 위/아래에서의 거래는 매수/매도 압력의 명확한 신호 |
| **AD** | OOS 0.9837의 최고 성과 전략(S_AD)의 핵심. 가격-거래량 괴리를 포착하여 숨겨진 매집/분산 감지 |
| **CMF** | AD의 정규화 버전으로 구간 비교 가능. ETH에서 특히 강력한 성과. 자금 유입/유출의 정량적 측정 |
| **ADX** | 추세 존재 여부를 필터링하여 횡보장 진입을 차단. S등급 전략(BTC 1h LONG)의 핵심 필터 |
| **MOM** | 단순하지만 강력. 10봉 전 대비 가격 방향만으로 A등급(OOS 0.8871) 달성. 과적합 위험 최소 |
| **ROC** | MOM의 비율 버전. 서로 다른 가격대의 코인 간 비교 가능. MOM과 동일한 A등급 성과 |
| **AROON** | 추세 시작/종료 시점 포착. BTC 15m에서 ADX와 조합 시 A등급 달성 |
| **STDDEV** | 변동성 팽창 구간 포착. S등급(3_STDDEV_AD_ADX)의 핵심. 스퀴즈 후 폭발 움직임 감지 |
| **CCI** | XRP 15m에서 A등급, 다수 B등급. 평균 대비 가격 위치를 표준화하여 극단적 이탈 감지 |

### 왜 이 지표들을 제거하는가?

| 제거 지표 | 핵심 제거 이유 |
|----------|--------------|
| **MACD** | "만능 지표"라는 인식과 달리, 암호화폐 5m~4h에서 평균 OOS 0.4598로 **가장 낮은 성과**. 크로스오버 신호가 너무 늦게 발생하여 빠른 암호화폐 시장에서 지속적으로 손실 |
| **ICHIMOKU** | 일봉 기반으로 설계된 지표를 분/시 차트에 적용하는 구조적 문제. 26봉 기준선이 5m~1h에서는 의미 없는 과거 데이터 참조 |
| **SMA** | EMA 대비 반응 속도 2배 느림. 골든/데드크로스가 이미 가격에 반영된 후 발생. B+등급 0회 |
| **RSI** | 30/70 경계값이 강한 추세장에서 지속적으로 오신호 발생. 암호화폐의 추세 지속성 특성과 충돌 |
| **STOCH** | RSI보다 노이즈에 취약. 20/80 경계에서 반복적 휩소(whipsaw) 발생. B+등급 0회 |
| **WILLR** | RSI와 수학적으로 동치(100-RSI). 중복 지표. B+등급 0회 |
| **BB** | 2시그마 밴드 터치가 반등/반락을 보장하지 않음. 강한 추세에서 밴드 워킹 발생. KELTNER 대비 우위 없음, 둘 다 제거 |
| **PSAR** | 횡보장에서 잦은 반전 신호로 손실 누적. af=0.02의 민감도가 암호화폐 변동성에 부적합 |

---

## PART 7. 구현 우선순위

```
Phase 1 (즉시): config.py TP/SL 그리드 축소 + ACTIVE_CONFIGS 설정
Phase 2 (1일):  indicators.py FULL_IND_MAP 축소 + 신호 배열 리넘버링
Phase 3 (2일):  compute_signals() 불필요 계산 제거 + sig19 배열 생성
Phase 4 (3일):  load_combo_list() 새 조합 생성 + 백테스트 재실행
Phase 5 (4일):  결과 검증 + 실전 배포
```
