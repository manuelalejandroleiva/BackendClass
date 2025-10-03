import aio_pika
import json
from typing import Callable, Awaitable

RABBITMQ_URL = "amqp://guest:guest@localhost/"

class RabbitMQPublisher:
    def __init__(self, url: str = RABBITMQ_URL):
        self.url = url
        self.connection = None
        self.channel = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()

    async def publish(self, exchange_name: str, routing_key: str, event: str, data: dict):
        if not self.channel:
            await self.connect()

        exchange = await self.channel.declare_exchange(exchange_name, aio_pika.ExchangeType.TOPIC, durable=True)

        message = aio_pika.Message(
            body=json.dumps({
                "event": event,
                "data": data
            }).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await exchange.publish(message, routing_key=routing_key)


class RabbitMQConsumer:
    def __init__(self, url: str = RABBITMQ_URL):
        self.url = url
        self.connection = None
        self.channel = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()

    async def consume(self, queue_name: str, callback: Callable[[dict], Awaitable[None]]):
        if not self.channel:
            await self.connect()

        queue = await self.channel.declare_queue(queue_name, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    body = json.loads(message.body.decode())
                    await callback(body)
