"""
websocket_server.py
Servidor WebSocket local para dashboard de operador
Recibe eventos del sistema edge y retransmite respuestas
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Set
import websockets
from websockets.server import WebSocketServerProtocol


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DashboardWebSocketServer:
    """
    Servidor WebSocket para comunicación edge-dashboard
    Maneja múltiples conexiones y broadcasting de eventos
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Inicializa el servidor WebSocket
        
        Args:
            host: Host del servidor
            port: Puerto del servidor
        """
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.events_received = 0
        self.responses_sent = 0
    
    async def register_client(self, websocket: WebSocketServerProtocol):
        """
        Registra un nuevo cliente conectado
        
        Args:
            websocket: Cliente WebSocket
        """
        self.clients.add(websocket)
        logger.info(f"Cliente conectado. Total clientes: {len(self.clients)}")
        
        # Enviar mensaje de bienvenida
        welcome_msg = {
            'type': 'connection',
            'status': 'connected',
            'message': 'Conectado a servidor edge',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        await websocket.send(json.dumps(welcome_msg))
    
    async def unregister_client(self, websocket: WebSocketServerProtocol):
        """
        Desregistra un cliente desconectado
        
        Args:
            websocket: Cliente WebSocket
        """
        self.clients.remove(websocket)
        logger.info(f"Cliente desconectado. Total clientes: {len(self.clients)}")
    
    async def broadcast_event(self, event: dict, exclude: WebSocketServerProtocol = None):
        """
        Envía un evento a todos los clientes conectados
        
        Args:
            event: Evento a enviar
            exclude: Cliente a excluir del broadcast (opcional)
        """
        if not self.clients:
            logger.warning("No hay clientes conectados para broadcast")
            return
        
        message = json.dumps(event, ensure_ascii=False)
        
        # Enviar a todos los clientes excepto el excluido
        tasks = []
        for client in self.clients:
            if client != exclude:
                tasks.append(client.send(message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Evento broadcast a {len(tasks)} clientes: {event.get('id', 'unknown')}")
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """
        Maneja la conexión de un cliente
        
        Args:
            websocket: Cliente WebSocket
            path: Ruta de conexión
        """
        await self.register_client(websocket)
        
        try:
            async for message in websocket:
                await self.process_message(message, websocket)
        
        except websockets.exceptions.ConnectionClosed:
            logger.info("Conexión cerrada normalmente")
        
        except Exception as e:
            logger.error(f"Error en cliente: {e}")
        
        finally:
            await self.unregister_client(websocket)
    
    async def process_message(self, message: str, websocket: WebSocketServerProtocol):
        """
        Procesa un mensaje recibido
        
        Args:
            message: Mensaje JSON
            websocket: Cliente que envió el mensaje
        """
        try:
            data = json.loads(message)
            msg_type = data.get('type', 'unknown')
            
            logger.info(f"Mensaje recibido: {msg_type}")
            
            # Evento del sistema edge
            if msg_type in ['persona', 'incendio', 'inundacion'] or 'tipo' in data:
                self.events_received += 1
                # Broadcast a todos los dashboards
                await self.broadcast_event(data, exclude=websocket)
                
                # Confirmar recepción al emisor
                ack = {
                    'type': 'ack',
                    'event_id': data.get('id', 'unknown'),
                    'status': 'received',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
                await websocket.send(json.dumps(ack))
            
            # Respuesta del operador (confirmar/rechazar)
            elif msg_type == 'operator_response':
                self.responses_sent += 1
                # Broadcast la respuesta a todos (incluyendo sistema edge)
                await self.broadcast_event(data)
                
                logger.info(
                    f"Respuesta del operador: {data.get('action')} "
                    f"para evento {data.get('event_id')}"
                )
            
            # Ping/heartbeat
            elif msg_type == 'ping':
                pong = {
                    'type': 'pong',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
                await websocket.send(json.dumps(pong))
            
            # Test/diagnóstico
            elif msg_type == 'test':
                response = {
                    'type': 'test_response',
                    'status': 'ok',
                    'server': 'Edge Dashboard Server',
                    'clients_connected': len(self.clients),
                    'events_received': self.events_received,
                    'responses_sent': self.responses_sent,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
                await websocket.send(json.dumps(response))
            
            # Solicitud de estadísticas
            elif msg_type == 'get_stats':
                stats = {
                    'type': 'stats',
                    'clients_connected': len(self.clients),
                    'events_received': self.events_received,
                    'responses_sent': self.responses_sent,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }
                await websocket.send(json.dumps(stats))
            
            else:
                logger.warning(f"Tipo de mensaje desconocido: {msg_type}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON: {e}")
            error_msg = {
                'type': 'error',
                'message': 'JSON inválido',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            await websocket.send(json.dumps(error_msg))
        
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
    
    async def start(self):
        """
        Inicia el servidor WebSocket
        """
        logger.info(f"🚀 Iniciando servidor WebSocket en ws://{self.host}:{self.port}")
        
        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        ):
            logger.info("✅ Servidor WebSocket activo")
            logger.info(f"   • Endpoint: ws://{self.host}:{self.port}/events")
            logger.info(f"   • Esperando conexiones...")
            logger.info(f"   • Presiona Ctrl+C para detener\n")
            
            # Mantener el servidor corriendo
            await asyncio.Future()  # run forever
    
    def get_stats(self) -> dict:
        """
        Obtiene estadísticas del servidor
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'clients_connected': len(self.clients),
            'events_received': self.events_received,
            'responses_sent': self.responses_sent
        }


async def main():
    """
    Función principal
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Servidor WebSocket para Dashboard de Dron de Rescate'
    )
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Host del servidor (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000,
                       help='Puerto del servidor (default: 8000)')
    
    args = parser.parse_args()
    
    # Crear y arrancar servidor
    server = DashboardWebSocketServer(host=args.host, port=args.port)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Servidor detenido por usuario")
        stats = server.get_stats()
        logger.info(f"\n📊 Estadísticas finales:")
        logger.info(f"   • Eventos recibidos: {stats['events_received']}")
        logger.info(f"   • Respuestas enviadas: {stats['responses_sent']}")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())