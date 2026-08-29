import os
from neonize.client import NewClient
from neonize.utils.jid import build_jid

from moodle_bot.config import DEFAULT_PHONE_NUMBER


def send_message(
    client: NewClient,
    message: str,
    phone_number: str | None = None,
) -> bool:
    """
    Send a WhatsApp text message using an active Neonize client instance.

    :param client: Connected NewClient instance
    :param message: Text string to send
    :param phone_number: Target phone number (e.g. 94767581730). If None, reads DEFAULT_PHONE_NUMBER from env.
    :return: True if sent successfully, False otherwise
    """
    if client is None:
        print("❌ WhatsApp client is not initialized or connected.")
        return False

    target_number = phone_number or DEFAULT_PHONE_NUMBER or os.getenv("DEFAULT_PHONE_NUMBER", "94767581730")
    if not target_number:
        print("❌ No target phone number specified.")
        return False

    try:
        # Strip any leading '+' if present
        clean_number = target_number.lstrip("+").strip()
        target_jid = build_jid(clean_number)
        client.send_message(target_jid, message)
        print(f"✅ Sent message to +{clean_number}")
        return True
    except Exception as e:
        print(f"❌ Error sending WhatsApp message: {e}")
        return False


# Backward-compatible alias
send_msg = send_message
