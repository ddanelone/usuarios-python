from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from app.core.config import settings
from pydantic import SecretStr
from typing import cast

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=SecretStr(settings.MAIL_PASSWORD),
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,  # MAILTRAP: TRUE / CORREOS REALES: FALSE
    MAIL_SSL_TLS=False,    # MAILTRAP: FALSE / CORREOS REALES: TRUE
    USE_CREDENTIALS=True,
    MAIL_FROM_NAME="Simulación 2025"
)

async def send_reset_email(to_email: EmailStr, token: str):
    message = MessageSchema(
         subject="Recuperación de contraseña",
         recipients=[to_email],
         body=f"Hola,\n\nTu token de recuperación es: {token}",
         subtype=cast(MessageType, "plain")  
)
    fm = FastMail(conf)
    await fm.send_message(message)

async def send_welcome_email(to_email: EmailStr, name: str):
    message = MessageSchema(
        subject="¡Bienvenido a nuestra plataforma!",
        recipients=[to_email],
        body=f"Hola {name},\n\nGracias por registrarte. ¡Bienvenido!",
        subtype=cast(MessageType, "plain")
    )

    fm = FastMail(conf)
    await fm.send_message(message)