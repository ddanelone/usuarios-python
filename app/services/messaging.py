# services/messaging.py
import json
import uuid
from aio_pika import connect_robust, Message, ExchangeType
from app.core.config import settings

QUEUE_NAME = "reset_password"

async def publish_email_message(to: str, token: str, type_: str):
    correlation_id = str(uuid.uuid4())
    payload = {
        "to": to,
        "token": token,
        "type": type_,
        "correlationId": correlation_id,
    }

    connection = await connect_robust(settings.RABBITMQ_URI)
    channel = await connection.channel()
    await channel.declare_queue(QUEUE_NAME, durable=True)
    message = Message(body=json.dumps(payload).encode())
    await channel.default_exchange.publish(message, routing_key=QUEUE_NAME)
    await connection.close()

    return correlation_id
