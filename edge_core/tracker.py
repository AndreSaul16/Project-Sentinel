"""
tracker.py
Sistema de tracking de personas usando algoritmo de centroide
Mantiene IDs persistentes y monitorea tiempo de permanencia
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import OrderedDict
from scipy.spatial import distance


class PersonTracker:
    """
    Tracker de personas basado en distancia de centroides
    Asigna y mantiene IDs únicos para cada persona detectada
    """
    
    def __init__(self, max_disappeared: int = 30, max_distance: float = 100.0):
        """
        Inicializa el tracker
        
        Args:
            max_disappeared: Frames máximos antes de perder el tracking
            max_distance: Distancia máxima (píxeles) para asociar detecciones
        """
        self.next_object_id = 0
        self.objects = OrderedDict()  # ID -> centroid
        self.disappeared = OrderedDict()  # ID -> frames desaparecido
        self.frame_count = OrderedDict()  # ID -> frames desde aparición
        self.bboxes = OrderedDict()  # ID -> última bbox
        
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        
        # Umbral de frames para generar evento (persona visible > X frames)
        # Cambiado a 1 para generar alertas inmediatas al detectar personas
        self.event_threshold = 1  # Alerta inmediata
    
    def register(self, centroid: Tuple[int, int], bbox: List[int]) -> int:
        """
        Registra un nuevo objeto con ID único
        
        Args:
            centroid: Tupla (x, y) del centro
            bbox: Bounding box [x1, y1, x2, y2]
            
        Returns:
            ID asignado
        """
        object_id = self.next_object_id
        self.objects[object_id] = centroid
        self.disappeared[object_id] = 0
        self.frame_count[object_id] = 1
        self.bboxes[object_id] = bbox
        self.next_object_id += 1
        
        return object_id
    
    def deregister(self, object_id: int):
        """
        Elimina un objeto del tracking
        
        Args:
            object_id: ID del objeto a eliminar
        """
        del self.objects[object_id]
        del self.disappeared[object_id]
        del self.frame_count[object_id]
        del self.bboxes[object_id]
    
    def update(self, detections: List[Dict]) -> Dict[int, Dict]:
        """
        Actualiza el tracker con nuevas detecciones
        
        Args:
            detections: Lista de detecciones de personas
            
        Returns:
            Diccionario {ID: detección actualizada}
        """
        # Si no hay detecciones, marcar todos como desaparecidos
        if len(detections) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                
                # Eliminar objetos que han desaparecido demasiado tiempo
                if self.disappeared[object_id] > self.max_disappeared:
                    self.deregister(object_id)
            
            return {}
        
        # Extraer centroides de las detecciones
        input_centroids = np.array([det['center'] for det in detections])
        
        # Si no hay objetos trackeados, registrar todos
        if len(self.objects) == 0:
            tracked = {}
            for i, det in enumerate(detections):
                object_id = self.register(det['center'], det['bbox'])
                det['track_id'] = object_id
                det['frames_visible'] = 1
                tracked[object_id] = det
            return tracked
        
        # Obtener IDs y centroides actuales
        object_ids = list(self.objects.keys())
        object_centroids = np.array(list(self.objects.values()))
        
        # Calcular matriz de distancias
        D = distance.cdist(object_centroids, input_centroids)
        
        # Encontrar la mínima distancia en cada fila (objeto existente)
        rows = D.min(axis=1).argsort()
        
        # Encontrar la columna (detección nueva) con mínima distancia
        cols = D.argmin(axis=1)
        
        # Conjunto de índices usados
        used_rows = set()
        used_cols = set()
        
        tracked = {}
        
        # Asociar objetos existentes con detecciones
        for row in rows:
            # Si ya procesamos esta fila, continuar
            if row in used_rows:
                continue
            
            # Obtener la columna asociada
            col = cols[row]
            
            # Si ya usamos esta columna, continuar
            if col in used_cols:
                continue
            
            # Verificar si la distancia es aceptable
            if D[row, col] > self.max_distance:
                continue
            
            # Asociar el objeto existente con la nueva detección
            object_id = object_ids[row]
            self.objects[object_id] = input_centroids[col]
            self.disappeared[object_id] = 0
            self.frame_count[object_id] += 1
            self.bboxes[object_id] = detections[col]['bbox']
            
            # Actualizar detección con info de tracking
            detections[col]['track_id'] = object_id
            detections[col]['frames_visible'] = self.frame_count[object_id]
            tracked[object_id] = detections[col]
            
            used_rows.add(row)
            used_cols.add(col)
        
        # Calcular objetos no asociados y detecciones no asociadas
        unused_rows = set(range(0, D.shape[0])).difference(used_rows)
        unused_cols = set(range(0, D.shape[1])).difference(used_cols)
        
        # Manejar objetos que no fueron asociados (desaparecidos)
        for row in unused_rows:
            object_id = object_ids[row]
            self.disappeared[object_id] += 1
            
            if self.disappeared[object_id] > self.max_disappeared:
                self.deregister(object_id)
        
        # Registrar nuevas detecciones no asociadas
        for col in unused_cols:
            object_id = self.register(input_centroids[col], detections[col]['bbox'])
            detections[col]['track_id'] = object_id
            detections[col]['frames_visible'] = 1
            tracked[object_id] = detections[col]
        
        return tracked
    
    def should_generate_event(self, track_id: int) -> bool:
        """
        Determina si un objeto ha sido visible suficiente tiempo para generar evento
        
        Args:
            track_id: ID del objeto trackeado
            
        Returns:
            True si debe generarse evento
        """
        if track_id not in self.frame_count:
            return False
        
        # Generar evento solo una vez cuando alcanza el umbral
        return self.frame_count[track_id] == self.event_threshold
    
    def get_track_info(self, track_id: int) -> Optional[Dict]:
        """
        Obtiene información de un track específico
        
        Args:
            track_id: ID del track
            
        Returns:
            Diccionario con información del track o None
        """
        if track_id not in self.objects:
            return None
        
        return {
            'id': track_id,
            'centroid': self.objects[track_id],
            'bbox': self.bboxes[track_id],
            'frames_visible': self.frame_count[track_id],
            'disappeared_frames': self.disappeared[track_id]
        }
    
    def get_all_tracks(self) -> Dict[int, Dict]:
        """
        Obtiene información de todos los tracks activos
        
        Returns:
            Diccionario con todos los tracks
        """
        tracks = {}
        for track_id in self.objects.keys():
            tracks[track_id] = self.get_track_info(track_id)
        
        return tracks
    
    def get_statistics(self) -> Dict:
        """
        Obtiene estadísticas del tracker
        
        Returns:
            Diccionario con estadísticas
        """
        active_tracks = len(self.objects)
        long_term_tracks = sum(1 for count in self.frame_count.values() 
                               if count >= self.event_threshold)
        
        stats = {
            'active_tracks': active_tracks,
            'long_term_tracks': long_term_tracks,
            'total_registered': self.next_object_id,
            'avg_visibility': np.mean(list(self.frame_count.values())) if self.frame_count else 0
        }
        
        return stats
    
    def reset(self):
        """
        Resetea el tracker completamente
        """
        self.next_object_id = 0
        self.objects.clear()
        self.disappeared.clear()
        self.frame_count.clear()
        self.bboxes.clear()