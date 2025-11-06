"""
geo_sim.py
Simulador de geolocalización para dron de rescate
Simula coordenadas GPS con variaciones realistas
"""

import random
from typing import Tuple, Optional


class GeoSimulator:
    """
    Simulador de coordenadas GPS para operaciones de dron
    Genera coordenadas con variaciones aleatorias realistas
    """
    
    def __init__(self, base_lat: float = 40.4168, base_lon: float = -3.7038):
        """
        Inicializa el simulador con coordenadas base
        
        Args:
            base_lat: Latitud base (default: Madrid)
            base_lon: Longitud base (default: Madrid)
        """
        self.base_lat = base_lat
        self.base_lon = base_lon
        
        # Variación máxima en grados (aprox. 100m de radio)
        self.max_variation = 0.001  # ~111 metros por grado de latitud
    
    def get_coordinates(self, add_noise: bool = True) -> Tuple[float, float]:
        """
        Obtiene coordenadas simuladas
        
        Args:
            add_noise: Si se debe añadir ruido aleatorio
            
        Returns:
            Tupla (latitud, longitud)
        """
        if not add_noise:
            return self.base_lat, self.base_lon
        
        # Añadir variación aleatoria pequeña (simula movimiento del dron)
        lat_noise = random.uniform(-self.max_variation, self.max_variation)
        lon_noise = random.uniform(-self.max_variation, self.max_variation)
        
        lat = self.base_lat + lat_noise
        lon = self.base_lon + lon_noise
        
        return round(lat, 6), round(lon, 6)
    
    def set_base_location(self, lat: float, lon: float):
        """
        Actualiza la ubicación base
        
        Args:
            lat: Nueva latitud base
            lon: Nueva longitud base
        """
        self.base_lat = lat
        self.base_lon = lon
    
    def simulate_route(self, num_points: int = 10) -> list:
        """
        Simula una ruta de vuelo del dron
        
        Args:
            num_points: Número de puntos en la ruta
            
        Returns:
            Lista de tuplas (lat, lon)
        """
        route = []
        current_lat = self.base_lat
        current_lon = self.base_lon
        
        for _ in range(num_points):
            # Pequeños incrementos para simular vuelo
            current_lat += random.uniform(-self.max_variation, self.max_variation)
            current_lon += random.uniform(-self.max_variation, self.max_variation)
            
            route.append((round(current_lat, 6), round(current_lon, 6)))
        
        return route
    
    def calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        Calcula distancia aproximada entre dos puntos (método simple)
        
        Args:
            lat1, lon1: Coordenadas del punto 1
            lat2, lon2: Coordenadas del punto 2
            
        Returns:
            Distancia en metros (aproximada)
        """
        # Fórmula simplificada para distancias cortas
        # 1 grado lat ≈ 111km, 1 grado lon ≈ 111km * cos(lat)
        import math
        
        lat_diff = (lat2 - lat1) * 111000  # metros
        lon_diff = (lon2 - lon1) * 111000 * math.cos(math.radians(lat1))
        
        distance = math.sqrt(lat_diff**2 + lon_diff**2)
        return round(distance, 2)
    
    def format_coordinates(self, lat: float, lon: float) -> str:
        """
        Formatea coordenadas para visualización
        
        Args:
            lat: Latitud
            lon: Longitud
            
        Returns:
            String formateado
        """
        lat_dir = 'N' if lat >= 0 else 'S'
        lon_dir = 'E' if lon >= 0 else 'W'
        
        return f"{abs(lat):.6f}°{lat_dir}, {abs(lon):.6f}°{lon_dir}"
    
    def get_location_metadata(self) -> dict:
        """
        Obtiene metadata de ubicación simulada
        
        Returns:
            Diccionario con metadata
        """
        lat, lon = self.get_coordinates()
        
        return {
            'latitude': lat,
            'longitude': lon,
            'altitude': random.randint(50, 150),  # Altura del dron en metros
            'heading': random.randint(0, 359),    # Dirección en grados
            'speed': round(random.uniform(5, 15), 1),  # Velocidad en m/s
            'accuracy': round(random.uniform(2, 5), 1),  # Precisión GPS en metros
            'timestamp': None  # Se añadirá externamente
        }


def get_predefined_locations() -> dict:
    """
    Obtiene diccionario de ubicaciones predefinidas para testing
    
    Returns:
        Diccionario con ubicaciones de ciudades españolas
    """
    return {
        'madrid': (40.4168, -3.7038),
        'barcelona': (41.3874, 2.1686),
        'valencia': (39.4699, -0.3763),
        'sevilla': (37.3891, -5.9845),
        'zaragoza': (41.6488, -0.8891),
        'malaga': (36.7213, -4.4217),
        'bilbao': (43.2630, -2.9350)
    }


def create_geo_simulator(location_name: Optional[str] = None, 
                        custom_lat: Optional[float] = None,
                        custom_lon: Optional[float] = None) -> GeoSimulator:
    """
    Función factory para crear simulador de geo
    
    Args:
        location_name: Nombre de ubicación predefinida
        custom_lat: Latitud personalizada
        custom_lon: Longitud personalizada
        
    Returns:
        Instancia de GeoSimulator
    """
    if custom_lat is not None and custom_lon is not None:
        return GeoSimulator(custom_lat, custom_lon)
    
    if location_name:
        locations = get_predefined_locations()
        if location_name.lower() in locations:
            lat, lon = locations[location_name.lower()]
            return GeoSimulator(lat, lon)
    
    # Default: Madrid
    return GeoSimulator()