/**
 * dashboard.js
 * Script principal del dashboard de operador
 * Gestiona WebSocket, mapa, eventos y UI
 */

// Configuración
const CONFIG = {
    wsUrl: 'ws://localhost:8000/events',
    reconnectDelay: 3000,
    maxReconnectDelay: 30000, // Máximo 30 segundos
    mapCenter: [40.4168, -3.7038], // Madrid por defecto
    mapZoom: 13,
    maxEvents: 100,
    maxReconnectAttempts: 5  // Máximo 5 intentos
};

// Estado global
const STATE = {
    ws: null,
    connected: false,
    reconnectAttempts: 0,
    events: [],
    selectedEvent: null,
    currentFilter: 'all',
    markers: {},
    map: null,
    reconnectTimeout: null,
    isReconnecting: false,
    gaveUp: false
};

// Iconos personalizados para el mapa
const MARKER_ICONS = {
    persona: L.divIcon({
        className: 'custom-marker',
        html: '<div class="marker-icon marker-persona">👤</div>',
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    }),
    incendio: L.divIcon({
        className: 'custom-marker',
        html: '<div class="marker-icon marker-incendio">🔥</div>',
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    }),
    inundacion: L.divIcon({
        className: 'custom-marker',
        html: '<div class="marker-icon marker-inundacion">💧</div>',
        iconSize: [30, 30],
        iconAnchor: [15, 15]
    })
};

/**
 * Inicialización del dashboard
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Inicializando dashboard...');
    
    initMap();
    initWebSocket();
    initEventListeners();
    
    console.log('✅ Dashboard inicializado');
});

/**
 * Inicializa el mapa Leaflet
 */
function initMap() {
    STATE.map = L.map('map').setView(CONFIG.mapCenter, CONFIG.mapZoom);
    
    // Capa de mapa (OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(STATE.map);
    
    console.log('🗺️ Mapa inicializado');
}

/**
 * Inicializa la conexión WebSocket
 */
function initWebSocket() {
    try {
        STATE.ws = new WebSocket(CONFIG.wsUrl);
        
        STATE.ws.onopen = onWebSocketOpen;
        STATE.ws.onclose = onWebSocketClose;
        STATE.ws.onerror = onWebSocketError;
        STATE.ws.onmessage = onWebSocketMessage;
        
    } catch (error) {
        console.error('❌ Error creando WebSocket:', error);
        updateConnectionStatus(false);
        scheduleReconnect();
    }
}

/**
 * Manejador de conexión WebSocket abierta
 */
function onWebSocketOpen(event) {
    console.log('✅ WebSocket conectado');
    STATE.connected = true;
    STATE.isReconnecting = false;
    STATE.gaveUp = false;
    
    // Solo resetear reintentos si es la primera conexión
    if (STATE.reconnectAttempts === 0) {
        updateConnectionStatus(true);
        showToast('Conectado al sistema edge', 'success');
    } else {
        console.log('🔄 Reconectado exitosamente');
        updateConnectionStatus(true);
        showToast('Reconectado al sistema edge', 'success');
        STATE.reconnectAttempts = 0;
    }
}

/**
 * Manejador de conexión WebSocket cerrada
 */
function onWebSocketClose(event) {
    console.log('🔌 WebSocket desconectado', event.code, event.reason);
    STATE.connected = false;
    updateConnectionStatus(false);
    
    // Solo mostrar toast si no estamos ya intentando reconectar
    if (!STATE.isReconnecting && STATE.reconnectAttempts === 0) {
        showToast('Desconectado del sistema edge', 'warning');
    }
    
    // No reconectar si ya nos dimos por vencidos
    if (!STATE.gaveUp) {
        scheduleReconnect();
    }
}

/**
 * Manejador de error WebSocket
 */
function onWebSocketError(error) {
    console.error('❌ Error WebSocket:', error);
    updateConnectionStatus(false);
}

/**
 * Manejador de mensajes WebSocket
 */
function onWebSocketMessage(event) {
    try {
        const data = JSON.parse(event.data);
        console.log('📨 Mensaje recibido:', data.type || data.tipo);
        
        // Procesar según tipo de mensaje
        if (data.tipo || data.type === 'persona' || data.type === 'incendio' || data.type === 'inundacion') {
            handleEventMessage(data);
        } else if (data.type === 'connection') {
            console.log('🔗 Mensaje de conexión:', data.message);
        } else if (data.type === 'ack') {
            console.log('✅ ACK recibido para evento:', data.event_id);
        } else if (data.type === 'operator_response') {
            console.log('📬 Respuesta procesada:', data.action);
        }
        
    } catch (error) {
        console.error('❌ Error procesando mensaje:', error);
    }
}

/**
 * Programa reconexión automática con backoff exponencial
 */
function scheduleReconnect() {
    // Limpiar timeout anterior si existe
    if (STATE.reconnectTimeout) {
        clearTimeout(STATE.reconnectTimeout);
    }
    
    if (STATE.reconnectAttempts < CONFIG.maxReconnectAttempts) {
        STATE.reconnectAttempts++;
        STATE.isReconnecting = true;
        
        // Backoff exponencial: 3s, 6s, 12s, 24s, 30s
        const delay = Math.min(
            CONFIG.reconnectDelay * Math.pow(2, STATE.reconnectAttempts - 1),
            CONFIG.maxReconnectDelay
        );
        
        console.log(`🔄 Reintentando conexión en ${delay/1000}s (intento ${STATE.reconnectAttempts}/${CONFIG.maxReconnectAttempts})...`);
        
        STATE.reconnectTimeout = setTimeout(() => {
            initWebSocket();
        }, delay);
    } else {
        STATE.gaveUp = true;
        STATE.isReconnecting = false;
        console.log('❌ Máximo de reintentos alcanzado. Dashboard en modo offline.');
        showToast('No se pudo conectar al servidor. Dashboard en modo offline.', 'error');
        updateConnectionStatus(false, 'Offline (sin servidor)');
    }
}

/**
 * Actualiza el indicador de estado de conexión
 */
function updateConnectionStatus(connected, customText = null) {
    const statusElement = document.getElementById('ws-status');
    const statusText = statusElement.querySelector('.status-text');
    const reconnectBtn = document.getElementById('btn-reconnect');
    
    if (connected) {
        statusElement.classList.remove('offline');
        statusElement.classList.add('online');
        statusText.textContent = customText || 'Conectado';
        reconnectBtn.style.display = 'none';
    } else {
        statusElement.classList.remove('online');
        statusElement.classList.add('offline');
        
        if (customText) {
            statusText.textContent = customText;
        } else if (STATE.isReconnecting) {
            statusText.textContent = `Reconectando (${STATE.reconnectAttempts}/${CONFIG.maxReconnectAttempts})`;
        } else {
            statusText.textContent = 'Desconectado';
        }
        
        // Mostrar botón de reconexión si nos dimos por vencidos
        if (STATE.gaveUp) {
            reconnectBtn.style.display = 'inline-block';
        } else {
            reconnectBtn.style.display = 'none';
        }
    }
}

/**
 * Maneja un mensaje de evento nuevo
 */
function handleEventMessage(event) {
    // Añadir timestamp si no existe
    if (!event.timestamp) {
        event.timestamp = new Date().toISOString();
    }
    
    // Añadir a la lista de eventos
    STATE.events.unshift(event);
    
    // Limitar número de eventos
    if (STATE.events.length > CONFIG.maxEvents) {
        STATE.events = STATE.events.slice(0, CONFIG.maxEvents);
    }
    
    // Actualizar UI
    updateEventsList();
    updateEventCount();
    addMarkerToMap(event);
    
    // Notificación
    const tipo = event.tipo || event.type;
    const prioridad = event.priority || 'normal';
    
    let toastType = 'info';
    if (prioridad === 'critica') toastType = 'error';
    else if (prioridad === 'alta') toastType = 'warning';
    
    showToast(`Nuevo evento: ${tipo.toUpperCase()}`, toastType);
    
    // Sonido de alerta (opcional)
    playAlertSound(prioridad);
}

/**
 * Actualiza la lista de eventos en el panel lateral
 */
function updateEventsList() {
    const eventsList = document.getElementById('events-list');
    
    // Filtrar eventos según filtro activo
    const filteredEvents = STATE.events.filter(event => {
        if (STATE.currentFilter === 'all') return true;
        return (event.tipo || event.type) === STATE.currentFilter;
    });
    
    // Limpiar lista
    eventsList.innerHTML = '';
    
    if (filteredEvents.length === 0) {
        eventsList.innerHTML = '<div class="empty-state"><p>No hay eventos para mostrar</p></div>';
        return;
    }
    
    // Crear elementos de evento
    filteredEvents.forEach(event => {
        const eventCard = createEventCard(event);
        eventsList.appendChild(eventCard);
    });
}

/**
 * Crea una tarjeta de evento para la lista
 */
function createEventCard(event) {
    const card = document.createElement('div');
    card.className = 'event-card';
    card.dataset.eventId = event.id;
    
    // Clases según tipo y prioridad
    const tipo = event.tipo || event.type || 'desconocido';
    const prioridad = event.priority || 'normal';
    
    card.classList.add(`event-${tipo}`);
    card.classList.add(`priority-${prioridad}`);
    
    // Icono según tipo
    const icons = {
        'persona': '👤',
        'incendio': '🔥',
        'inundacion': '💧'
    };
    const icon = icons[tipo] || '❓';
    
    // Formato de hora
    const timestamp = new Date(event.timestamp);
    const timeStr = timestamp.toLocaleTimeString('es-ES');
    
    // Contenido HTML
    card.innerHTML = `
        <div class="event-card-header">
            <span class="event-icon">${icon}</span>
            <div class="event-info">
                <div class="event-tipo">${tipo.toUpperCase()}</div>
                <div class="event-time">${timeStr}</div>
            </div>
            <span class="event-priority badge badge-${prioridad}">${prioridad}</span>
        </div>
        <div class="event-card-body">
            ${tipo === 'persona' ? `
                <div class="event-detail">
                    <span class="label">Postura:</span>
                    <span class="value">${event.postura || 'N/A'}</span>
                </div>
                <div class="event-detail">
                    <span class="label">Confianza:</span>
                    <span class="value">${((event.conf_postura || 0) * 100).toFixed(0)}%</span>
                </div>
            ` : ''}
            ${event.fire_detected ? '<div class="alert-badge">🔥 Fuego detectado</div>' : ''}
            ${event.water_detected ? '<div class="alert-badge">💧 Agua detectada</div>' : ''}
        </div>
        <div class="event-card-footer">
            <span class="event-location">📍 ${event.lat?.toFixed(4)}, ${event.lon?.toFixed(4)}</span>
        </div>
    `;
    
    // Click para mostrar detalles
    card.addEventListener('click', () => showEventDetails(event));
    
    return card;
}

/**
 * Muestra los detalles de un evento
 */
function showEventDetails(event) {
    STATE.selectedEvent = event;
    
    // Mostrar panel de detalles
    const detailsPanel = document.getElementById('event-details');
    detailsPanel.style.display = 'block';
    
    // Rellenar información
    document.getElementById('detail-id').textContent = event.id;
    document.getElementById('detail-tipo').textContent = (event.tipo || event.type || 'N/A').toUpperCase();
    document.getElementById('detail-tipo').className = `badge badge-${event.tipo || event.type}`;
    document.getElementById('detail-prioridad').textContent = (event.priority || 'normal').toUpperCase();
    document.getElementById('detail-prioridad').className = `badge badge-${event.priority || 'normal'}`;
    
    const timestamp = new Date(event.timestamp);
    document.getElementById('detail-timestamp').textContent = timestamp.toLocaleString('es-ES');
    
    // Detalles de persona
    const personDetails = document.getElementById('person-details');
    if (event.tipo === 'persona' || event.type === 'persona') {
        personDetails.style.display = 'block';
        document.getElementById('detail-postura').textContent = event.postura || 'N/A';
        document.getElementById('detail-conf-postura').textContent = 
            `${((event.conf_postura || 0) * 100).toFixed(0)}%`;
        document.getElementById('detail-estado').textContent = event.estado || 'N/A';
        document.getElementById('detail-count').textContent = event.count_people || 0;
    } else {
        personDetails.style.display = 'none';
    }
    
    // Detalles de emergencia
    const hazardDetails = document.getElementById('hazard-details');
    if (event.fire_detected || event.water_detected) {
        hazardDetails.style.display = 'block';
        document.getElementById('detail-fire').textContent = event.fire_detected ? 
            `Sí (${(event.fire_confidence * 100).toFixed(0)}%)` : 'No';
        document.getElementById('detail-water').textContent = event.water_detected ? 
            `Sí (${(event.water_confidence * 100).toFixed(0)}%)` : 'No';
    } else {
        hazardDetails.style.display = 'none';
    }
    
    // Ubicación
    document.getElementById('detail-lat').textContent = event.lat?.toFixed(6) || 'N/A';
    document.getElementById('detail-lon').textContent = event.lon?.toFixed(6) || 'N/A';
    
    // Clip de video
    const clipDetails = document.getElementById('clip-details');
    if (event.clip_path) {
        clipDetails.style.display = 'block';
        document.getElementById('detail-clip-path').textContent = event.clip_path;
    } else {
        clipDetails.style.display = 'none';
    }
    
    // Centrar mapa en el evento
    if (event.lat && event.lon) {
        STATE.map.setView([event.lat, event.lon], 15);
    }
    
    // Resaltar marcador
    highlightMarker(event.id);
}

/**
 * Añade un marcador al mapa
 */
function addMarkerToMap(event) {
    if (!event.lat || !event.lon) return;
    
    const tipo = event.tipo || event.type || 'persona';
    const icon = MARKER_ICONS[tipo] || MARKER_ICONS.persona;
    
    const marker = L.marker([event.lat, event.lon], { icon: icon })
        .addTo(STATE.map);
    
    // Popup con información
    const timestamp = new Date(event.timestamp);
    const popupContent = `
        <div class="map-popup">
            <h4>${tipo.toUpperCase()}</h4>
            <p><strong>ID:</strong> ${event.id}</p>
            <p><strong>Hora:</strong> ${timestamp.toLocaleTimeString('es-ES')}</p>
            <p><strong>Prioridad:</strong> ${event.priority || 'normal'}</p>
            ${tipo === 'persona' ? `<p><strong>Postura:</strong> ${event.postura || 'N/A'}</p>` : ''}
        </div>
    `;
    
    marker.bindPopup(popupContent);
    marker.on('click', () => showEventDetails(event));
    
    // Guardar referencia
    STATE.markers[event.id] = marker;
}

/**
 * Resalta un marcador específico
 */
function highlightMarker(eventId) {
    // Quitar resaltado de todos
    Object.values(STATE.markers).forEach(marker => {
        const icon = marker.getIcon();
        if (icon.options.html) {
            icon.options.html = icon.options.html.replace(' highlighted', '');
            marker.setIcon(icon);
        }
    });
    
    // Resaltar el seleccionado
    const marker = STATE.markers[eventId];
    if (marker) {
        marker.openPopup();
    }
}

/**
 * Actualiza el contador de eventos
 */
function updateEventCount() {
    const count = STATE.events.length;
    document.getElementById('event-count').textContent = 
        `${count} evento${count !== 1 ? 's' : ''}`;
}

/**
 * Inicializa event listeners de la UI
 */
function initEventListeners() {
    // Filtros de eventos
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Actualizar botón activo
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            
            // Aplicar filtro
            STATE.currentFilter = e.target.dataset.filter;
            updateEventsList();
        });
    });
    
    // Limpiar eventos
    document.getElementById('clear-events').addEventListener('click', () => {
        if (confirm('¿Estás seguro de querer limpiar todos los eventos?')) {
            STATE.events = [];
            updateEventsList();
            updateEventCount();
            
            // Limpiar marcadores
            Object.values(STATE.markers).forEach(marker => marker.remove());
            STATE.markers = {};
            
            showToast('Eventos limpiados', 'info');
        }
    });
    
    // Centrar mapa
    document.getElementById('center-map').addEventListener('click', () => {
        STATE.map.setView(CONFIG.mapCenter, CONFIG.mapZoom);
    });
    
    // Cerrar detalles
    document.getElementById('close-details').addEventListener('click', () => {
        document.getElementById('event-details').style.display = 'none';
        STATE.selectedEvent = null;
    });
    
    // Acciones del operador
    document.getElementById('btn-confirm').addEventListener('click', () => {
        sendOperatorResponse('confirm');
    });
    
    document.getElementById('btn-reject').addEventListener('click', () => {
        sendOperatorResponse('reject');
    });
    
    // Botón de reconexión manual
    document.getElementById('btn-reconnect').addEventListener('click', () => {
        manualReconnect();
    });
}

/**
 * Reconexión manual después de dar por vencido
 */
function manualReconnect() {
    console.log('🔄 Reconexión manual solicitada');
    STATE.reconnectAttempts = 0;
    STATE.gaveUp = false;
    STATE.isReconnecting = false;
    
    if (STATE.reconnectTimeout) {
        clearTimeout(STATE.reconnectTimeout);
    }
    
    showToast('Intentando reconectar...', 'info');
    initWebSocket();
}

/**
 * Envía respuesta del operador al sistema edge
 */
function sendOperatorResponse(action) {
    if (!STATE.selectedEvent) return;
    
    const response = {
        type: 'operator_response',
        action: action,
        event_id: STATE.selectedEvent.id,
        operator_id: 'OP001',
        timestamp: new Date().toISOString()
    };
    
    if (STATE.connected && STATE.ws) {
        STATE.ws.send(JSON.stringify(response));
        console.log(`📤 Respuesta enviada: ${action} para ${STATE.selectedEvent.id}`);
        
        showToast(
            `Evento ${action === 'confirm' ? 'confirmado' : 'rechazado'}`,
            action === 'confirm' ? 'success' : 'warning'
        );
        
        // Cerrar detalles
        document.getElementById('event-details').style.display = 'none';
        STATE.selectedEvent = null;
    } else {
        showToast('No hay conexión con el sistema edge', 'error');
    }
}

/**
 * Muestra una notificación toast
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // Animar entrada
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Remover después de 3 segundos
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Reproduce sonido de alerta según prioridad
 */
function playAlertSound(priority) {
    // Implementación opcional usando Web Audio API
    // Por ahora solo log
    if (priority === 'critica' || priority === 'alta') {
        console.log('🔔 Alerta de prioridad:', priority);
    }
}

/**
 * Utilidad para formatear fechas
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// Exportar funciones para debugging
window.DEBUG = {
    state: STATE,
    config: CONFIG,
    testEvent: () => {
        const testEvent = {
            id: 'evt_test_' + Date.now(),
            tipo: 'persona',
            postura: 'tumbado',
            conf_postura: 0.85,
            estado: 'desconocido',
            conf_estado: 0.5,
            count_people: 1,
            lat: 40.4168,
            lon: -3.7038,
            timestamp: new Date().toISOString(),
            priority: 'alta',
            fire_detected: false,
            water_detected: false
        };
        handleEventMessage(testEvent);
    }
};

console.log('📱 Dashboard cargado. Usa window.DEBUG para debugging');