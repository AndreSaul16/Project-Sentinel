"""
websocket_client.py
Cliente WebSocket para enviar eventos al dashboard en tiempo real
Comunicación edge-to-dashboard sin conexión a internet
"""

import asyncio
import json
import logging
from typing import Dict, Optional, Callable
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketClient:
    """
    Cliente WebSocket para comunicación con dashboard local
    Maneja reconexión automática y cola de mensajes
    """
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        """
        Inicializa el cliente WebSocket
        
        Args:
            host: Host del servidor WebSocket
            port: Puerto del servidor WebSocket
        """
        self.host = host
        self.port = port
        self.uri = f"ws://{host}:{port}/events"
        self.websocket = None
        self.connected = False
        self.message_queue = []
        self.max_queue_size = 100
        
        # Callback para mensajes recibidos
        self.on_message_callback: Optional[Callable] = None
    
    async def connect(self) -> bool:
        """
        Conecta al servidor WebSocket
        
        Returns:
            True si la conexión fue exitosa
        """
        try:
            self.websocket = await websockets.connect(
                self.uri,
                ping_interval=20,
                ping_timeout=10
            )
            self.connected = True
            logger.info(f"Conectado a WebSocket en {self.uri}")
            
            # Enviar mensajes en cola si hay
            await self._flush_queue()
            
            return True
            
        except Exception as e:
            logger.warning(f"No se pudo conectar a WebSocket: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """
        Desconecta del servidor WebSocket
        """
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            logger.info("Desconectado de WebSocket")
    
    async def send_event(self, event: Dict, retry: bool = True) -> bool:
        """
        Envía un evento al dashboard
        
        Args:
            event: Diccionario del evento
            retry: Si se debe reintentar en caso de error
            
        Returns:
            True si el envío fue exitoso
        """
        try:
            if not self.connected:
                # Intentar reconectar
                if retry:
                    await self.connect()
                
                # Si sigue sin conexión, encolar
                if not self.connected:
                    self._enqueue_message(event)
                    return False
            
            # Convertir a JSON y enviar
            message = json.dumps(event, ensure_ascii=False)
            await self.websocket.send(message)
            logger.info(f"Evento enviado: {event.get('id', 'unknown')}")
            return True
            
        except (ConnectionClosed, WebSocketException) as e:
            logger.error(f"Error al enviar evento: {e}")
            self.connected = False
            
            # Encolar mensaje para reintento
            if retry:
                self._enqueue_message(event)
            
            return False
        
        except Exception as e:
            logger.error(f"Error inesperado al enviar evento: {e}")
            return False
    
    async def receive_message(self, timeout: float = 1.0) -> Optional[Dict]:
        """
        Recibe un mensaje del servidor
        
        Args:
            timeout: Tiempo máximo de espera en segundos
            
        Returns:
            Diccionario con el mensaje o None
        """
        try:
            if not self.connected:
                return None
            
            message = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=timeout
            )
            
            data = json.loads(message)
            logger.info(f"Mensaje recibido: {data.get('type', 'unknown')}")
            
            # Llamar callback si está definido
            if self.on_message_callback:
                self.on_message_callback(data)
            
            return data
            
        except asyncio.TimeoutError:
            return None
        
        except (ConnectionClosed, WebSocketException):
            self.connected = False
            logger.warning("Conexión perdida")
            return None
        
        except Exception as e:
            logger.error(f"Error al recibir mensaje: {e}")
            return None
    
    def _enqueue_message(self, message: Dict):
        """
        Encola un mensaje para envío posterior
        
        Args:
            message: Diccionario del mensaje
        """
        if len(self.message_queue) < self.max_queue_size:
            self.message_queue.append(message)
            logger.info(f"Mensaje encolado. Total en cola: {len(self.message_queue)}")
        else:
            logger.warning("Cola de mensajes llena. Descartando mensaje antiguo.")
            self.message_queue.pop(0)
            self.message_queue.append(message)
    
    async def _flush_queue(self):
        """
        Envía todos los mensajes en cola
        """
        if not self.message_queue:
            return
        
        logger.info(f"Enviando {len(self.message_queue)} mensajes en cola")
        
        while self.message_queue:
            message = self.message_queue.pop(0)
            success = await self.send_event(message, retry=False)
            
            if not success:
                # Devolver a la cola si falla
                self.message_queue.insert(0, message)
                break
            
            # Pequeña pausa entre mensajes
            await asyncio.sleep(0.1)
    
    def set_message_callback(self, callback: Callable):
        """
        Establece un callback para mensajes recibidos
        
        Args:
            callback: Función a llamar cuando se recibe un mensaje
        """
        self.on_message_callback = callback
    
    async def listen_for_responses(self, duration: float = 60.0):
        """
        Escucha respuestas del dashboard por un tiempo determinado
        
        Args:
            duration: Duración máxima de escucha en segundos
        """
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < duration:
            message = await self.receive_message(timeout=1.0)
            
            if message:
                # Procesar respuesta del operador
                if message.get('type') == 'operator_response':
                    logger.info(
                        f"Respuesta del operador: {message.get('action')} "
                        f"para evento {message.get('event_id')}"
                    )
    
    def get_queue_size(self) -> int:
        """
        Obtiene el tamaño actual de la cola
        
        Returns:
            Número de mensajes en cola
        """
        return len(self.message_queue)
    
    def is_connected(self) -> bool:
        """
        Verifica si está conectado
        
        Returns:
            True si hay conexión activa
        """
        return self.connected


async def test_connection(host: str = "localhost", port: int = 8000) -> bool:
    """
    Prueba la conexión al servidor WebSocket
    
    Args:
        host: Host del servidor
        port: Puerto del servidor
        
    Returns:
        True si la conexión es exitosa
    """
    client = WebSocketClient(host, port)
    
    try:
        connected = await client.connect()
        
        if connected:
            # Enviar mensaje de prueba
            test_event = {
                'type': 'test',
                'message': 'Conexión de prueba desde edge system'
            }
            await client.send_event(test_event)
            
            await client.disconnect()
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error en prueba de conexión: {e}")
        return False