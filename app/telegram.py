import logging
import httpx
from sqlalchemy.orm import Session
from app.database import get_config_val
from app.database import Strike

logger = logging.getLogger("app.telegram")

async def send_telegram_notification(db: Session, strike: Strike):
    """
    Sends a telegram message about a detected lightning strike if enabled.
    """
    try:
        enabled = get_config_val(db, "telegram_enabled", "false").lower() == "true"
        if not enabled:
            return

        token = get_config_val(db, "telegram_token", "")
        chat_id = get_config_val(db, "telegram_chat_id", "")

        if not token or not chat_id:
            logger.warning("Telegram is enabled but Token or Chat ID is missing.")
            return

        message = (
            f"⚡ **Lightning Strike Detected!** ⚡\n\n"
            f"📍 **Distance:** {strike.distance} km\n"
            f"💥 **Energy Intensity:** {strike.intensity}\n"
            f"⏰ **Time (UTC):** {strike.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        await dispatch_telegram_message(token, chat_id, message)
    except Exception as e:
        logger.error(f"Failed to prepare Telegram notification: {e}")

async def send_test_message(token: str, chat_id: str) -> bool:
    """
    Sends a test telegram message to verify credentials.
    """
    message = "⚡ **Lightning Tracker Telegram Bot Test Connection Successful!**"
    return await dispatch_telegram_message(token, chat_id, message)

async def dispatch_telegram_message(token: str, chat_id: str, message: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                logger.info("Telegram notification sent successfully.")
                return True
            else:
                logger.error(f"Telegram API returned status code {response.status_code}: {response.text}")
                return False
    except httpx.RequestError as e:
        logger.error(f"Network error while sending Telegram notification: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Telegram notification: {e}")
        return False
