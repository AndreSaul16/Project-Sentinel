"""
event_manager.py
Gestor de eventos inteligentes para el sistema edge
Crea, almacena y gestiona eventos de emergencia con metadata completa
"""

import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Optional
import uuid


class EventManager:
    """
    Gestor centralizado de eventos de emergencia
    Maneja creación, almacenamiento y exportación de eventos
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Inicializa el gestor de eventos
        
        Args:
            output_dir: Directorio base para guardar eventos y clips
        """
        self.output_dir = output_dir
        self.clips_dir = os.path.join(output_dir, "clips")
        self.csv_path = os.path.join(output_dir, "events.csv")
        self.jsonl_path = os.path.join(output_dir, "events.jsonl")
        
        # Crear directorios si no existen
        os.makedirs(self.clips_dir, exist_ok=True)
        
        # Lista de eventos en memoria
        self.events = []
        
        # Inicializar archivos CSV
        self._init_csv()
    
    def _init_csv(self):
        """
        Inicializa el archivo CSV con cabeceras
        """
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'id', 'tipo', 'postura', 'conf_postura', 'estado',
                    'conf_estado', 'count_people', 'lat', 'lon',
                    'timestamp', 'clip_path', 'fire_detected', 'water_detected',
                    'fire_confidence', 'water_confidence', 'priority'
                ])
    
    def create_event(self, 
                    tipo: str,
                    postura: str = "desconocido",
                    conf_postura: float = 0.0,
                    estado: str = "desconocido",
                    conf_estado: float = 0.0,
                    count_people: int = 0,
                    lat: float = 0.0,
                    lon: float = 0.0,
                    clip_path: Optional[str] = None,
                    fire_detected: bool = False,
                    water_detected: bool = False,
                    fire_confidence: float = 0.0,
                    water_confidence: float = 0.0,
                    extra_data: Optional[Dict] = None) -> Dict:
        """
        Crea un nuevo evento de emergencia
        
        Args:
            tipo: Tipo de evento ('persona', 'incendio', 'inundacion')
            postura: Postura de la persona
            conf_postura: Confianza de la postura
            estado: Estado (con_movil, desconocido)
            conf_estado: Confianza del estado
            count_people: Número de personas detectadas
            lat: Latitud
            lon: Longitud
            clip_path: Ruta al clip de video
            fire_detected: Si se detectó fuego
            water_detected: Si se detectó agua
            fire_confidence: Confianza de detección de fuego
            water_confidence: Confianza de detección de agua
            extra_data: Datos adicionales
            
        Returns:
            Diccionario con el evento creado
        """
        # Generar ID único
        timestamp = datetime.utcnow()
        event_id = f"evt_{timestamp.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Determinar prioridad
        priority = self._calculate_priority(
            tipo, postura, fire_detected, water_detected
        )
        
        # Crear evento
        event = {
            'id': event_id,
            'tipo': tipo,
            'postura': postura,
            'conf_postura': round(conf_postura, 3),
            'estado': estado,
            'conf_estado': round(conf_estado, 3),
            'count_people': count_people,
            'lat': round(lat, 6),
            'lon': round(lon, 6),
            'timestamp': timestamp.isoformat() + 'Z',
            'clip_path': clip_path if clip_path else "",
            'fire_detected': fire_detected,
            'water_detected': water_detected,
            'fire_confidence': round(fire_confidence, 3),
            'water_confidence': round(water_confidence, 3),
            'priority': priority
        }
        
        # Añadir datos extra si existen
        if extra_data:
            event.update(extra_data)
        
        # Guardar en memoria
        self.events.append(event)
        
        # Guardar en archivos
        self._save_to_csv(event)
        self._save_to_jsonl(event)
        
        return event
    
    def _calculate_priority(self, tipo: str, postura: str, 
                           fire_detected: bool, water_detected: bool) -> str:
        """
        Calcula la prioridad del evento
        
        Args:
            tipo: Tipo de evento
            postura: Postura de la persona
            fire_detected: Si hay fuego
            water_detected: Si hay agua
            
        Returns:
            Nivel de prioridad: 'critica', 'alta', 'media', 'baja'
        """
        # Máxima prioridad: fuego + agua o persona tumbada con emergencias
        if (fire_detected and water_detected) or \
           (postura == 'tumbado' and (fire_detected or water_detected)):
            return 'critica'
        
        # Alta prioridad: emergencias o persona en riesgo
        if fire_detected or water_detected or postura == 'tumbado':
            return 'alta'
        
        # Media prioridad: persona en postura de riesgo medio
        if postura in ['sentado', 'agachado']:
            return 'media'
        
        # Baja prioridad: resto de casos
        return 'baja'
    
    def _save_to_csv(self, event: Dict):
        """
        Guarda evento en archivo CSV
        
        Args:
            event: Diccionario del evento
        """
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                event['id'],
                event['tipo'],
                event['postura'],
                event['conf_postura'],
                event['estado'],
                event['conf_estado'],
                event['count_people'],
                event['lat'],
                event['lon'],
                event['timestamp'],
                event['clip_path'],
                event['fire_detected'],
                event['water_detected'],
                event['fire_confidence'],
                event['water_confidence'],
                event['priority']
            ])
    
    def _save_to_jsonl(self, event: Dict):
        """
        Guarda evento en archivo JSONL
        
        Args:
            event: Diccionario del evento
        """
        with open(self.jsonl_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
    
    def get_clip_path(self, event_id: str) -> str:
        """
        Obtiene la ruta para guardar el clip de un evento
        
        Args:
            event_id: ID del evento
            
        Returns:
            Ruta relativa del clip
        """
        clip_filename = f"{event_id}.mp4"
        return os.path.join(self.clips_dir, clip_filename)
    
    def get_all_events(self) -> List[Dict]:
        """
        Obtiene todos los eventos en memoria
        
        Returns:
            Lista de eventos
        """
        return self.events.copy()
    
    def get_events_by_type(self, tipo: str) -> List[Dict]:
        """
        Obtiene eventos filtrados por tipo
        
        Args:
            tipo: Tipo de evento
            
        Returns:
            Lista de eventos del tipo especificado
        """
        return [e for e in self.events if e['tipo'] == tipo]
    
    def get_events_by_priority(self, priority: str) -> List[Dict]:
        """
        Obtiene eventos filtrados por prioridad
        
        Args:
            priority: Nivel de prioridad
            
        Returns:
            Lista de eventos con esa prioridad
        """
        return [e for e in self.events if e['priority'] == priority]
    
    def get_statistics(self) -> Dict:
        """
        Obtiene estadísticas de los eventos
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.events:
            return {
                'total': 0,
                'by_type': {},
                'by_priority': {},
                'with_fire': 0,
                'with_water': 0,
                'avg_people': 0
            }
        
        stats = {
            'total': len(self.events),
            'by_type': {},
            'by_priority': {},
            'with_fire': sum(1 for e in self.events if e['fire_detected']),
            'with_water': sum(1 for e in self.events if e['water_detected']),
            'avg_people': sum(e['count_people'] for e in self.events) / len(self.events)
        }
        
        # Contar por tipo
        for event in self.events:
            tipo = event['tipo']
            stats['by_type'][tipo] = stats['by_type'].get(tipo, 0) + 1
            
            priority = event['priority']
            stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
        
        return stats
    
    def export_summary(self, output_path: Optional[str] = None) -> str:
        """
        Exporta un resumen de todos los eventos
        
        Args:
            output_path: Ruta de salida (opcional)
            
        Returns:
            Ruta del archivo creado
        """
        if output_path is None:
            output_path = os.path.join(self.output_dir, "events_summary.json")
        
        summary = {
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'statistics': self.get_statistics(),
            'events': self.events
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def clear_events(self):
        """
        Limpia todos los eventos en memoria
        """
        self.events.clear()