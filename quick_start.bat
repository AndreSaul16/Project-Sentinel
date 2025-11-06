@echo off
REM Quick Start Script para Sistema Edge Dron de Rescate
REM Windows Batch Script

echo ====================================
echo SISTEMA EDGE DRON DE RESCATE
echo Quick Start Menu
echo ====================================
echo.

:menu
echo Selecciona una opcion:
echo.
echo 1. Instalar dependencias
echo 2. Iniciar servidor WebSocket
echo 3. Iniciar dashboard (navegador)
echo 4. Procesar video (ejemplo)
echo 5. Modo completo (servidor + dashboard)
echo 6. Salir
echo.
set /p option="Opcion (1-6): "

if "%option%"=="1" goto install
if "%option%"=="2" goto websocket
if "%option%"=="3" goto dashboard
if "%option%"=="4" goto process
if "%option%"=="5" goto full
if "%option%"=="6" goto end

echo Opcion invalida
goto menu

:install
echo.
echo [1/2] Instalando dependencias...
pip install -r requirements.txt
echo.
echo [2/2] Instalacion completada!
echo.
pause
goto menu

:websocket
echo.
echo Iniciando servidor WebSocket en ws://localhost:8000
echo Presiona Ctrl+C para detener
echo.
python websocket_server.py
pause
goto menu

:dashboard
echo.
echo Abriendo dashboard en navegador...
start dashboard\index.html
echo Dashboard abierto!
echo.
pause
goto menu

:process
echo.
set /p video="Ruta del video a procesar: "
if "%video%"=="" (
    echo Error: Debes especificar un video
    pause
    goto menu
)
echo.
echo Procesando %video%...
python process_video_alert.py "%video%"
echo.
pause
goto menu

:full
echo.
echo Iniciando modo completo...
echo 1. Servidor WebSocket se iniciara en una nueva ventana
echo 2. Dashboard se abrira en tu navegador
echo.
start "WebSocket Server" cmd /k python websocket_server.py
timeout /t 2 /nobreak >nul
start dashboard\index.html
echo.
echo Sistema iniciado!
echo Ahora puedes ejecutar el procesamiento de video en esta ventana.
echo.
set /p video="Ruta del video a procesar (Enter para volver): "
if not "%video%"=="" (
    python process_video_alert.py "%video%"
)
goto menu

:end
echo.
echo Saliendo...
exit