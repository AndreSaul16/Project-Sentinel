#!/bin/bash
# Quick Start Script para Sistema Edge Dron de Rescate
# Linux/Mac Bash Script

echo "===================================="
echo "SISTEMA EDGE DRON DE RESCATE"
echo "Quick Start Menu"
echo "===================================="
echo ""

show_menu() {
    echo "Selecciona una opción:"
    echo ""
    echo "1. Instalar dependencias"
    echo "2. Iniciar servidor WebSocket"
    echo "3. Iniciar dashboard (navegador)"
    echo "4. Procesar video (ejemplo)"
    echo "5. Modo completo (servidor + dashboard)"
    echo "6. Salir"
    echo ""
    read -p "Opción (1-6): " option
    
    case $option in
        1) install_deps ;;
        2) start_websocket ;;
        3) open_dashboard ;;
        4) process_video ;;
        5) full_mode ;;
        6) exit 0 ;;
        *) echo "Opción inválida"; show_menu ;;
    esac
}

install_deps() {
    echo ""
    echo "[1/2] Instalando dependencias..."
    pip install -r requirements.txt
    echo ""
    echo "[2/2] Instalación completada!"
    echo ""
    read -p "Presiona Enter para continuar..."
    show_menu
}

start_websocket() {
    echo ""
    echo "Iniciando servidor WebSocket en ws://localhost:8000"
    echo "Presiona Ctrl+C para detener"
    echo ""
    python3 websocket_server.py
    show_menu
}

open_dashboard() {
    echo ""
    echo "Abriendo dashboard en navegador..."
    
    # Detectar sistema operativo y abrir navegador
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Mac
        open dashboard/index.html
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        xdg-open dashboard/index.html 2>/dev/null || \
        python3 -m http.server 8080 --directory dashboard &
        sleep 2
        xdg-open http://localhost:8080 2>/dev/null
    fi
    
    echo "Dashboard abierto!"
    echo ""
    read -p "Presiona Enter para continuar..."
    show_menu
}

process_video() {
    echo ""
    read -p "Ruta del video a procesar: " video
    
    if [ -z "$video" ]; then
        echo "Error: Debes especificar un video"
        read -p "Presiona Enter para continuar..."
        show_menu
        return
    fi
    
    echo ""
    echo "Procesando $video..."
    python3 process_video_alert.py "$video"
    echo ""
    read -p "Presiona Enter para continuar..."
    show_menu
}

full_mode() {
    echo ""
    echo "Iniciando modo completo..."
    echo "1. Servidor WebSocket se iniciará en segundo plano"
    echo "2. Dashboard se abrirá en tu navegador"
    echo ""
    
    # Iniciar servidor WebSocket en background
    python3 websocket_server.py > /dev/null 2>&1 &
    WS_PID=$!
    echo "Servidor WebSocket iniciado (PID: $WS_PID)"
    
    sleep 2
    
    # Abrir dashboard
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open dashboard/index.html
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open dashboard/index.html 2>/dev/null
    fi
    
    echo ""
    echo "Sistema iniciado!"
    echo "Ahora puedes procesar un video."
    echo ""
    read -p "Ruta del video a procesar (Enter para volver): " video
    
    if [ ! -z "$video" ]; then
        python3 process_video_alert.py "$video"
    fi
    
    # Matar servidor WebSocket
    kill $WS_PID 2>/dev/null
    show_menu
}

# Hacer ejecutable el script
chmod +x "$0" 2>/dev/null

# Mostrar menú
show_menu