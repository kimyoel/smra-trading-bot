"""
utils/notifier.py — 텔레그램 알림
"""

import os
import requests
from utils.logger import get_logger

logger = get_logger("notifier")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")
BASE_URL  = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def send_telegram(message: str) -> bool:
    """텔레그램 메시지 전송. 실패해도 봇은 계속 동작."""
    if not BOT_TOKEN or not CHAT_ID:
        logger.warning("[TELEGRAM] 환경변수 미설정 — 알림 스킵")
        return False
    try:
        resp = requests.post(
            BASE_URL,
            json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=10
        )
        if resp.status_code != 200:
            logger.warning(f"[TELEGRAM] 전송 실패: {resp.status_code} {resp.text}")
            return False
        return True
    except Exception as e:
        logger.warning(f"[TELEGRAM] 예외 발생: {e}")
        return False


def notify_entry(strategy_id: str, symbol: str, side: str,
                 entry: float, tp: float, sl: float,
                 leverage: int, margin: float) -> None:
    msg = (
        f"✅ <b>진입</b>\n"
        f"전략: {strategy_id}\n"
        f"심볼: {symbol} {side}\n"
        f"진입가: {entry:.4f}\n"
        f"TP: {tp:.4f} | SL: {sl:.4f}\n"
        f"레버: {leverage}x | 마진: ${margin:.2f}"
    )
    send_telegram(msg)


def notify_close(strategy_id: str, symbol: str,
                 result: str, pnl: float) -> None:
    icon = "🟢" if pnl >= 0 else "🔴"
    msg = (
        f"{icon} <b>청산</b>\n"
        f"전략: {strategy_id}\n"
        f"심볼: {symbol}\n"
        f"결과: {result}\n"
        f"PnL: {pnl:+.2f} USDT"
    )
    send_telegram(msg)


def notify_circuit_breaker(reason: str, detail: str = "") -> None:
    msg = (
        f"🚨 <b>Circuit Breaker 발동</b>\n"
        f"사유: {reason}\n"
        f"{detail}"
    )
    send_telegram(msg)


def notify_error(error: str) -> None:
    msg = f"❌ <b>봇 오류</b>\n{error}"
    send_telegram(msg)
