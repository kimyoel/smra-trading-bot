"""
utils/notifier.py — 텔레그램 알림 (v6.3.2)

v6.3.2:
  [FIX] 파일 기반 에러 알림 중복 차단 (_error_dedup)
    - Railway 재시작 시에도 동일 에러 메시지 반복 전송 방지
    - 해시 기반: 동일 에러 → 동일 해시 → 1회만 전송
    - 쿨다운: ERROR_DEDUP_COOLDOWN_SEC (기본 3600초) 경과 후 재전송 허용
    - 초기화: data/error_dedup.json (프로세스 재시작 시 유지)
"""

import os
import json
import time
import hashlib
import requests
from utils.logger import get_logger

logger = get_logger("notifier")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")
BASE_URL  = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# ── 에러 알림 중복 차단 설정 ──────────────────────────────────
ERROR_DEDUP_FILE        = "data/error_dedup.json"
ERROR_DEDUP_COOLDOWN_SEC = 3600   # 1시간 쿨다운 후 동일 에러 재전송 허용


def _load_error_dedup() -> dict:
    """파일에서 에러 중복 기록 로드."""
    try:
        if os.path.exists(ERROR_DEDUP_FILE):
            with open(ERROR_DEDUP_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"[TELEGRAM] error_dedup 로드 실패 (초기화): {e}")
    return {}


def _save_error_dedup(data: dict) -> None:
    """에러 중복 기록 파일 저장."""
    try:
        os.makedirs(os.path.dirname(ERROR_DEDUP_FILE), exist_ok=True)
        with open(ERROR_DEDUP_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        logger.warning(f"[TELEGRAM] error_dedup 저장 실패: {e}")


def _is_error_duplicate(error_msg: str) -> bool:
    """
    동일 에러 메시지가 쿨다운 내에 이미 전송되었는지 확인.
    True면 중복 → 전송 스킵.
    """
    msg_hash = hashlib.md5(error_msg.encode()).hexdigest()
    dedup    = _load_error_dedup()
    last_ts  = dedup.get(msg_hash, 0)
    now      = time.time()

    if now - last_ts < ERROR_DEDUP_COOLDOWN_SEC:
        return True  # 쿨다운 내 → 중복

    # 새로 기록
    dedup[msg_hash] = now
    # 오래된 항목 정리 (24시간 이상)
    dedup = {k: v for k, v in dedup.items() if now - v < 86400}
    _save_error_dedup(dedup)
    return False


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
                 leverage: int, margin: float,
                 timeframe: str = "") -> None:
    tf_label = f" ({timeframe})" if timeframe else ""
    msg = (
        f"✅ <b>진입</b>\n"
        f"전략: {strategy_id}{tf_label}\n"
        f"심볼: {symbol} {side}\n"
        f"진입가: {entry:.4f}\n"
        f"TP: {tp:.4f} | SL: {sl:.4f}\n"
        f"레버: {leverage}x | 마진: ${margin:.2f}"
    )
    send_telegram(msg)


def notify_close(strategy_id: str, symbol: str,
                 result: str, pnl: float,
                 timeframe: str = "") -> None:
    icon = "🟢" if pnl >= 0 else "🔴"
    tf_label = f" ({timeframe})" if timeframe else ""
    msg = (
        f"{icon} <b>청산</b>\n"
        f"전략: {strategy_id}{tf_label}\n"
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
    # CB도 동일 사유 반복 전송 방지
    dedup_key = f"CB:{reason}:{detail}"
    if _is_error_duplicate(dedup_key):
        logger.info(f"[TELEGRAM] CB 알림 중복 → 스킵 ({reason})")
        return
    send_telegram(msg)


def notify_error(error: str) -> None:
    """에러 알림 (파일 기반 중복 차단 — Railway 재시작 시에도 유지)."""
    if _is_error_duplicate(error):
        logger.info(f"[TELEGRAM] 에러 알림 중복 → 스킵 (쿨다운 {ERROR_DEDUP_COOLDOWN_SEC}초)")
        return
    msg = f"❌ <b>봇 오류</b>\n{error}"
    send_telegram(msg)
