import logging

from app.config import settings

logger = logging.getLogger("tossline.email")


def send_pin_email(to_email: str, pin: str) -> None:
    if settings.email_backend == "resend":
        _send_via_resend(to_email, pin)
    else:
        _send_via_console(to_email, pin)


def _send_via_console(to_email: str, pin: str) -> None:
    logger.info("LOGIN PIN for %s: %s", to_email, pin)


def _send_via_resend(to_email: str, pin: str) -> None:
    import resend

    resend.api_key = settings.resend_api_key
    resend.Emails.send(
        {
            "from": settings.email_from,
            "to": [to_email],
            "subject": "Your login code",
            "html": f"<p>Your login code is <strong>{pin}</strong>. It expires in {settings.pin_expire_minutes} minutes.</p>",
        }
    )
