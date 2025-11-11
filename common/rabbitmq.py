import aio_pika
import asyncio
import json
import uuid
from typing import Callable, Awaitable, Dict, Optional
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
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.processed_ids: set = set()

    # -----------------------------
    # 🔗 Conexión y cierre
    # -----------------------------
    async def connect(self):
        if self.connection and not self.connection.is_closed:
            return
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()
        
        # Aumentar el tiempo de espera para mensajes
        await self.channel.set_qos(prefetch_count=1)
        
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
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
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
    async def rpc_request(self, routing_key: str, payload: dict, timeout: int = 30):
        """Realiza una llamada RPC y espera la respuesta."""
        await self.connect()
        correlation_id = str(uuid.uuid4())
        reply_queue = await self.channel.declare_queue(
            exclusive=True, 
            auto_delete=True,
            durable=False
        )
        future = asyncio.get_event_loop().create_future()
        
        # Guardar el future
        self.pending_requests[correlation_id] = future

        print(f"📡 [RPC] Enviando → {routing_key} (corr_id={correlation_id})")

        async def on_message(message: aio_pika.IncomingMessage):
            async with message.process():
                if message.correlation_id == correlation_id:
                    # Verificar si ya procesamos este mensaje
                    if correlation_id in self.processed_ids:
                        print(f"⚠️ [RPC] Mensaje duplicado ignorado: {correlation_id}")
                        return
                    
                    self.processed_ids.add(correlation_id)
                    
                    try:
                        data = json.loads(message.body.decode())
                        print(f"📨 [RPC] Respuesta recibida (corr_id={correlation_id})")
                        
                        # Resolver el future solo si existe y no está resuelto
                        if correlation_id in self.pending_requests:
                            future_to_resolve = self.pending_requests[correlation_id]
                            if not future_to_resolve.done():
                                future_to_resolve.set_result(data)
                                print(f"✅ [RPC] Future resuelto exitosamente: {correlation_id}")
                            else:
                                print(f"⚠️ [RPC] Future ya estaba resuelto: {correlation_id}")
                        else:
                            print(f"⚠️ [RPC] Correlation ID no encontrado en pending_requests: {correlation_id}")
                            print(f"🔍 [DEBUG] Pending requests: {list(self.pending_requests.keys())}")
                    except Exception as e:
                        print(f"❌ [RPC] Error procesando mensaje: {e}")
                        if correlation_id in self.pending_requests:
                            future_to_resolve = self.pending_requests[correlation_id]
                            if not future_to_resolve.done():
                                future_to_resolve.set_exception(e)

        # Consumir antes de publicar para evitar perder mensajes
        consumer_tag = await reply_queue.consume(on_message)
        
        try:
            await self.publish(
                routing_key, payload, correlation_id=correlation_id, reply_to=reply_queue.name
            )

            try:
                result = await asyncio.wait_for(future, timeout=timeout)
                return result
            except asyncio.TimeoutError:
                print(f"⏱️ [RPC] Timeout de {timeout}s esperando respuesta de '{routing_key}'")
                # Limpiar el consumer
                await reply_queue.cancel(consumer_tag)
                raise
            except Exception as e:
                print(f"❌ [RPC] Error durante la espera: {e}")
                await reply_queue.cancel(consumer_tag)
                raise
                
        finally:
            # Limpieza final garantizada
            self.pending_requests.pop(correlation_id, None)
            self.processed_ids.discard(correlation_id)
            
            # Eliminar la cola de respuesta
            try:
                await reply_queue.delete(if_unused=False, if_empty=False)
                print(f"🧹 [RPC] Cola de respuesta eliminada: {reply_queue.name}")
            except Exception as e:
                print(f"⚠️ [RPC] Error eliminando cola de respuesta: {e}")

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

            async def create_callback(handler_func, pattern_key):
                async def _callback(message: aio_pika.IncomingMessage):
                    async with message.process():
                        try:
                            # Convierte a dict desde el body de RabbitMQ
                            payload_str = message.body.decode()
                            payload_data = json.loads(payload_str)

                            print(f"📩 [Handler:{pattern_key}] Mensaje recibido")
                            
                            # Ejecutar el handler
                            result = await handler_func(payload_data)

                            # Responder vía RPC si es necesario
                            if message.reply_to:
                                reply_msg = aio_pika.Message(
                                    body=json.dumps(result, default=str).encode(),
                                    correlation_id=message.correlation_id,
                                    content_type="application/json",
                                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                                )
                                await self.channel.default_exchange.publish(
                                    reply_msg,
                                    routing_key=message.reply_to
                                )
                                print(f"📬 [Handler:{pattern_key}] Respuesta enviada a: {message.reply_to}")

                        except json.JSONDecodeError as e:
                            print(f"❌ [Handler:{pattern_key}] Error decodificando JSON: {e}")
                            await self._send_error_response(message, f"JSON inválido: {str(e)}")
                        except Exception as e:
                            print(f"❌ [Handler:{pattern_key}] Error: {e}")
                            await self._send_error_response(message, f"Error del handler: {str(e)}")
                
                return _callback

            callback = await create_callback(handler, pattern)
            await queue.consume(callback)
            print(f"🎧 [Broker] Escuchando patrón: {pattern} → {queue_name}")

    async def _send_error_response(self, message: aio_pika.IncomingMessage, error_msg: str):
        """Envía una respuesta de error para solicitudes RPC."""
        if message.reply_to:
            error_response = {
                "success": False, 
                "message": error_msg
            }
            reply_msg = aio_pika.Message(
                body=json.dumps(error_response, default=str).encode(),
                correlation_id=message.correlation_id,
                content_type="application/json"
            )
            try:
                await self.channel.default_exchange.publish(
                    reply_msg,
                    routing_key=message.reply_to
                )
                print(f"📬 [Handler] Respuesta de error enviada: {error_msg}")
            except Exception as e:
                print(f"❌ [Handler] Error enviando respuesta de error: {e}")

    # -----------------------------
    # 🧹 Limpieza
    # -----------------------------
    async def cleanup(self):
        """Limpia todos los recursos pendientes."""
        print("🧹 [Broker] Realizando limpieza...")
        
        # Cancelar todos los futures pendientes
        for corr_id, future in self.pending_requests.items():
            if not future.done():
                future.set_exception(asyncio.CancelledError(f"Cleanup for {corr_id}"))
        
        self.pending_requests.clear()
        self.processed_ids.clear()
        
        await self.close()