# SMRA Trading Bot

**Sharpe-Multi-Regime Alpha Bot** — Binance Futures 자동매매 봇

## 개요
WFA(Walk-Forward Analysis) OOS 백테스트 검증된 10개 전략을 상시 모니터링하며 Score 기반으로 최우선 신호를 선택, 바이낸스 선물 포지션을 자동 관리하는 봇입니다.

## 전략 (v5.0)
- BTC/USDT 15m: 10개 전략 (LONG 5 + SHORT 5)
- WFA 황금 기준 통과: survived_windows ≥ 5, avg_calmar ≥ 2.0, min_calmar ≥ 0.5
- Score 기반 충돌 해소: 동일 심볼 복수 신호 시 Score 최고 1개만 실행

### LONG 전략
1. L1_WILLR_BB_EMA_STACK (Score 19.21) — 추세 추종형 평균 회귀
2. L2_ADX_WILLR_EMA_STACK (Score 18.73) — 안정성 최고
3. L3_AROON_DONCHIAN_VOL_INV (Score 15.97) — 저볼륨 돌파
4. L4_EMA_MACD_PSAR (Score 15.64) — 단기 모멘텀
5. L5_EMA_PSAR_MOM (Score 15.53) — 고RR 타이트 손절

### SHORT 전략
1. S1_WILLR_BB_OBV (Score 20.36) — 종합 1위, 3차원 숏
2. S2_SMA_ICHIMOKU_STDDEV (Score 19.36) — 변동성 확장 숏
3. S3_OBV_KELTNER_ADX_INV (Score 18.98) — 횡보장 역추세
4. S4_BB_EMA_STACK (Score 18.73) — 7윈도우 안정형
5. S5_BB_EMA_STACK_ATR_INV (Score 18.73) — ATR 필터 버전

## 설치 및 실행

### 환경 변수 설정
```bash
cp .env.example .env
# .env 파일에 API 키 입력
```

### 로컬 실행
```bash
pip install -r requirements.txt
python main.py
```

### Railway 배포
- Railway 프로젝트에 GitHub 연결
- 환경 변수 4개 설정 (BINANCE_API_KEY, BINANCE_API_SECRET, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
- Dockerfile 자동 감지 후 배포

## 주요 특징
- TP/SL: WFA 백테스트 검증된 고정 % (전략별 최적값)
- 서킷브레이커: 플래시크래시, 스프레드, 펀딩율, MDD 감지
- 전략별 max_hold_bars 기반 강제청산 (12~48봉)
- Telegram 알림 지원
- Score 기반 충돌 해소 (WFA 종합 스코어 순위)
