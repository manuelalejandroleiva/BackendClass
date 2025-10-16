import aio_pika
import asyncio
import json
import uuid
from typing import Callable, Awaitable, Dict
from functools import wraps

# =============================
# 🔌 Decorador message_pattern
# =============================
message_handlers: Dict[str, Callable] = {}

def message_pattern(pattern: str):
    """Registra un handler para un patrón de routing key."""
    def decorator(func: Callable[[dict], Awaitable[dict]]):
        message_handlers[pattern] = func

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper
    return decorator


# =============================
# 🚀 Clase MessageBroker
# =============================
class MessageBroker:
    def __init__(self, url: str, exchange_name="app_exchange"):
        self.url = url
        self.exchange_name = exchange_name
        self.connection = None
        self.channel = None
        self.exchange = None

    # -----------------------------
    # 🔗 Conexión y cierre
    # -----------------------------
    async def connect(self):
        if self.connection and not self.connection.is_closed:
            return
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.declare_exchange(
            self.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
        )
        print(f"✅ [Broker] Conectado a RabbitMQ → exchange='{self.exchange_name}'")

    async def close(self):
        if self.connection:
            await self.connection.close()
            print("🔻 [Broker] Conexión cerrada")

    # -----------------------------
    # 📤 Publicar mensajes
    # -----------------------------
    async def publish(self, routing_key: str, message: dict, correlation_id=None, reply_to=None):
        """Publica un mensaje. Si es RPC reply, se envía directamente a la cola temporal."""
        await self.connect()
        body = json.dumps(message, default=str).encode()
        msg = aio_pika.Message(
            body=body,
            correlation_id=correlation_id,
            reply_to=reply_to,
            content_type="application/json",
        )

        try:
            # 🧠 Si es una cola temporal (amq.gen-...) o no está ligada al exchange → enviar directo
            if routing_key.startswith("amq.") or routing_key.startswith("reply_"):
                await self.channel.default_exchange.publish(msg, routing_key=routing_key)
                print(f"📬 [Broker] Respuesta enviada a cola directa → {routing_key}")
            else:
                await self.exchange.publish(msg, routing_key=routing_key)
                print(f"📤 [Broker] Mensaje publicado → {routing_key}")
        except Exception as e:
            print(f"❌ [Broker] Error al publicar en '{routing_key}': {e}")


    # -----------------------------
    # 🔁 RPC request/response
    # -----------------------------
    async def rpc_request(self, routing_key: str, payload: dict, timeout: int = 5):
        """Realiza una llamada RPC y espera la respuesta."""
        await self.connect()
        correlation_id = str(uuid.uuid4())
        reply_queue = await self.channel.declare_queue(exclusive=True, auto_delete=True)
        future = asyncio.get_event_loop().create_future()

        print(f"📡 [RPC] Enviando → {routing_key} (corr_id={correlation_id})")

        async def on_message(message: aio_pika.IncomingMessage):
            async with message.process():
                if message.correlation_id == correlation_id:
                    data = json.loads(message.body.decode())
                    future.set_result(data)
                    print(f"📨 [RPC] Respuesta recibida (corr_id={correlation_id})")

        await reply_queue.consume(on_message)
        await self.publish(
            routing_key, payload, correlation_id=correlation_id, reply_to=reply_queue.name
        )

        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            print(f"⏱️ [RPC] Timeout esperando respuesta de '{routing_key}'")
            raise

    # -----------------------------
    # 🎧 Subscripción de handlers
    # -----------------------------
    async def subscribe_patterns(self):
        """Suscribe automáticamente todos los handlers registrados con message_pattern."""
        await self.connect()
        for pattern, handler in message_handlers.items():
            queue_name = f"queue_{pattern.replace('.', '_')}"
            queue = await self.channel.declare_queue(queue_name, durable=True)
            await queue.bind(self.exchange, routing_key=pattern)

            async def _callback(message: aio_pika.IncomingMessage, h=handler, p=pattern):
                async with message.process():
                    try:
                        # Convierte a dict desde el body de RabbitMQ
                        payload_str = message.body.decode()
                        payload = json.loads(payload_str)  # ahora es dict

                        print(f"📩 [Handler:{p}] Mensaje recibido: {payload}")
                        result = await h(payload)  # ahora payload es dict, no str

                        # Responder vía RPC
                        if message.reply_to:
                            reply_msg = aio_pika.Message(
                                body=json.dumps(result, default=str).encode(),
                                correlation_id=message.correlation_id,
                                content_type="application/json"
                            )
                            await self.channel.default_exchange.publish(
                                reply_msg,
                                routing_key=message.reply_to
                            )
                            print(f"📬 [Handler:{p}] Respuesta enviada a cola: {message.reply_to}")

                    except Exception as e:
                        print(f"❌ [Handler:{p}] Error: {e}")


            await queue.consume(_callback)
            print(f"🎧 [Broker] Escuchando patrón: {pattern}")
