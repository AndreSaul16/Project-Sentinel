# 🏗️ Arquitectura del Sistema Edge de Dron de Rescate

## Visión General

Este documento describe la arquitectura técnica del sistema edge de procesamiento de video para drones de rescate. El sistema está diseñado siguiendo principios de **Clean Architecture** y **Clean Code**.

## Principios de Diseño

### Clean Architecture

```
┌─────────────────────────────────────────────────┐
│                   UI Layer                      │
│              (Dashboard Web)                    │
├─────────────────────────────────────────────────┤
│              Interface Layer                    │
│     (WebSocket Client/Server, CLI)             │
├─────────────────────────────────────────────────┤
│            Application Layer                    │
│        (EdgeVideoProcessor)                     │
├─────────────────────────────────────────────────┤
│              Domain Layer                       │
│  (Detector, Tracker, Classifier, EventManager) │
├─────────────────────────────────────────────────┤
│           Infrastructure Layer                  │
│      (OpenCV, YOLOv8, File System)            │
└─────────────────────────────────────────────────┘
```

### Dependencias

- **Regla de dependencia**: Las capas internas NO dependen de las externas
- **Inversión de control**: Las interfaces están en capas superiores
- **Abstracción**: Cada capa se comunica mediante contratos definidos

## Componentes Principales

### 1. Edge Core (Domain Layer)

#### detector.py - ObjectDetector
**Responsabilidad**: Detección de objetos usando YOLOv8

```python
Entradas:
- Frame de video (numpy array)
- Umbral de confianza

Salidas:
- Lista de detecciones con bbox, clase, confianza

Dependencias:
- ultralytics.YOLO
- OpenCV
- NumPy
```

**Patrón**: Strategy Pattern para diferentes modelos de detección

#### posture_classifier.py - PostureClassifier
**Responsabilidad**: Clasificación heurística de postura

```python
Entradas:
- Detección con dimensiones (width, height)

Salidas:
- Postura clasificada
- Nivel de confianza

Algoritmo:
- Análisis de ratio altura/ancho
- Reglas heurísticas basadas en umbrales
```

**Patrón**: Strategy Pattern + Template Method

#### fire_water_detector.py - FireWaterDetector
**Responsabilidad**: Detección de emergencias por color

```python
Entradas:
- Frame RGB

Salidas:
- Detección de fuego (bool + confianza)
- Detección de agua (bool + confianza)
- Máscaras HSV

Algoritmo:
- Conversión RGB -> HSV
- Máscaras de rango de color
- Operaciones morfológicas
- Análisis de distribución
```

**Patrón**: Template Method + Strategy

#### tracker.py - PersonTracker
**Responsabilidad**: Tracking multi-objeto con IDs persistentes

```python
Entradas:
- Lista de detecciones actuales

Salidas:
- Detecciones con IDs persistentes
- Información de tracking

Algoritmo:
- Cálculo de distancia de centroides
- Asociación Hungarian (implícita)
- Gestión de apariciones/desapariciones
```

**Patrón**: Observer Pattern + State Machine

#### event_manager.py - EventManager
**Responsabilidad**: Gestión centralizada de eventos

```python
Responsabilidades:
- Crear eventos con metadata
- Calcular prioridad
- Guardar en CSV/JSONL
- Gestionar clips de video

Salidas:
- Eventos estructurados (JSON)
- Archivos persistentes
```

**Patrón**: Repository Pattern + Factory Pattern

#### geo_sim.py - GeoSimulator
**Responsabilidad**: Simulación de geolocalización

```python
Funcionalidad:
- Coordenadas base configurables
- Ruido aleatorio para realismo
- Ubicaciones predefinidas
- Cálculo de distancias
```

**Patrón**: Singleton (para instancia global) + Factory

### 2. Application Layer

#### process_video_alert.py - EdgeVideoProcessor
**Responsabilidad**: Orquestación del pipeline completo

```python
Pipeline:
1. Leer frame de video
2. Detectar objetos (YOLOv8)
3. Clasificar posturas
4. Detectar emergencias
5. Actualizar tracking
6. Generar eventos si necesario
7. Guardar clips
8. Enviar a dashboard

Estado:
- Buffer circular de frames
- Contadores de eventos
- Referencias a detectores
```

**Patrón**: Facade Pattern + Chain of Responsibility

### 3. Interface Layer

#### websocket_client.py - WebSocketClient
**Responsabilidad**: Cliente WebSocket para envío de eventos

```python
Funcionalidades:
- Conexión asíncrona
- Reconexión automática
- Cola de mensajes
- Callbacks para respuestas
```

**Patrón**: Observer Pattern + Retry Pattern

#### websocket_server.py - DashboardWebSocketServer
**Responsabilidad**: Servidor WebSocket para dashboard

```python
Funcionalidades:
- Gestión de múltiples clientes
- Broadcasting de eventos
- Recepción de respuestas
- Estadísticas
```

**Patrón**: Publisher-Subscriber + Mediator

### 4. Presentation Layer

#### Dashboard (HTML/JS/CSS)
**Responsabilidad**: UI para operador

```javascript
Componentes:
- EventsList: Lista de eventos
- MapView: Visualización geográfica
- EventDetails: Panel de detalles
- WebSocketManager: Comunicación

Estado:
- Lista de eventos
- Evento seleccionado
- Filtros activos
- Marcadores del mapa
```

**Patrón**: MVC (Model-View-Controller)

## Flujo de Datos

### Procesamiento de Video

```
Video File
    ↓
[Frame Reader] (OpenCV)
    ↓
[Frame Buffer] (Circular Queue)
    ↓
[Object Detection] (YOLOv8) ──→ [Persons]
    ↓                              ↓
[Fire/Water Detection] ──→ [Hazards]
    ↓                              ↓
[Person Tracking] ←────────────────┘
    ↓
[Event Generation]
    ↓
├──→ [Clip Saver] ──→ [File System]
├──→ [Event Manager] ──→ [CSV/JSONL]
└──→ [WebSocket Client] ──→ [Server] ──→ [Dashboard]
```

### Comunicación WebSocket

```
Edge System              Server              Dashboard
    │                      │                      │
    │───── connect() ─────→│                      │
    │                      │←──── connect() ──────│
    │                      │                      │
    │─── send(event) ─────→│                      │
    │                      │─── broadcast() ─────→│
    │                      │                      │
    │                      │←── response() ───────│
    │←─── forward() ───────│                      │
```

## Patrones de Diseño Aplicados

### 1. Creacionales

- **Factory Pattern**: `create_geo_simulator()`
- **Builder Pattern**: Construcción de eventos con metadata
- **Singleton Pattern**: Instancias únicas de gestores

### 2. Estructurales

- **Facade Pattern**: `EdgeVideoProcessor` simplifica complejidad
- **Adapter Pattern**: Adaptación de YOLOv8 a interfaz propia
- **Composite Pattern**: Agregación de detecciones

### 3. Comportamiento

- **Strategy Pattern**: Diferentes estrategias de detección
- **Observer Pattern**: WebSocket notificaciones
- **Chain of Responsibility**: Pipeline de procesamiento
- **Template Method**: Estructura común de detectores
- **State Pattern**: Estados del tracker

## Principios SOLID

### Single Responsibility Principle (SRP)
✅ Cada clase tiene una única responsabilidad:
- `ObjectDetector`: Solo detección
- `PostureClassifier`: Solo clasificación
- `EventManager`: Solo gestión de eventos

### Open/Closed Principle (OCP)
✅ Extensible sin modificar código existente:
- Nuevos detectores heredan de clase base
- Configuración externa en lugar de hardcoded

### Liskov Substitution Principle (LSP)
✅ Subtipos intercambiables:
- Diferentes modelos YOLO son intercambiables
- Simuladores GPS intercambiables

### Interface Segregation Principle (ISP)
✅ Interfaces específicas:
- Métodos públicos mínimos y específicos
- No fuerza implementación de métodos no usados

### Dependency Inversion Principle (DIP)
✅ Depende de abstracciones:
- No depende de implementaciones concretas
- Inyección de dependencias en constructores

## Gestión de Estado

### Estado del Sistema

```python
EdgeVideoProcessor:
    - frame_buffer: deque (circular)
    - frame_count: int
    - events_generated: int
    - ws_client: WebSocketClient

PersonTracker:
    - objects: OrderedDict (ID -> centroid)
    - disappeared: OrderedDict (ID -> frames)
    - frame_count: OrderedDict (ID -> total frames)

EventManager:
    - events: List[Dict] (en memoria)
    - archivos: CSV + JSONL (persistentes)
```

### Gestión de Concurrencia

```python
AsyncIO:
- WebSocket usa asyncio para operaciones no bloqueantes
- Procesamiento de video en thread principal
- Buffer circular thread-safe (deque)
```

## Manejo de Errores

### Estrategia de Resiliencia

1. **Graceful Degradation**
   - Si WebSocket falla → continuar sin dashboard
   - Si YOLOv8 falla → registrar error y continuar
   - Si clip falla → registrar evento sin clip

2. **Retry Pattern**
   - WebSocket reconexión automática
   - Cola de mensajes para reintentos

3. **Circuit Breaker**
   - Límite de reintentos de conexión
   - Fallback a modo offline

## Performance y Optimización

### Estrategias Implementadas

1. **Frame Skipping**
   - Procesar cada N frames según FPS objetivo
   - Reduce carga computacional

2. **Buffer Circular**
   - Tamaño fijo para clips
   - Memoria acotada

3. **Lazy Loading**
   - YOLOv8 se carga una vez
   - Reutilización de recursos

4. **Batch Processing**
   - Detecciones en batch cuando posible
   - Reduce overhead

### Métricas Esperadas

- **FPS**: 10-15 frames/segundo
- **Latencia**: < 100ms por frame
- **Memoria**: < 2GB RAM
- **CPU**: 50-70% en i7 moderno

## Seguridad

### Consideraciones

1. **Validación de Entrada**
   - Validar rutas de archivo
   - Sanitizar nombres de archivo

2. **Autenticación**
   - WebSocket sin autenticación (local)
   - Agregar JWT para producción

3. **Datos Sensibles**
   - Coordenadas GPS pueden ser sensibles
   - Clips de video requieren gestión segura

## Escalabilidad

### Horizontal

```python
# Múltiples instancias procesando diferentes streams
instances = [
    EdgeVideoProcessor(video1, output1),
    EdgeVideoProcessor(video2, output2),
    EdgeVideoProcessor(video3, output3)
]

# Servidor WebSocket único recibe todos los eventos
```

### Vertical

```python
# GPU para YOLOv8
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = YOLO(model_path).to(device)

# Multi-threading para I/O
thread_pool = ThreadPoolExecutor(max_workers=4)
```

## Testing

### Estrategia de Testing

1. **Unit Tests**
   - Cada componente edge_core/
   - Mocks para dependencias externas

2. **Integration Tests**
   - Pipeline completo con video de prueba
   - WebSocket comunicación

3. **End-to-End Tests**
   - Sistema completo funcionando
   - Dashboard + Backend + Processing

## Deployment

### Configuración de Producción

```python
Recomendaciones:
- Docker container para portabilidad
- Volúmenes para output/
- Variables de entorno para config
- Logging estructurado
- Monitoring con Prometheus
```

## Documentación de Código

### Convenciones

- **Docstrings**: Google Style
- **Type Hints**: Python 3.8+
- **Comments**: Solo para lógica compleja
- **README**: Documentación de usuario

## Conclusión

Este sistema demuestra:
- ✅ Arquitectura limpia y mantenible
- ✅ Separación de responsabilidades
- ✅ Código testeable y extensible
- ✅ Performance optimizado para edge
- ✅ Resiliencia ante fallos
- ✅ Documentación completa

El sistema está **production-ready** para demostraciones y puede ser extendido para deployment real con modificaciones mínimas en seguridad y escalabilidad.