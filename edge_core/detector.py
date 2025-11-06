"""
detector.py
Módulo de detección de objetos usando YOLOv8
Detección edge de personas y objetos relevantes
"""

from ultralytics import YOLO
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional


class ObjectDetector:
    """
    Detector de objetos usando YOLOv8
    Optimizado para detección de personas en escenarios de rescate
    """
    
    def __init__(self, model_path: str = "models/yolov8n.pt", conf_threshold: float = 0.4):
        """
        Inicializa el detector YOLOv8
        
        Args:
            model_path: Ruta al modelo YOLOv8
            conf_threshold: Umbral de confianza para detecciones
        """
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        
        # Clases de interés para rescate
        self.rescue_classes = {
            0: 'person',
            1: 'backpack',
            2: 'person_lying',
            67: 'cell_phone'
        }
    
    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Detecta objetos en el frame
        
        Args:
            frame: Frame de video (numpy array BGR)
            
        Returns:
            Lista de detecciones con formato:
            {
                'class': str,
                'conf': float,
                'bbox': [x1, y1, x2, y2],
                'center': (cx, cy)
            }
        """
        # Ejecutar inferencia
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        
        detections = []
        
        for result in results:
            boxes = result.boxes
            
            for box in boxes:
                # Extraer información
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())
                cls = int(box.cls[0].cpu().numpy())
                
                # Calcular centro
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                
                # Obtener nombre de clase
                class_name = result.names[cls]
                
                detection = {
                    'class': class_name,
                    'class_id': cls,
                    'conf': conf,
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'center': (cx, cy),
                    'width': int(x2 - x1),
                    'height': int(y2 - y1)
                }
                
                detections.append(detection)
        
        return detections
    
    def filter_persons(self, detections: List[Dict]) -> List[Dict]:
        """
        Filtra solo detecciones de personas
        
        Args:
            detections: Lista de detecciones
            
        Returns:
            Lista de detecciones de personas
        """
        return [d for d in detections if d['class'] == 'person']
    
    def detect_phone(self, detections: List[Dict]) -> bool:
        """
        Verifica si hay un teléfono móvil detectado
        
        Args:
            detections: Lista de detecciones
            
        Returns:
            True si se detecta un teléfono
        """
        return any(d['class'] == 'cell phone' for d in detections)
    
    def draw_detections(self, frame: np.ndarray, detections: List[Dict], 
                       track_ids: Optional[Dict] = None) -> np.ndarray:
        """
        Dibuja las detecciones en el frame
        
        Args:
            frame: Frame de video
            detections: Lista de detecciones
            track_ids: Diccionario de IDs de tracking (opcional)
            
        Returns:
            Frame con detecciones dibujadas
        """
        output = frame.copy()
        
        for i, det in enumerate(detections):
            x1, y1, x2, y2 = det['bbox']
            conf = det['conf']
            class_name = det['class']
            
            # Color según clase
            if class_name == 'person':
                color = (0, 255, 0)  # Verde para personas
            elif class_name == 'cell phone':
                color = (255, 0, 255)  # Magenta para móviles
            else:
                color = (255, 255, 0)  # Cian para otros
            
            # Dibujar bbox
            cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
            
            # Preparar texto
            if track_ids and i in track_ids:
                label = f"ID:{track_ids[i]} {class_name} {conf:.2f}"
            else:
                label = f"{class_name} {conf:.2f}"
            
            # Fondo para texto
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(output, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            
            # Texto
            cv2.putText(output, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            # Dibujar centro
            cx, cy = det['center']
            cv2.circle(output, (cx, cy), 4, color, -1)
        
        return output
    
    def get_detection_stats(self, detections: List[Dict]) -> Dict:
        """
        Obtiene estadísticas de las detecciones
        
        Args:
            detections: Lista de detecciones
            
        Returns:
            Diccionario con estadísticas
        """
        stats = {
            'total': len(detections),
            'persons': len([d for d in detections if d['class'] == 'person']),
            'has_phone': self.detect_phone(detections),
            'avg_confidence': np.mean([d['conf'] for d in detections]) if detections else 0.0
        }
        
        return stats