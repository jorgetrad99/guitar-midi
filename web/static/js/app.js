/* Guitar-MIDI Web Interface - Main JavaScript */

// Estado global de la aplicación
window.appState = {
    connected: false,
    currentInstrument: 0,
    currentPreset: 'default',
    instruments: {},
    effects: {
        master_volume: 80,
        global_reverb: 50,
        global_chorus: 30
    },
    midiActivity: []
};

// Configuración
const CONFIG = {
    reconnectInterval: 3000,
    activityMaxItems: 10,
    toastDuration: 3000
};

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎸 Guitar-MIDI Web Interface iniciada');
    
    // Inicializar componentes
    initializeApp();
    initializeEventListeners();
    
    // Conectar WebSocket
    if (typeof initializeWebSocket === 'function') {
        initializeWebSocket();
    }
    
    // Cargar estado inicial
    loadInitialState();
});

function initializeApp() {
    // Configurar PWA
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js')
            .then(reg => console.log('Service Worker registrado'))
            .catch(err => console.log('Error en Service Worker:', err));
    }
    
    // Prevenir zoom en iOS
    document.addEventListener('gesturestart', function(e) {
        e.preventDefault();
    });
    
    // Prevenir scroll bounce en iOS
    document.addEventListener('touchmove', function(e) {
        if (e.target.closest('.activity-log, .preset-list')) {
            return; // Permitir scroll en contenedores específicos
        }
        e.preventDefault();
    }, { passive: false });
}

function initializeEventListeners() {
    // Botón PANIC
    const panicBtn = document.getElementById('panicBtn');
    if (panicBtn) {
        panicBtn.addEventListener('click', function() {
            triggerPanic();
        });
    }
    
    // Navegación entre tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', function(e) {
            // Actualizar UI pero permitir navegación normal
            updateActiveTab(this.getAttribute('href'));
        });
    });
    
    // Prevenir comportamiento de selección de texto
    document.addEventListener('selectstart', function(e) {
        if (!e.target.closest('input, textarea')) {
            e.preventDefault();
        }
    });
}

function loadInitialState() {
    // Cargar instrumentos
    loadInstruments();
    
    // Cargar presets disponibles si estamos en la página correcta
    if (document.getElementById('presetSelect')) {
        loadAvailablePresets();
    }
    
    // Cargar información del sistema si estamos en la página correcta
    if (document.getElementById('systemInfo')) {
        loadSystemInfo();
    }
    
    // Actualizar display inicial
    updateCurrentInstrumentDisplay();
}

// ==================== API CALLS ====================

function loadInstruments() {
    fetch('/api/instruments')
        .then(response => response.json())
        .then(instruments => {
            window.appState.instruments = instruments;
            updateInstrumentGrid(instruments);
            updateCurrentInstrumentDisplay();
        })
        .catch(error => {
            console.error('Error cargando instrumentos:', error);
            showToast('Error al cargar instrumentos', 'error');
        });
}

function updateInstrument(pc, instrumentData) {
    showLoading(true);
    
    fetch(`/api/instruments/${pc}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(instrumentData)
    })
    .then(response => response.json())
    .then(result => {
        showLoading(false);
        
        if (result.success) {
            window.appState.instruments[pc] = instrumentData;
            updateInstrumentGrid(window.appState.instruments);
            showToast(`Instrumento PC ${pc} actualizado`, 'success');
            
            // Si es el instrumento actual, actualizar display
            if (pc == window.appState.currentInstrument) {
                updateCurrentInstrumentDisplay();
            }
        } else {
            showToast('Error al actualizar instrumento', 'error');
        }
    })
    .catch(error => {
        showLoading(false);
        console.error('Error actualizando instrumento:', error);
        showToast('Error de conexión', 'error');
    });
}

function triggerPanic() {
    const panicBtn = document.getElementById('panicBtn');
    if (panicBtn) {
        panicBtn.style.transform = 'scale(0.9)';
        setTimeout(() => {
            panicBtn.style.transform = '';
        }, 100);
    }
    
    fetch('/api/system/panic', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            showToast('PANIC - Todas las notas detenidas', 'warning');
            logActivity('PANIC activado');
        } else {
            showToast('Error en PANIC', 'error');
        }
    })
    .catch(error => {
        console.error('Error en PANIC:', error);
        showToast('Error de conexión', 'error');
    });
}

function loadSystemInfo() {
    fetch('/api/system/info')
        .then(response => response.json())
        .then(info => {
            updateSystemInfoDisplay(info);
        })
        .catch(error => {
            console.error('Error cargando info del sistema:', error);
        });
}

// ==================== UI UPDATES ====================

function updateInstrumentGrid(instruments) {
    document.querySelectorAll('.instrument-item').forEach(item => {
        const pc = parseInt(item.dataset.pc);
        if (instruments[pc]) {
            const nameElement = item.querySelector('.instrument-name');
            const iconElement = item.querySelector('.instrument-icon');
            
            if (nameElement) {
                nameElement.textContent = instruments[pc].name;
            }
            
            if (iconElement) {
                iconElement.textContent = getInstrumentIcon(instruments[pc].name);
            }
        }
    });
}

function updateCurrentInstrumentDisplay() {
    const currentPC = window.appState.currentInstrument;
    const currentInstrument = window.appState.instruments[currentPC];
    
    if (currentInstrument) {
        // Actualizar footer
        const footerName = document.querySelector('.footer .instrument-name');
        const footerIcon = document.querySelector('.footer .instrument-icon');
        const footerPC = document.querySelector('.footer .instrument-pc');
        
        if (footerName) footerName.textContent = currentInstrument.name;
        if (footerIcon) footerIcon.textContent = getInstrumentIcon(currentInstrument.name);
        if (footerPC) footerPC.textContent = `PC: ${currentPC}`;
        
        // Actualizar header de instrumentos (si existe)
        const headerName = document.getElementById('currentInstrumentName');
        const headerIcon = document.getElementById('currentInstrumentIcon');
        const headerPC = document.getElementById('currentPC');
        const headerBank = document.getElementById('currentBank');
        const headerProgram = document.getElementById('currentProgram');
        
        if (headerName) headerName.textContent = currentInstrument.name;
        if (headerIcon) headerIcon.textContent = getInstrumentIcon(currentInstrument.name);
        if (headerPC) headerPC.textContent = currentPC;
        if (headerBank) headerBank.textContent = currentInstrument.bank;
        if (headerProgram) headerProgram.textContent = currentInstrument.program;
        
        // Actualizar item activo en grid
        document.querySelectorAll('.instrument-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeItem = document.querySelector(`[data-pc="${currentPC}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
    }
}

function updateActiveTab(href) {
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    const activeTab = document.querySelector(`[href="${href}"]`);
    if (activeTab) {
        activeTab.classList.add('active');
    }
}

function updateConnectionStatus(connected) {
    window.appState.connected = connected;
    
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    if (statusDot && statusText) {
        statusDot.className = 'status-dot ' + (connected ? 'connected' : 'disconnected');
        statusText.textContent = connected ? 'Conectado' : 'Desconectado';
    }
}

function updateSystemInfoDisplay(info) {
    const container = document.getElementById('systemInfo');
    if (!container) return;
    
    // Aquí actualizarías los elementos específicos de la página de sistema
    // Por ahora solo loggeamos la información
    console.log('System info:', info);
}

// ==================== UTILIDADES ====================

function getInstrumentIcon(instrumentName) {
    const iconMap = {
        'Piano': '🎹',
        'Drums': '🥁',
        'Bass': '🎸',
        'Guitar': '🎸',
        'Saxophone': '🎷',
        'Strings': '🎻',
        'Organ': '🎹',
        'Flute': '🪈',
        'Trumpet': '🎺',
        'Violin': '🎻',
        'Cello': '🎻',
        'Harp': '🪗'
    };
    
    // Buscar coincidencia parcial
    for (const [key, icon] of Object.entries(iconMap)) {
        if (instrumentName.toLowerCase().includes(key.toLowerCase())) {
            return icon;
        }
    }
    
    return '🎵'; // Icono por defecto
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        if (show) {
            overlay.classList.add('show');
        } else {
            overlay.classList.remove('show');
        }
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    // Mostrar toast
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Ocultar y remover toast
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, CONFIG.toastDuration);
}

function logActivity(message) {
    const timestamp = new Date().toLocaleTimeString('es-ES', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    
    const activity = {
        timestamp: timestamp,
        message: message
    };
    
    // Agregar a la lista
    window.appState.midiActivity.unshift(activity);
    
    // Mantener solo los últimos elementos
    if (window.appState.midiActivity.length > CONFIG.activityMaxItems) {
        window.appState.midiActivity = window.appState.midiActivity.slice(0, CONFIG.activityMaxItems);
    }
    
    // Actualizar UI
    updateActivityLog();
    
    // Activar indicador de actividad
    activateActivityIndicator();
}

function updateActivityLog() {
    const logContainer = document.getElementById('activityLog');
    if (!logContainer) return;
    
    logContainer.innerHTML = '';
    
    window.appState.midiActivity.forEach(activity => {
        const item = document.createElement('div');
        item.className = 'activity-item';
        
        item.innerHTML = `
            <span class="activity-time">${activity.timestamp}</span>
            <span class="activity-message">${activity.message}</span>
        `;
        
        logContainer.appendChild(item);
    });
}

function activateActivityIndicator() {
    const indicator = document.querySelector('.activity-dot');
    if (indicator) {
        indicator.classList.add('active');
        setTimeout(() => {
            indicator.classList.remove('active');
        }, 1000);
    }
}

// ==================== KEYBOARD SHORTCUTS ====================

document.addEventListener('keydown', function(e) {
    // Solo procesar si no estamos en un input
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
    }
    
    switch(e.key) {
        case 'p':
        case 'P':
            e.preventDefault();
            triggerPanic();
            break;
            
        case '0':
        case '1':
        case '2':
        case '3':
        case '4':
        case '5':
        case '6':
        case '7':
            e.preventDefault();
            const pc = parseInt(e.key);
            selectInstrument(pc);
            break;
    }
});

function selectInstrument(pc) {
    if (pc >= 0 && pc <= 7) {
        window.appState.currentInstrument = pc;
        updateCurrentInstrumentDisplay();
        logActivity(`Instrumento seleccionado: PC ${pc}`);
    }
}

// ==================== ERROR HANDLING ====================

window.addEventListener('error', function(e) {
    console.error('Error de aplicación:', e.error);
    showToast('Error inesperado en la aplicación', 'error');
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Promise rechazada:', e.reason);
    showToast('Error de comunicación', 'error');
});

// Log inicial
console.log('🎸 Guitar-MIDI Web Interface v1.0');
console.log('📱 Optimizado para dispositivos móviles');
console.log('🎹 Presiona 0-7 para seleccionar instrumentos');
console.log('🔴 Presiona P para PANIC');