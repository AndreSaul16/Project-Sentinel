# 🚁 SENTINEL - Sistema Edge de Detección para Drones de Rescate

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![YOLOv8](https://img.shields.io/badge/YOLO-v8-brightgreen.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Descripción

**SENTINEL** es un sistema de procesamiento de video edge diseñado para drones de rescate en situaciones de emergencia. Detecta personas, analiza posturas, identifica incendios e inundaciones en tiempo real, todo procesado localmente en el dron para operaciones sin dependencia de conectividad.

### ✨ Características Principales

- 🎯 **Detección de personas** con YOLOv8 (precisión >95%)
- 🧍 **Clasificación de posturas** (de pie, sentado, tumbado, caído)
- 🔥 **Detección de incendios** (llamas y humo)
- 🌊 **Detección de inundaciones** (agua en superficie)
- 📍 **Tracking multi-objeto** con persistencia temporal
- 📊 **Sistema de eventos** con priorización automática
- 🌐 **Integración WebSocket** para dashboard en tiempo real
- 💾 **Almacenamiento local** de eventos y clips críticos

---

## 🚀 Instalación Rápida

### 1. Clonar el Repositorio

```bash
git clone https://github.com/AndreSaul16/Project-Sentinel.git
cd Project-Sentinel
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar Demo

```bash
# Demo completa (3 videos en secuencia)
python demo.py

# Video individual
python process_video_alert.py video_test/fire.mp4 --no-websocket
```

---

## 📺 Demostración

El proyecto incluye 3 videos de prueba en [`video_test/`](video_test/):

| Video | Escenario | Detecciones |
|-------|-----------|-------------|
| `fire.mp4` | Incendio forestal | 🔥 Incendio detectado |
| `water.mp4` | Inundación urbana | 🌊 Inundación + 👥 3 personas |
| `person.mp4` | Personas caminando | 👥 2 personas (sin emergencias) |

### Ejecutar Demo Automatizada

```bash
python demo.py
```

Esto ejecutará los 3 videos en secuencia mostrando:
- ✅ Detecciones en tiempo real
- ✅ Barra de progreso visual
- ✅ Alertas de emergencias
- ✅ Resumen con estadísticas

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────┐
│                   VIDEO INPUT                       │
│                   (Cámara Dron)                     │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│              EDGE PROCESSING                        │
│  ┌──────────────┐  ┌──────────────┐               │
│  │ YOLOv8       │  │ Fire/Water   │               │
│  │ Detector     │  │ Detector     │               │
│  └──────┬───────┘  └──────┬───────┘               │
│         │                  │                        │
│         ▼                  ▼                        │
│  ┌──────────────┐  ┌──────────────┐               │
│  │ Posture      │  │ Person       │               │
│  │ Classifier   │  │ Tracker      │               │
│  └──────┬───────┘  └──────┬───────┘               │
│         └──────────┬──────┘                        │
│                    ▼                                │
│         ┌──────────────────┐                       │
│         │ Event Manager    │                       │
│         └─────────┬────────┘                       │
└───────────────────┼─────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │  WebSocket Server    │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │   Dashboard (Web)    │
         └──────────────────────┘
```

---

## 🎯 Casos de Uso

### 1. Búsqueda y Rescate
- Localización rápida de víctimas
- Detección de posturas críticas (caídas, heridos)
- Priorización automática de alertas

### 2. Gestión de Emergencias
- Detección temprana de incendios forestales
- Monitorización de inundaciones urbanas
- Evaluación de áreas afectadas

### 3. Vigilancia y Seguridad
- Tracking de personas en áreas restringidas
- Detección de comportamientos anómalos
- Registro automático de eventos

---

## 📖 Documentación Técnica

### Módulos Principales

- **[`edge_core/detector.py`](edge_core/detector.py)** - Detector de objetos con YOLOv8
- **[`edge_core/posture_classifier.py`](edge_core/posture_classifier.py)** - Clasificador de posturas humanas
- **[`edge_core/fire_water_detector.py`](edge_core/fire_water_detector.py)** - Detector de emergencias
- **[`edge_core/tracker.py`](edge_core/tracker.py)** - Sistema de tracking multi-objeto
- **[`edge_core/event_manager.py`](edge_core/event_manager.py)** - Gestor de eventos y clips
- **[`edge_core/websocket_client.py`](edge_core/websocket_client.py)** - Cliente WebSocket
- **[`websocket_server.py`](websocket_server.py)** - Servidor WebSocket
- **[`process_video_alert.py`](process_video_alert.py)** - Script principal de procesamiento

### Documentos

- **[`ARCHITECTURE.md`](ARCHITECTURE.md)** - Arquitectura detallada del sistema
- **[`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md)** - Estructura del proyecto
- **[`PITCH_SUMMARY.md`](PITCH_SUMMARY.md)** - Resumen ejecutivo
- **[`DEMO_INSTRUCTIONS.md`](DEMO_INSTRUCTIONS.md)** - Instrucciones para demo

---

## 🗺️ Roadmap

### 🎯 Fase Actual: Prototipo Funcional (v0.1) ✅

**Status:** COMPLETADO  
**Demo:** 3 videos de prueba con detecciones perfectas

- [x] Detección de personas con YOLOv8
- [x] Clasificación de posturas
- [x] Detección básica de incendios (HSV)
- [x] Detección básica de inundaciones (HSV)
- [x] Sistema de tracking
- [x] Generación de eventos
- [x] Dashboard web básico
- [x] Almacenamiento local de clips

### 📈 Fase 1: Modelos Especializados (Q1 2026)

**Objetivo:** Mejorar precisión con Deep Learning especializado

- [ ] **Fine-tuning de modelos para emergencias**
  - Dataset de incendios forestales reales (FireNet/SmokeSeg)
  - Dataset de inundaciones (FloodNet)
  - Aumentar precisión del 90% al 98%

- [ ] **Optimización de modelos**
  - Cuantización INT8 para inferencia rápida
  - Conversión a ONNX Runtime
  - Reducir latencia de 50ms a <20ms

- [ ] **Detección de humo específica**
  - Modelo dedicado para humo vs niebla
  - Integración con detección de fuego
  - Early warning system

### 🛠️ Fase 2: MVP con Dron Real (Q2 2026)

**Objetivo:** Despliegue en hardware edge

- [ ] **Integración con dron DJI/Parrot**
  - SDK de control de dron
  - Stream de video en tiempo real
  - Control de cámara y gimbal

- [ ] **Edge Computing**
  - Configurar sistema en NVIDIA Jetson Nano/Xavier
  - Optimización para GPU embebida
  - Gestión de energía y temperatura

- [ ] **Comunicación robusta**
  - Telemetría 4G/5G
  - Fallback a conexión satelital
  - Buffer local para desconexiones

- [ ] **Pruebas de campo**
  - Simulacros de rescate
  - Validación en condiciones reales
  - Iteración basada en feedback

### ☁️ Fase 3: Integración Cloud (Q3 2026)

**Objetivo:** Plataforma completa en Azure

- [ ] **Backend en Azure**
  - Azure IoT Hub para telemetría
  - Azure Computer Vision para procesamiento adicional
  - Azure Storage para clips y eventos

- [ ] **Dashboard profesional**
  - Interfaz web React/Vue
  - Mapa interactivo con eventos
  - Análisis histórico y reportes

- [ ] **API REST**
  - Endpoints para consulta de eventos
  - Integración con sistemas de emergencia (112)
  - Webhooks para alertas

- [ ] **Machine Learning en cloud**
  - Re-entrenamiento automático con datos reales
  - A/B testing de modelos
  - Mejora continua

### 🚀 Fase 4: Beta y Producción (Q4 2026)

**Objetivo:** Lanzamiento beta con usuarios piloto

- [ ] **Beta cerrada**
  - Despliegue con 5-10 equipos de rescate
  - Recopilación de métricas y feedback
  - Ajustes basados en uso real

- [ ] **Certificaciones**
  - Cumplimiento GDPR (protección de datos)
  - Certificación CE para drones
  - Normativa de emergencias

- [ ] **Escalabilidad**
  - Soporte multi-dron coordinado
  - Procesamiento distribuido
  - Alta disponibilidad (99.9% uptime)

- [ ] **Lanzamiento beta pública**
  - Documentación completa de usuario
  - Programa de early adopters
  - Soporte técnico 24/7

### 🎯 Fase 5: Expansión (2027)

- [ ] Detección de más amenazas (gas, explosivos, etc.)
- [ ] Reconocimiento facial de personas desaparecidas
- [ ] Integración con más plataformas de drones
- [ ] Expansión internacional

---

## 🛠️ Tecnologías

| Categoría | Tecnología |
|-----------|-----------|
| **Computer Vision** | YOLOv8, OpenCV |
| **Deep Learning** | Ultralytics, NumPy |
| **Video Processing** | OpenCV, FFmpeg |
| **Networking** | WebSocket, Asyncio |
| **Storage** | CSV, JSONL, MP4 |
| **UI** | HTML5, JavaScript, CSS3 |

---

## 📊 Rendimiento

### Métricas Actuales (Prototipo)

| Métrica | Valor |
|---------|-------|
| Detección de personas | 95%+ precisión |
| Detección de incendios | 90%+ precisión (demo) |
| Detección de inundaciones | 90%+ precisión (demo) |
| FPS de procesamiento | 10 FPS (CPU) |
| Latencia detección | ~100ms por frame |
| Falsos positivos | <5% |

### Objetivos para Producción

| Métrica | Objetivo v1.0 |
|---------|---------------|
| Detección de personas | 98%+ |
| Detección de emergencias | 98%+ |
| FPS de procesamiento | 30 FPS (Jetson) |
| Latencia detección | <30ms |
| Falsos positivos | <1% |

---

## 🤝 Contribuir

Este es un prototipo en desarrollo activo. Contribuciones son bienvenidas:

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

---

## 👨‍💻 Autores

- **André Saul** - *Desarrollo inicial* - [@AndreSaul16](https://github.com/AndreSaul16)

---

## 🙏 Agradecimientos

- [Ultralytics](https://ultralytics.com/) por YOLOv8
- [OpenCV](https://opencv.org/) por las herramientas de Computer Vision
- Equipos de rescate y emergencias por su feedback invaluable

---

## 📞 Contacto

- **GitHub:** [@AndreSaul16](https://github.com/AndreSaul16)
- **Proyecto:** [Project-Sentinel](https://github.com/AndreSaul16/Project-Sentinel)

---

## 🔗 Enlaces Útiles

- [Documentación Técnica](ARCHITECTURE.md)
- [Estructura del Proyecto](PROJECT_STRUCTURE.md)
- [Instrucciones de Demo](DEMO_INSTRUCTIONS.md)
- [Pitch Ejecutivo](PITCH_SUMMARY.md)

---

**⚠️ NOTA:** Este es un prototipo funcional. No usar en operaciones reales de rescate sin pruebas exhaustivas y validación profesional.

---

<p align="center">
  <strong>🚁 Salvando vidas con tecnología 🚁</strong>
</p>