# SMRA Trading Bot

**Sharpe-Multi-Regime Alpha Bot** — Binance Futures 자동매매 봇

## 개요
13개 전략을 상시 모니터링하며 Sharpe 비율 기반으로 최우선 신호를 선택, 바이낸스 선물 포지션을 자동 관리하는 봇입니다.

## 전략
- BTC/USDT: 10개 전략 (5m, 15m 타임프레임)
- ETH/USDT: 1개 전략 (5m)
- XRP/USDT: 2개 전략 (1h)

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
- TP/SL: ATR 기반 동적 설정 또는 고정 퍼센트
- 서킷브레이커: 플래시크래시, 스프레드, 펀딩율, MDD 감지
- 24봉 기준 강제청산 (타임프레임별 자동 계산)
- Telegram 알림 지원
