"""
process_video_alert.py
Script principal del sistema edge de procesamiento de video para dron de rescate
Integra detección, tracking, clasificación y alertas en tiempo real
"""

import cv2
import numpy as np
import argparse
import asyncio
import sys
import os
from collections import deque
from datetime import datetime

# Importar módulos edge
from edge_core.detector import ObjectDetector
from edge_core.posture_classifier import PostureClassifier
from edge_core.fire_water_detector import FireWaterDetector
from edge_core.tracker import PersonTracker
from edge_core.event_manager import EventManager
from edge_core.geo_sim import create_geo_simulator
from edge_core.websocket_client import WebSocketClient


class EdgeVideoProcessor:
    """
    Procesador principal de vídeo edge para dron de rescate
    Integra todos los módulos de detección y alerta
    """
    
    def __init__(self, 
                 video_path: str,
                 output_dir: str = "output",
                 target_fps: int = 10,
                 clip_duration: int = 5,
                 use_websocket: bool = True,
                 websocket_host: str = "localhost",
                 websocket_port: int = 8000,
                 base_lat: float = 40.4168,
                 base_lon: float = -3.7038):
        """
        Inicializa el procesador de vídeo edge
        
        Args:
            video_path: Ruta al vídeo de entrada
            output_dir: Directorio de salida
            target_fps: FPS objetivo de procesamiento
            clip_duration: Duración de clips en segundos
            use_websocket: Si usar WebSocket para dashboard
            websocket_host: Host del servidor WebSocket
            websocket_port: Puerto del servidor WebSocket
            base_lat: Latitud base
            base_lon: Longitud base
        """
        self.video_path = video_path
        self.output_dir = output_dir
        self.target_fps = target_fps
        self.clip_duration = clip_duration
        self.use_websocket = use_websocket
        
        # Crear directorios
        os.makedirs(output_dir, exist_ok=True)
        
        # Inicializar módulos
        print("🚁 Inicializando sistema edge...")
        self.detector = ObjectDetector(conf_threshold=0.4)
        self.posture_classifier = PostureClassifier()
        self.fire_water_detector = FireWaterDetector()
        self.tracker = PersonTracker(max_disappeared=30)
        self.event_manager = EventManager(output_dir)
        self.geo_sim = create_geo_simulator(custom_lat=base_lat, custom_lon=base_lon)
        
        # WebSocket (opcional)
        self.ws_client = None
        if use_websocket:
            self.ws_client = WebSocketClient(websocket_host, websocket_port)
        
        # Buffer circular para clips
        self.frame_buffer = deque(maxlen=clip_duration * target_fps)
        
        # Estado
        self.frame_count = 0
        self.events_generated = 0
        
        print("✅ Sistema edge inicializado correctamente")
    
    async def process_video(self):
        """
        Procesa el vídeo completo
        """
        # Conectar WebSocket si está habilitado
        if self.ws_client:
            print("🔌 Intentando conectar a dashboard WebSocket...")
            await self.ws_client.connect()
            if self.ws_client.is_connected():
                print("✅ Conectado a dashboard")
            else:
                print("⚠️  No se pudo conectar a dashboard (continuando sin WebSocket)")
        
        # Abrir vídeo
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            print(f"❌ Error: No se pudo abrir el vídeo {self.video_path}")
            return
        
        # Obtener propiedades del vídeo
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"\n📹 Información del vídeo:")
        print(f"   • Resolución: {video_width}x{video_height}")
        print(f"   • FPS original: {video_fps:.2f}")
        print(f"   • Frames totales: {total_frames}")
        print(f"   • FPS procesamiento: {self.target_fps}")
        
        # Calcular skip de frames
        frame_skip = max(1, int(video_fps / self.target_fps))
        
        print(f"\n╔{'═'*58}╗")
        print(f"║{'  🎬 INICIANDO PROCESAMIENTO EDGE - DRON RESCATE  ':^60}║")
        print(f"╚{'═'*58}╝\n")
        print(f"⌨️  Presiona 'q' en la ventana de video para detener\n")
        
        try:
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                self.frame_count += 1
                
                # Procesar solo cada N frames
                if self.frame_count % frame_skip != 0:
                    continue
                
                # Añadir frame al buffer
                self.frame_buffer.append(frame.copy())
                
                # Procesar frame
                await self.process_frame(frame, video_fps)
                
                # Mostrar progreso actualizado
                progress = (self.frame_count / total_frames) * 100
                bar_length = 40
                filled_length = int(bar_length * self.frame_count // total_frames)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                print(f"\r🔄 [{bar}] {progress:.1f}% | Frame {self.frame_count}/{total_frames} | Eventos: {self.events_generated}  ", end="", flush=True)
                
                # Actualizar ventana de visualización
                cv2.imshow('Edge Processing - Dron Rescate', self.visualization_frame)
                
                # Control de teclado
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\n\n⏹️  Detenido por usuario")
                    break
        
        finally:
            # Limpieza
            cap.release()
            cv2.destroyAllWindows()
            
            if self.ws_client:
                await self.ws_client.disconnect()
            
            # Resumen final
            self.print_summary()
    
    async def process_frame(self, frame: np.ndarray, video_fps: float):
        """
        Procesa un frame individual
        
        Args:
            frame: Frame a procesar
            video_fps: FPS del vídeo original
        """
        # 1. Detectar objetos (personas)
        detections = self.detector.detect(frame)
        persons = self.detector.filter_persons(detections)
        
        # 2. Clasificar posturas
        for person in persons:
            self.posture_classifier.add_posture_info(person)
        
        # 3. Detectar móviles (estado)
        has_phone = self.detector.detect_phone(detections)
        
        # 4. Detectar incendio e inundación
        hazard_result = self.fire_water_detector.detect_all(frame)
        fire_detected = hazard_result['fire']['detected']
        fire_conf = hazard_result['fire']['confidence']
        water_detected = hazard_result['water']['detected']
        water_conf = hazard_result['water']['confidence']
        
        # 5. Tracking de personas
        tracked_persons = self.tracker.update(persons)
        
        # 6. Generar eventos si es necesario
        await self.generate_events(
            tracked_persons, 
            has_phone,
            fire_detected, fire_conf,
            water_detected, water_conf
        )
        
        # 7. Crear visualización
        self.create_visualization(
            frame, 
            list(tracked_persons.values()), 
            hazard_result
        )
    
    async def generate_events(self, 
                            tracked_persons: dict,
                            has_phone: bool,
                            fire_detected: bool, fire_conf: float,
                            water_detected: bool, water_conf: float):
        """
        Genera eventos basados en detecciones
        
        Args:
            tracked_persons: Diccionario de personas trackeadas
            has_phone: Si se detectó móvil
            fire_detected: Si hay incendio
            fire_conf: Confianza de incendio
            water_detected: Si hay inundación
            water_conf: Confianza de inundación
        """
        # Obtener coordenadas
        lat, lon = self.geo_sim.get_coordinates(add_noise=True)
        
        # Evento por persona que supera el umbral de permanencia
        for track_id, person in tracked_persons.items():
            if self.tracker.should_generate_event(track_id):
                await self.create_person_event(
                    person, has_phone, lat, lon,
                    fire_detected, fire_conf, water_detected, water_conf
                )
        
        # Evento de incendio (generar solo una vez cuando se detecta por primera vez)
        if fire_detected and not hasattr(self, '_fire_event_created'):
            await self.create_hazard_event(
                'incendio', fire_conf, lat, lon, len(tracked_persons)
            )
            self._fire_event_created = True
        
        # Resetear flag si ya no hay fuego
        if not fire_detected and hasattr(self, '_fire_event_created'):
            delattr(self, '_fire_event_created')
        
        # Evento de inundación
        if water_detected and not hasattr(self, '_water_event_created'):
            await self.create_hazard_event(
                'inundacion', water_conf, lat, lon, len(tracked_persons)
            )
            self._water_event_created = True
        
        if not water_detected and hasattr(self, '_water_event_created'):
            delattr(self, '_water_event_created')
    
    async def create_person_event(self, 
                                 person: dict,
                                 has_phone: bool,
                                 lat: float, lon: float,
                                 fire_detected: bool, fire_conf: float,
                                 water_detected: bool, water_conf: float):
        """
        Crea un evento de persona detectada
        """
        # Guardar clip
        clip_path = await self.save_clip(f"person_{person['track_id']}")
        
        # Crear evento
        event = self.event_manager.create_event(
            tipo='persona',
            postura=person.get('postura', 'desconocido'),
            conf_postura=person.get('conf_postura', 0.0),
            estado='con_movil' if has_phone else 'desconocido',
            conf_estado=0.8 if has_phone else 0.3,
            count_people=1,
            lat=lat,
            lon=lon,
            clip_path=clip_path,
            fire_detected=fire_detected,
            water_detected=water_detected,
            fire_confidence=fire_conf,
            water_confidence=water_conf,
            extra_data={
                'track_id': person['track_id'],
                'frames_visible': person['frames_visible'],
                'bbox': person['bbox'],
                'riesgo': person.get('riesgo', 'medio')
            }
        )
        
        self.events_generated += 1
        
        # Enviar por WebSocket
        if self.ws_client and self.ws_client.is_connected():
            await self.ws_client.send_event(event)
        
        track_id = event.get('extra_data', {}).get('track_id', 'N/A')
        print(f"\n\n┌─────────────────────────────────────────────────────┐")
        print(f"│ 👤 PERSONA DETECTADA                               │")
        print(f"├─────────────────────────────────────────────────────┤")
        print(f"│ ID Evento:  {event['id']:<38}│")
        print(f"│ Track ID:   {track_id:<38}│")
        print(f"│ Postura:    {event['postura']:<28} ({event['conf_postura']:.2f}) │")
        print(f"│ Prioridad:  {event['priority'].upper():<38}│")
        print(f"│ GPS:        {lat:.4f}, {lon:.4f}{' '*15}│")
        print(f"└─────────────────────────────────────────────────────┘")
    
    async def create_hazard_event(self, 
                                 tipo: str,
                                 confidence: float,
                                 lat: float, lon: float,
                                 people_count: int):
        """
        Crea un evento de emergencia (fuego/agua)
        """
        # Guardar clip
        clip_path = await self.save_clip(tipo)
        
        # Crear evento
        event = self.event_manager.create_event(
            tipo=tipo,
            conf_postura=confidence,
            count_people=people_count,
            lat=lat,
            lon=lon,
            clip_path=clip_path,
            fire_detected=(tipo == 'incendio'),
            water_detected=(tipo == 'inundacion'),
            fire_confidence=confidence if tipo == 'incendio' else 0.0,
            water_confidence=confidence if tipo == 'inundacion' else 0.0
        )
        
        self.events_generated += 1
        
        # Enviar por WebSocket
        if self.ws_client and self.ws_client.is_connected():
            await self.ws_client.send_event(event)
        
        emoji = "🔥" if tipo == 'incendio' else "🌊"
        border_char = "═" if tipo == 'incendio' else "─"
        
        print(f"\n\n╔{border_char*57}╗")
        print(f"║ {emoji} ¡EMERGENCIA DETECTADA! - {tipo.upper():<28}║")
        print(f"╠{border_char*57}╣")
        print(f"║ ID Evento:  {event['id']:<40}║")
        print(f"║ Tipo:       {tipo.upper():<40}║")
        print(f"║ Confianza:  {confidence:.2f} ({int(confidence*100)}%){' '*28}║")
        print(f"║ Prioridad:  {event['priority'].upper():<40}║")
        print(f"║ Personas:   {people_count} en zona de emergencia{' '*20}║")
        print(f"║ GPS:        {lat:.4f}, {lon:.4f}{' '*23}║")
        print(f"╚{border_char*57}╝")
    
    async def save_clip(self, event_prefix: str) -> str:
        """
        Guarda clip del buffer circular Y snapshot (imagen)
        
        Args:
            event_prefix: Prefijo para el nombre del clip
            
        Returns:
            Ruta relativa del clip guardado
        """
        # Generar timestamp único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        
        # 1. GUARDAR SNAPSHOT (imagen del frame actual) - SIEMPRE
        if len(self.frame_buffer) > 0:
            snapshot_filename = f"{event_prefix}_{timestamp}.jpg"
            snapshot_path = os.path.join(self.event_manager.clips_dir, snapshot_filename)
            
            # Tomar el último frame (más reciente)
            current_frame = list(self.frame_buffer)[-1]
            cv2.imwrite(snapshot_path, current_frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        
        # 2. GUARDAR CLIP de video si hay suficientes frames (mínimo 3 frames = ~0.3 seg)
        if len(self.frame_buffer) >= 3:
            clip_filename = f"{event_prefix}_{timestamp}.mp4"
            clip_path = os.path.join(self.event_manager.clips_dir, clip_filename)
            
            # Obtener frames del buffer
            frames_to_save = list(self.frame_buffer)
            
            if frames_to_save:
                # Propiedades del vídeo
                height, width = frames_to_save[0].shape[:2]
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(clip_path, fourcc, self.target_fps, (width, height))
                
                # Escribir frames
                for frame in frames_to_save:
                    out.write(frame)
                
                out.release()
                
                return os.path.relpath(clip_path)
        
        # Si no hay clip, devolver ruta del snapshot
        return os.path.relpath(snapshot_path) if len(self.frame_buffer) > 0 else ""
    
    def create_visualization(self, 
                           frame: np.ndarray,
                           persons: list,
                           hazard_result: dict):
        """
        Crea frame de visualización con todas las detecciones
        
        Args:
            frame: Frame original
            persons: Lista de personas detectadas
            hazard_result: Resultado de detección de emergencias
        """
        vis_frame = frame.copy()
        
        # Dibujar detecciones de personas
        if persons:
            vis_frame = self.detector.draw_detections(
                vis_frame, 
                persons,
                {i: p['track_id'] for i, p in enumerate(persons)}
            )
        
        # Añadir alertas de emergencia
        fire_detected = hazard_result['fire']['detected']
        fire_conf = hazard_result['fire']['confidence']
        water_detected = hazard_result['water']['detected']
        water_conf = hazard_result['water']['confidence']
        
        vis_frame = self.fire_water_detector.add_alerts_to_frame(
            vis_frame, fire_detected, fire_conf, water_detected, water_conf
        )
        
        # Añadir overlay de información
        self.add_info_overlay(vis_frame, len(persons), hazard_result)
        
        self.visualization_frame = vis_frame
    
    def add_info_overlay(self, frame: np.ndarray, person_count: int, hazard_result: dict):
        """
        Añade overlay de información del sistema
        """
        h, w = frame.shape[:2]
        
        # Panel de información
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, h - 150), (400, h - 10), (0, 0, 0), -1)
        frame_blend = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
        
        # Información
        y_pos = h - 130
        cv2.putText(frame_blend, "EDGE SYSTEM - DRON RESCATE", (20, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        y_pos += 25
        cv2.putText(frame_blend, f"Personas: {person_count}", (20, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        y_pos += 25
        cv2.putText(frame_blend, f"Eventos generados: {self.events_generated}", (20, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        y_pos += 25
        status_color = (0, 255, 0) if self.ws_client and self.ws_client.is_connected() else (0, 0, 255)
        status_text = "CONECTADO" if self.ws_client and self.ws_client.is_connected() else "SIN CONEXION"
        cv2.putText(frame_blend, f"Dashboard: {status_text}", (20, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
        
        y_pos += 25
        lat, lon = self.geo_sim.get_coordinates(add_noise=False)
        cv2.putText(frame_blend, f"GPS: {lat:.4f}, {lon:.4f}", (20, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        frame[:] = frame_blend[:]
    
    def print_summary(self):
        """
        Imprime resumen final del procesamiento
        """
        stats = self.event_manager.get_statistics()
        
        print("\n\n╔" + "═"*58 + "╗")
        print("║" + "  📊 RESUMEN FINAL DEL PROCESAMIENTO EDGE  ".center(60) + "║")
        print("╠" + "═"*58 + "╣")
        print(f"║ ✅ Frames procesados:        {self.frame_count:<27}║")
        print(f"║ 🚨 Eventos generados:        {self.events_generated:<27}║")
        print(f"║ 👥 Personas detectadas:      {stats.get('by_type', {}).get('persona', 0):<27}║")
        print(f"║ 🔥 Incendios detectados:     {stats.get('with_fire', 0):<27}║")
        print(f"║ 💧 Inundaciones detectadas:  {stats.get('with_water', 0):<27}║")
        print("╠" + "─"*58 + "╣")
        print(f"║ 📁 Archivos generados:                                   ║")
        print(f"║    • CSV:   {os.path.basename(self.event_manager.csv_path):<43}║")
        print(f"║    • JSONL: {os.path.basename(self.event_manager.jsonl_path):<43}║")
        print(f"║    • Clips: {os.path.basename(self.event_manager.clips_dir):<43}║")
        print("╚" + "═"*58 + "╝\n")


async def main():
    """
    Función principal
    """
    parser = argparse.ArgumentParser(
        description='Sistema Edge de Procesamiento de Video para Dron de Rescate'
    )
    parser.add_argument('video', type=str, help='Ruta al archivo de video')
    parser.add_argument('--output', type=str, default='output', 
                       help='Directorio de salida (default: output)')
    parser.add_argument('--fps', type=int, default=10, 
                       help='FPS de procesamiento (default: 10)')
    parser.add_argument('--clip-duration', type=int, default=5, 
                       help='Duración de clips en segundos (default: 5)')
    parser.add_argument('--no-websocket', action='store_true',
                       help='Desactivar conexión WebSocket')
    parser.add_argument('--ws-host', type=str, default='localhost',
                       help='Host del servidor WebSocket (default: localhost)')
    parser.add_argument('--ws-port', type=int, default=8000,
                       help='Puerto del servidor WebSocket (default: 8000)')
    parser.add_argument('--lat', type=float, default=40.4168,
                       help='Latitud base (default: Madrid 40.4168)')
    parser.add_argument('--lon', type=float, default=-3.7038,
                       help='Longitud base (default: Madrid -3.7038)')
    
    args = parser.parse_args()
    
    # Verificar que el vídeo existe
    if not os.path.exists(args.video):
        print(f"❌ Error: El archivo de vídeo no existe: {args.video}")
        sys.exit(1)
    
    # Crear procesador
    processor = EdgeVideoProcessor(
        video_path=args.video,
        output_dir=args.output,
        target_fps=args.fps,
        clip_duration=args.clip_duration,
        use_websocket=not args.no_websocket,
        websocket_host=args.ws_host,
        websocket_port=args.ws_port,
        base_lat=args.lat,
        base_lon=args.lon
    )
    
    # Procesar vídeo
    await processor.process_video()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Procesamiento interrumpido por usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)