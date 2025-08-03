/* Guitar-MIDI Web Interface - WebSocket Communication */

let socket = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 3000;

function initializeWebSocket() {
    console.log('🔌 Iniciando conexión WebSocket...');
    
    // Conectar a SocketIO
    socket = io({
        transports: ['websocket', 'polling'],
        timeout: 5000,
        forceNew: true
    });
    
    // Event listeners
    setupSocketEventListeners();
}

function setupSocketEventListeners() {
    if (!socket) return;
    
    // ==================== CONNECTION EVENTS ====================
    
    socket.on('connect', function() {
        console.log('✅ WebSocket conectado');
        reconnectAttempts = 0;
        updateConnectionStatus(true);
        showToast('Conectado al sistema MIDI', 'success');
        
        // Solicitar estado actual
        socket.emit('request_state');
    });
    
    socket.on('disconnect', function(reason) {
        console.log('❌ WebSocket desconectado:', reason);
        updateConnectionStatus(false);
        showToast('Conexión perdida', 'warning');
        
        // Intentar reconectar si no fue desconexión manual
        if (reason !== 'io client disconnect') {
            attemptReconnect();
        }
    });
    
    socket.on('connect_error', function(error) {
        console.error('❌ Error de conexión:', error);
        updateConnectionStatus(false);
        
        if (reconnectAttempts === 0) {
            showToast('Error de conexión al servidor', 'error');
        }
        
        attemptReconnect();
    });
    
    socket.on('reconnect', function(attemptNumber) {
        console.log(`🔄 Reconectado después de ${attemptNumber} intentos`);
        updateConnectionStatus(true);
        showToast('Reconectado al sistema', 'success');
    });
    
    socket.on('reconnect_error', function(error) {
        console.error('❌ Error de reconexión:', error);
    });
    
    socket.on('reconnect_failed', function() {
        console.error('❌ Reconexión fallida después de múltiples intentos');
        showToast('No se pudo reconectar. Recarga la página.', 'error');
    });
    
    // ==================== APPLICATION EVENTS ====================
    
    socket.on('state_update', function(state) {
        console.log('📊 Actualización de estado recibida:', state);
        updateAppState(state);
    });
    
    socket.on('instrument_changed', function(data) {
        console.log('🎹 Instrumento cambiado:', data);
        
        if (window.appState && window.appState.instruments) {
            window.appState.instruments[data.pc] = data.instrument;
            updateInstrumentGrid(window.appState.instruments);
            
            // Si es el instrumento actual, actualizar display
            if (data.pc == window.appState.currentInstrument) {
                updateCurrentInstrumentDisplay();
            }
        }
        
        logActivity(`PC ${data.pc} → ${data.instrument.name}`);
        showToast(`Instrumento ${data.pc} cambiado a ${data.instrument.name}`, 'success');
    });
    
    socket.on('preset_loaded', function(data) {
        console.log('💾 Preset cargado:', data);
        
        if (data.state) {
            updateAppState(data.state);
        }
        
        logActivity(`Preset cargado: ${data.preset_name}`);
        showToast(`Preset "${data.preset_name}" cargado`, 'success');
    });
    
    socket.on('effects_changed', function(effects) {
        console.log('🎛️ Efectos actualizados:', effects);
        
        if (window.appState) {
            window.appState.effects = effects;
            updateEffectsDisplay(effects);
        }
        
        logActivity('Efectos globales actualizados');
    });
    
    socket.on('midi_activity', function(activity) {
        console.log('🎵 Actividad MIDI:', activity);
        
        if (activity && activity.message) {
            logActivity(activity.message);
        }
        
        // Actualizar indicador de actividad
        activateActivityIndicator();
    });
    
    socket.on('panic_triggered', function(data) {
        console.log('🔴 PANIC activado:', data);
        logActivity('PANIC - Todas las notas detenidas');
        
        // Efecto visual en el botón
        const panicBtn = document.getElementById('panicBtn');
        if (panicBtn) {
            panicBtn.style.backgroundColor = '#ff1744';
            setTimeout(() => {
                panicBtn.style.backgroundColor = '';
            }, 500);
        }
    });
    
    // ==================== ERROR EVENTS ====================
    
    socket.on('error', function(error) {
        console.error('❌ Error del servidor:', error);
        showToast('Error del servidor', 'error');
    });
    
    socket.on('api_error', function(error) {
        console.error('❌ Error de API:', error);
        showToast(`Error: ${error.message}`, 'error');
    });
}

// ==================== HELPER FUNCTIONS ====================

function updateAppState(newState) {
    console.log('🔄 Actualizando estado de la aplicación');
    
    if (!window.appState) {
        window.appState = {};
    }
    
    // Fusionar estados
    Object.assign(window.appState, newState);
    
    // Actualizar UI
    if (newState.instruments) {
        updateInstrumentGrid(newState.instruments);
    }
    
    if (newState.effects) {
        updateEffectsDisplay(newState.effects);
    }
    
    if (newState.current_instrument !== undefined) {
        window.appState.currentInstrument = newState.current_instrument;
    }
    
    updateCurrentInstrumentDisplay();
}

function updateEffectsDisplay(effects) {
    // Actualizar sliders de efectos
    Object.keys(effects).forEach(effectName => {
        const value = effects[effectName];
        
        // Buscar slider correspondiente
        const slider = document.querySelector(`[data-effect="${effectName}"]`);
        if (slider) {
            slider.value = value;
            
            // Actualizar display de valor
            const valueDisplay = document.getElementById(effectName.replace('_', '') + 'Value');
            if (valueDisplay) {
                valueDisplay.textContent = value + '%';
            }
        }
    });
}

function attemptReconnect() {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        console.log('❌ Máximo número de intentos de reconexión alcanzado');
        showToast('Conexión perdida. Recarga la página.', 'error');
        return;
    }
    
    reconnectAttempts++;
    console.log(`🔄 Intento de reconexión ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`);
    
    setTimeout(() => {
        if (socket && !socket.connected) {
            console.log('🔌 Intentando reconectar...');
            socket.connect();
        }
    }, RECONNECT_DELAY);
}

// ==================== PUBLIC API ====================

function sendInstrumentChange(pc, instrumentData) {
    if (socket && socket.connected) {
        socket.emit('change_instrument', {
            pc: pc,
            instrument: instrumentData
        });
    } else {
        console.warn('⚠️ WebSocket no conectado, usando HTTP API');
        // Fallback a HTTP API
        updateInstrument(pc, instrumentData);
    }
}

function sendEffectChange(effectName, value) {
    if (socket && socket.connected) {
        socket.emit('change_effect', {
            effect: effectName,
            value: value
        });
    } else {
        console.warn('⚠️ WebSocket no conectado, usando HTTP API');
        // Fallback a HTTP API
        const data = {};
        data[effectName] = value;
        updateEffect(effectName, value);
    }
}

function sendPresetLoad(presetName) {
    if (socket && socket.connected) {
        socket.emit('load_preset', {
            preset_name: presetName
        });
    } else {
        console.warn('⚠️ WebSocket no conectado, usando HTTP API');
        // Fallback a HTTP API
        loadPreset(presetName);
    }
}

function requestCurrentState() {
    if (socket && socket.connected) {
        socket.emit('request_state');
    }
}

// ==================== CLEANUP ====================

window.addEventListener('beforeunload', function() {
    if (socket) {
        console.log('🔌 Cerrando conexión WebSocket...');
        socket.disconnect();
    }
});

// ==================== EXPORTS ====================

// Hacer funciones disponibles globalmente
window.sendInstrumentChange = sendInstrumentChange;
window.sendEffectChange = sendEffectChange;
window.sendPresetLoad = sendPresetLoad;
window.requestCurrentState = requestCurrentState;

console.log('🔌 WebSocket module cargado');