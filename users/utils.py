import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms(phone_number: str, message: str) -> bool:
    """Send SMS to phone_number.

    Uses Twilio if `TWILIO_ACCOUNT_SID` and `TWILIO_AUTH_TOKEN` are present in env;
    otherwise falls back to printing/logging for development.
    """
    try:
        sid = os.getenv('TWILIO_ACCOUNT_SID') or getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        token = os.getenv('TWILIO_AUTH_TOKEN') or getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        from_number = os.getenv('TWILIO_FROM_NUMBER') or getattr(settings, 'TWILIO_FROM_NUMBER', None)

        if sid and token and from_number:
            try:
                from twilio.rest import Client
            except Exception as e:
                logger.error('Twilio library not installed: %s', e)
                # Fall back to logging
                print(f"📱 SMS to {phone_number}: {message}")
                logger.info(f"SMS (fallback) to {phone_number}: {message}")
                return True

            client = Client(sid, token)
            # Twilio expects E.164 formatted numbers; assume caller provides correct format
            resp = client.messages.create(body=message, from_=from_number, to=phone_number)
            logger.info('Twilio SMS sent: sid=%s status=%s to=%s', getattr(resp, 'sid', None), getattr(resp, 'status', None), phone_number)
            return True

        # No Twilio configured — development fallback
        print(f"📱 SMS to {phone_number}: {message}")
        logger.info(f"SMS (dev) to {phone_number}: {message}")
        return True
    except Exception as e:
        logger.exception(f"Failed to send SMS to {phone_number}: {e}")
        return False
