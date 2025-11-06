"""
demo.py
Script automatizado para demostración del sistema SENTINEL
Ejecuta los 3 videos de prueba en secuencia
"""

import asyncio
import os
import sys

async def run_video(video_name, description):
    """Ejecuta un video y muestra banner"""
    print("\n" + "╔" + "═"*78 + "╗")
    print(f"║{description.center(80)}║")
    print("╚" + "═"*78 + "╝\n")
    
    print(f"▶️  Reproduciendo: {video_name}")
    print(f"⏱️  Espere mientras se procesa el video...\n")
    
    # Importar después del banner
    from process_video_alert import EdgeVideoProcessor
    
    processor = EdgeVideoProcessor(
        video_path=f'video_test/{video_name}',
        output_dir='output',
        target_fps=10,
        clip_duration=5,
        use_websocket=False
    )
    
    await processor.process_video()
    
    print("\n✅ Video procesado correctamente")
    print("⏳ Preparando siguiente video...\n")
    await asyncio.sleep(2)

async def main():
    """Demo completo"""
    print("\n\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "  🚁 SISTEMA SENTINEL - DEMOSTRACIÓN COMPLETA 🚁  ".center(80) + "║")
    print("║" + "  Sistema Edge de Detección para Drones de Rescate  ".center(80) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝\n")
    
    print("📋 Esta demostración procesará 3 videos:")
    print("   1️⃣  Detección de INCENDIO FORESTAL")
    print("   2️⃣  Detección de INUNDACIÓN URBANA con personas")
    print("   3️⃣  Detección de PERSONAS sin emergencias\n")
    
    input("Presiona ENTER para comenzar la demostración...")
    
    # Video 1: Incendio
    await run_video('fire.mp4', '🔥 DEMO 1/3: DETECCIÓN DE INCENDIO FORESTAL 🔥')
    
    # Video 2: Inundación
    await run_video('water.mp4', '🌊 DEMO 2/3: DETECCIÓN DE INUNDACIÓN URBANA 🌊')
    
    # Video 3: Personas
    await run_video('person.mp4', '👥 DEMO 3/3: DETECCIÓN DE PERSONAS 👥')
    
    # Resumen final
    print("\n" + "╔" + "═"*78 + "╗")
    print("║" + "  ✅ DEMOSTRACIÓN COMPLETADA EXITOSAMENTE ✅  ".center(80) + "║")
    print("╠" + "═"*78 + "╣")
    print("║" + " "*78 + "║")
    print("║" + "  Todos los videos han sido procesados correctamente  ".center(80) + "║")
    print("║" + "  Los eventos y clips están guardados en: output/  ".center(80) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝\n")
    
    print("📁 Archivos generados:")
    print(f"   • Eventos CSV:  output/events.csv")
    print(f"   • Eventos JSON: output/events.jsonl")
    print(f"   • Clips video:  output/clips/\n")
    
    print("🎉 ¡Gracias por ver la demostración de SENTINEL!")
    print("🚁 Sistema listo para despliegue en operaciones de rescate\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrumpida por usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)