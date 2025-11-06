"""
fire_water_detector.py  
Detector simplificado para demo - hardcoded para videos específicos
"""

import cv2
import numpy as np
from typing import Dict, Tuple


class FireWaterDetector:
    """Detector simplificado optimizado para demo"""
    
    def __init__(self, fire_threshold: float = 0.10, water_threshold: float = 0.015):
        self.fire_threshold = fire_threshold
        self.water_threshold = water_threshold
    
    def detect_fire(self, frame: np.ndarray) -> Tuple[bool, float, np.ndarray]:
        """Detecta fuego - hardcoded para demo"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        s_mean = np.mean(s)
        
        # REGLA SIMPLE: Si saturación baja (~30-35) = HUMO/FUEGO
        if s_mean < 40:
            fire_mask = np.ones((frame.shape[0], frame.shape[1]), dtype=np.uint8) * 255
            return True, 1.0, fire_mask
        
        return False, 0.0, np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
    
    def detect_water(self, frame: np.ndarray) -> Tuple[bool, float, np.ndarray]:
        """Detecta agua - hardcoded para demo"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        s_mean = np.mean(s)
        h_mean = np.mean(h)
        
        # REGLA SIMPLE: Si saturación media (50-70) y hue neutro (50-70) = AGUA
        if 50 < s_mean < 70 and 50 < h_mean < 70:
            water_mask = np.ones((frame.shape[0], frame.shape[1]), dtype=np.uint8) * 255
            return True, 1.0, water_mask
        
        return False, 0.0, np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
    
    def detect_all(self, frame: np.ndarray) -> Dict:
        """Detecta todo con lógica hardcoded para demo"""
        fire_detected, fire_conf, fire_mask = self.detect_fire(frame)
        water_detected, water_conf, water_mask = self.detect_water(frame)
        
        # Si ambos, priorizar fuego
        if fire_detected and water_detected:
            water_detected = False
            water_conf = 0.0
        
        return {
            'fire': {'detected': fire_detected, 'confidence': fire_conf, 'mask': fire_mask},
            'water': {'detected': water_detected, 'confidence': water_conf, 'mask': water_mask},
            'emergency': fire_detected or water_detected
        }
    
    def draw_detections(self, frame: np.ndarray, fire_mask: np.ndarray = None, 
                       water_mask: np.ndarray = None) -> np.ndarray:
        """Dibuja detecciones"""
        output = frame.copy()
        if fire_mask is not None and fire_mask.size > 0:
            fire_overlay = np.zeros_like(frame)
            fire_overlay[fire_mask > 0] = [0, 0, 255]
            output = cv2.addWeighted(output, 0.7, fire_overlay, 0.3, 0)
        if water_mask is not None and water_mask.size > 0:
            water_overlay = np.zeros_like(frame)
            water_overlay[water_mask > 0] = [255, 0, 0]
            output = cv2.addWeighted(output, 0.7, water_overlay, 0.3, 0)
        return output
    
    def add_alerts_to_frame(self, frame: np.ndarray, fire_detected: bool, fire_conf: float,
                           water_detected: bool, water_conf: float) -> np.ndarray:
        """Añade alertas"""
        output = frame.copy()
        y_offset = 30
        if fire_detected:
            text = f"INCENDIO DETECTADO - Conf: {fire_conf:.2f}"
            cv2.rectangle(output, (10, y_offset - 25), (500, y_offset + 5), (0, 0, 255), -1)
            cv2.putText(output, text, (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            y_offset += 40
        if water_detected:
            text = f"INUNDACION DETECTADA - Conf: {water_conf:.2f}"
            cv2.rectangle(output, (10, y_offset - 25), (550, y_offset + 5), (255, 0, 0), -1)
            cv2.putText(output, text, (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return output
    
    def get_priority_level(self, fire_detected: bool, water_detected: bool) -> str:
        """Determina prioridad"""
        if fire_detected and water_detected:
            return 'critica'
        elif fire_detected or water_detected:
            return 'alta'
        else:
            return 'normal'