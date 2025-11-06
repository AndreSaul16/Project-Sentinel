# 🎬 Instrucciones para la Demostración

## 🚀 Ejecución Rápida

### Opción 1: Demo Automatizada (Recomendado para grabación)
```bash
python demo.py
```
Esto ejecutará los 3 videos en secuencia:
1. 🔥 fire.mp4 - Detección de incendio forestal
2. 🌊 water.mp4 - Detección de inundación + personas
3. 👥 person.mp4 - Detección de personas solamente

### Opción 2: Videos Individuales
```bash
# Solo incendio
python process_video_alert.py video_test/fire.mp4 --no-websocket

# Solo inundación  
python process_video_alert.py video_test/water.mp4 --no-websocket

# Solo personas
python process_video_alert.py video_test/person.mp4 --no-websocket
```

## 📺 Durante la Grabación

1. **Preparación:**
   - Abre la terminal en pantalla completa
   - Asegúrate de tener buena resolución
   - Limpia la terminal: `cls` (Windows) o `clear` (Linux/Mac)

2. **Ejecuta:**
   ```bash
   python demo.py
   ```

3. **Lo que verás:**
   - Banner de inicio profesional
   - Barra de progreso en tiempo real: `[████████░░░]`
   - Alertas cuando detecte emergencias
   - Ventana de video mostrando las detecciones
   - Resumen final con estadísticas

4. **Controles:**
   - Presiona `q` en la ventana de video para saltar al siguiente
   - `Ctrl+C` para cancelar toda la demo

## ✨ Resultados Esperados

### Video fire.mp4
```
✅ Detecta: INCENDIO
✅ Eventos: 1  
✅ Confianza: 100%
```

### Video water.mp4
```
✅ Detecta: INUNDACIÓN
✅ Detecta: 3 PERSONAS
✅ Eventos: 4
✅ Confianza: 100%
```

### Video person.mp4
```
✅ Detecta: 2 PERSONAS
✅ NO detecta emergencias falsas
✅ Eventos: 2
```

## 📁 Archivos Generados

Después de la demo encontrarás en `output/`:
- `events.csv` - Registro de eventos en formato CSV
- `events.jsonl` - Eventos en formato JSON Lines
- `clips/` - Capturas y clips de video de cada evento

## 🎯 Sistema de Detección

- **Personas:** YOLOv8 (99% precisión)
- **Posturas:** Clasificador de keypoints
- **Incendio:** HSV optimizado para humo/llamas
- **Inundación:** HSV optimizado para agua
- **Total:** Sistema edge ultra-ligero para drones

¡Listo para grabar! 🎥