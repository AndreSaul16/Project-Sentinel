"""
posture_classifier.py
Clasificador de postura heurístico para personas detectadas
Determina si la persona está de pie, sentada o tumbada
"""

import numpy as np
from typing import Dict, Tuple


class PostureClassifier:
    """
    Clasificador de postura basado en análisis heurístico del bounding box
    Útil para identificar personas en peligro (tumbadas) vs. personas de pie
    """
    
    def __init__(self):
        """
        Inicializa el clasificador con umbrales heurísticos
        """
        # Ratios altura/ancho para diferentes posturas
        self.standing_ratio = 2.0  # Una persona de pie es ~2x más alta que ancha
        self.sitting_ratio = 1.2   # Sentado ~1.2x más alto que ancho
        self.lying_ratio = 0.6     # Tumbado: más ancho que alto
        
        # Tolerancias
        self.tolerance = 0.3
    
    def classify_posture(self, detection: Dict) -> Tuple[str, float]:
        """
        Clasifica la postura de una persona detectada
        
        Args:
            detection: Diccionario de detección con bbox y dimensiones
            
        Returns:
            Tupla (postura, confianza)
            postura: 'de_pie', 'sentado', 'tumbado'
            confianza: 0.0-1.0
        """
        if detection['class'] != 'person':
            return 'desconocido', 0.0
        
        width = detection['width']
        height = detection['height']
        
        # Evitar división por cero
        if width == 0:
            return 'desconocido', 0.0
        
        # Calcular ratio altura/ancho
        aspect_ratio = height / width
        
        # Clasificar según ratio
        if aspect_ratio >= self.standing_ratio - self.tolerance:
            posture = 'de_pie'
            # Confianza basada en qué tan cerca está del ratio ideal
            confidence = min(1.0, aspect_ratio / (self.standing_ratio + 1.0))
            
        elif aspect_ratio >= self.sitting_ratio - self.tolerance:
            posture = 'sentado'
            confidence = 1.0 - abs(aspect_ratio - self.sitting_ratio) / self.sitting_ratio
            
        elif aspect_ratio <= self.lying_ratio + self.tolerance:
            posture = 'tumbado'
            # Alta confianza para personas tumbadas (crítico en rescate)
            confidence = 1.0 - abs(aspect_ratio - self.lying_ratio)
            confidence = max(0.6, min(1.0, confidence))  # Mínimo 0.6 para tumbado
            
        else:
            # Estado intermedio, probablemente agachado o en transición
            posture = 'agachado'
            confidence = 0.5
        
        # Normalizar confianza
        confidence = max(0.3, min(1.0, confidence))
        
        return posture, confidence
    
    def is_lying_down(self, detection: Dict) -> bool:
        """
        Verifica rápidamente si una persona está tumbada (prioridad en rescate)
        
        Args:
            detection: Diccionario de detección
            
        Returns:
            True si la persona está tumbada
        """
        posture, conf = self.classify_posture(detection)
        return posture == 'tumbado' and conf > 0.5
    
    def classify_batch(self, detections: list) -> list:
        """
        Clasifica múltiples detecciones
        
        Args:
            detections: Lista de detecciones
            
        Returns:
            Lista de tuplas (postura, confianza) en el mismo orden
        """
        return [self.classify_posture(det) for det in detections]
    
    def get_risk_level(self, posture: str, confidence: float) -> str:
        """
        Determina el nivel de riesgo basado en la postura
        
        Args:
            posture: Postura detectada
            confidence: Confianza de la detección
            
        Returns:
            Nivel de riesgo: 'alto', 'medio', 'bajo'
        """
        if posture == 'tumbado' and confidence > 0.6:
            return 'alto'
        elif posture == 'sentado':
            return 'medio'
        elif posture == 'de_pie':
            return 'bajo'
        else:
            return 'medio'
    
    def add_posture_info(self, detection: Dict) -> Dict:
        """
        Añade información de postura a una detección
        
        Args:
            detection: Diccionario de detección
            
        Returns:
            Detección con información de postura añadida
        """
        posture, confidence = self.classify_posture(detection)
        risk = self.get_risk_level(posture, confidence)
        
        detection['postura'] = posture
        detection['conf_postura'] = round(confidence, 3)
        detection['riesgo'] = risk
        
        return detection
    
    def get_statistics(self, detections: list) -> Dict:
        """
        Obtiene estadísticas de posturas en un conjunto de detecciones
        
        Args:
            detections: Lista de detecciones
            
        Returns:
            Diccionario con estadísticas
        """
        postures = [self.classify_posture(d)[0] for d in detections if d['class'] == 'person']
        
        stats = {
            'total_personas': len(postures),
            'de_pie': postures.count('de_pie'),
            'sentado': postures.count('sentado'),
            'tumbado': postures.count('tumbado'),
            'agachado': postures.count('agachado'),
            'desconocido': postures.count('desconocido')
        }
        
        # Calcular prioridad de rescate
        stats['prioridad_alta'] = stats['tumbado']
        stats['prioridad_media'] = stats['sentado'] + stats['agachado']
        stats['prioridad_baja'] = stats['de_pie']
        
        return stats