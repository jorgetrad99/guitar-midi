#!/usr/bin/env python3
"""
Guitar-MIDI Web Interface
Servidor Flask para control en tiempo real desde dispositivos móviles
"""

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import json
import os
import sys
import threading
import time

# Agregar path del proyecto para importar módulos MIDI
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Importar APIs
from api.midi_controller import MIDIControllerAPI
from api.presets import PresetsAPI
from api.system_info import SystemInfoAPI

# Configuración Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'guitar-midi-secret-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Inicializar APIs
midi_api = MIDIControllerAPI()
presets_api = PresetsAPI()
system_api = SystemInfoAPI()

# Estado global de la aplicación
app_state = {
    'current_instrument': 0,
    'current_preset': 'default',
    'instruments': {},
    'effects': {
        'master_volume': 80,
        'global_reverb': 50,
        'global_chorus': 30
    },
    'midi_activity': []
}

@app.route('/')
def index():
    """Página principal del control center"""
    return render_template('index.html', state=app_state)

@app.route('/instruments')
def instruments():
    """Página de configuración de instrumentos"""
    return render_template('instruments.html', state=app_state)

@app.route('/presets')
def presets():
    """Página de gestión de presets"""
    return render_template('presets.html', state=app_state)

# ==================== API REST ENDPOINTS ====================

@app.route('/api/instruments', methods=['GET'])
def get_instruments():
    """Obtener configuración actual de instrumentos"""
    return jsonify(app_state['instruments'])

@app.route('/api/instruments/<int:pc_number>', methods=['POST'])
def update_instrument(pc_number):
    """Actualizar configuración de un instrumento específico"""
    data = request.get_json()
    
    if 0 <= pc_number <= 7:
        app_state['instruments'][pc_number] = data
        
        # Aplicar cambio al sistema MIDI
        result = midi_api.change_instrument(pc_number, data)
        
        # Notificar a todos los clientes conectados
        socketio.emit('instrument_changed', {
            'pc': pc_number,
            'instrument': data
        })
        
        return jsonify({'success': True, 'result': result})
    
    return jsonify({'error': 'PC number must be 0-7'}), 400

@app.route('/api/presets', methods=['GET'])
def get_presets():
    """Obtener lista de presets disponibles"""
    return jsonify(presets_api.get_all_presets())

@app.route('/api/presets/<preset_name>', methods=['POST'])
def load_preset(preset_name):
    """Cargar un preset específico"""
    result = presets_api.load_preset(preset_name)
    if result['success']:
        app_state.update(result['data'])
        
        # Notificar cambio de preset
        socketio.emit('preset_loaded', {
            'preset_name': preset_name,
            'state': app_state
        })
        
        return jsonify(result)
    
    return jsonify(result), 400

@app.route('/api/presets/<preset_name>', methods=['PUT'])
def save_preset(preset_name):
    """Guardar configuración actual como preset"""
    result = presets_api.save_preset(preset_name, app_state)
    return jsonify(result)

@app.route('/api/effects', methods=['POST'])
def update_effects():
    """Actualizar efectos globales"""
    data = request.get_json()
    
    for effect, value in data.items():
        if effect in app_state['effects']:
            app_state['effects'][effect] = value
            
            # Aplicar al sistema MIDI
            midi_api.set_effect(effect, value)
    
    # Notificar cambio de efectos
    socketio.emit('effects_changed', app_state['effects'])
    
    return jsonify({'success': True})

@app.route('/api/system/info', methods=['GET'])
def get_system_info():
    """Obtener información del sistema"""
    return jsonify(system_api.get_info())

@app.route('/api/system/panic', methods=['POST'])
def panic_all_notes():
    """Detener todas las notas MIDI (PANIC)"""
    result = midi_api.panic()
    
    socketio.emit('panic_triggered', {'timestamp': time.time()})
    
    return jsonify(result)

# ==================== WEBSOCKET EVENTS ====================

@socketio.on('connect')
def handle_connect():
    """Cliente conectado"""
    print(f'Cliente conectado: {request.sid}')
    emit('state_update', app_state)

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado"""
    print(f'Cliente desconectado: {request.sid}')

@socketio.on('request_state')
def handle_state_request():
    """Cliente solicita estado actual"""
    emit('state_update', app_state)

# ==================== FUNCIONES DE INICIALIZACIÓN ====================

def initialize_system():
    """Inicializar estado del sistema"""
    # Cargar instrumentos por defecto
    app_state['instruments'] = midi_api.get_default_instruments()
    
    # Cargar preset por defecto si existe
    default_preset = presets_api.load_preset('default')
    if default_preset['success']:
        app_state.update(default_preset['data'])
    
    print("🎸 Sistema Guitar-MIDI Web Interface inicializado")

def monitor_midi_activity():
    """Monitor de actividad MIDI en segundo plano"""
    while True:
        activity = midi_api.get_recent_activity()
        if activity:
            app_state['midi_activity'] = activity[-10:]  # Últimas 10 actividades
            socketio.emit('midi_activity', activity[-1])  # Enviar la más reciente
        
        time.sleep(0.1)  # 100ms polling

# ==================== MAIN ====================

if __name__ == '__main__':
    # Inicializar sistema
    initialize_system()
    
    # Iniciar monitor MIDI en hilo separado
    midi_thread = threading.Thread(target=monitor_midi_activity, daemon=True)
    midi_thread.start()
    
    print("🌐 Iniciando servidor web en http://0.0.0.0:5000")
    print("📱 Accede desde tu celular: http://192.168.4.1:5000")
    
    # Iniciar servidor
    socketio.run(app, 
                host='0.0.0.0', 
                port=5000, 
                debug=False,
                allow_unsafe_werkzeug=True)