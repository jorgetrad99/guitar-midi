#!/usr/bin/env python3
"""
🎸 Guitar-MIDI Complete System
Sistema 100% unificado - UN SOLO ARCHIVO PARA TODO
- Motor MIDI con FluidSynth
- Servidor Web con interfaz móvil integrada  
- Base de datos SQLite
- Auto-detección de audio
- Comunicación en tiempo real
"""

import os
import sys
import time
import json
import sqlite3
import threading
import subprocess
import signal
import queue
from pathlib import Path
from typing import Dict, Any, Optional, List

# Verificar dependencias críticas al inicio
try:
    import rtmidi
    import fluidsynth
    from flask import Flask, render_template_string, jsonify, request
    from flask_socketio import SocketIO, emit
except ImportError as e:
    print(f"❌ Error: Dependencia faltante: {e}")
    print("💡 Instalar con: pip install python-rtmidi pyfluidsynth Flask Flask-SocketIO")
    sys.exit(1)

class GuitarMIDIComplete:
    """Sistema Guitar-MIDI 100% unificado en una sola clase"""
    
    def __init__(self):
        print("🎸 Guitar-MIDI Complete System - Iniciando...")
        
        # Estado del sistema
        self.is_running = False
        self.current_instrument = 0
        
        # Base de datos SQLite integrada
        self.db_path = "guitar_midi.db"
        self._init_database()
        
        # Configuración de instrumentos (General MIDI)
        self.instruments = {
            0: {"name": "Piano", "program": 0, "bank": 0, "channel": 0, "icon": "🎹"},
            1: {"name": "Drums", "program": 0, "bank": 128, "channel": 9, "icon": "🥁"},
            2: {"name": "Bass", "program": 32, "bank": 0, "channel": 1, "icon": "🎸"},
            3: {"name": "Guitar", "program": 24, "bank": 0, "channel": 2, "icon": "🎸"},
            4: {"name": "Saxophone", "program": 64, "bank": 0, "channel": 3, "icon": "🎷"},
            5: {"name": "Strings", "program": 48, "bank": 0, "channel": 4, "icon": "🎻"},
            6: {"name": "Organ", "program": 16, "bank": 0, "channel": 5, "icon": "🎹"},
            7: {"name": "Flute", "program": 73, "bank": 0, "channel": 6, "icon": "🪈"}
        }
        
        # Efectos globales
        self.effects = {
            'master_volume': 80,
            'global_reverb': 50,
            'global_chorus': 30
        }
        
        # Componentes del sistema
        self.fs = None  # FluidSynth
        self.sfid = None  # SoundFont ID
        self.midi_in = None  # MIDI Input
        self.app = None  # Flask App
        self.socketio = None  # SocketIO
        self.audio_device = None  # Dispositivo de audio detectado
        
        # Configurar manejadores de señales
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("✅ Guitar-MIDI Complete inicializado")
    
    def _init_database(self):
        """Inicializar base de datos SQLite integrada"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabla de configuración
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Insertar configuración inicial
                cursor.execute('INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)', 
                             ('current_instrument', '0'))
                cursor.execute('INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)', 
                             ('master_volume', '80'))
                
                conn.commit()
                print("✅ Base de datos SQLite lista")
                
        except Exception as e:
            print(f"⚠️  Error en base de datos: {e}")
    
    def _auto_detect_audio(self) -> bool:
        """Auto-detectar dispositivo de audio que funciona"""
        print("🔊 Auto-detectando audio...")
        
        # Configuraciones a probar (Raspberry Pi)
        audio_configs = [
            ("hw:0,0", "Jack 3.5mm", 1),
            ("hw:0,1", "HDMI", 2),
            ("hw:1,0", "USB", None)
        ]
        
        for device, description, raspi_config in audio_configs:
            print(f"   Probando: {description} ({device})")
            
            # Configurar raspi-config si es necesario
            if raspi_config:
                try:
                    subprocess.run(['sudo', 'raspi-config', 'nonint', 'do_audio', str(raspi_config)], 
                                 check=True, capture_output=True, timeout=10)
                    time.sleep(1)
                except:
                    pass
            
            # Test del dispositivo
            try:
                result = subprocess.run(['speaker-test', '-D', device, '-t', 'sine', '-f', '440', '-c', '2'], 
                                      timeout=2, capture_output=True)
                if result.returncode == 0:
                    print(f"   ✅ Audio detectado: {description}")
                    self.audio_device = device
                    self._configure_alsa()
                    return True
                else:
                    print(f"   ❌ No funciona: {description}")
            except:
                print(f"   ❌ Error probando: {description}")
        
        print("   ⚠️  No se detectó audio funcionando")
        self.audio_device = "hw:0,0"  # Fallback
        return False
    
    def _configure_alsa(self):
        """Configurar ALSA con volúmenes óptimos"""
        try:
            subprocess.run(['amixer', 'set', 'PCM', '100%'], capture_output=True)
            subprocess.run(['amixer', 'set', 'Master', '100%'], capture_output=True)
            subprocess.run(['amixer', 'cset', 'numid=1', '100%'], capture_output=True)
            print("   ✅ ALSA configurado")
        except Exception as e:
            print(f"   ⚠️  Error configurando ALSA: {e}")
    
    def _init_fluidsynth(self) -> bool:
        """Inicializar FluidSynth con configuración automática"""
        try:
            print("🎹 Inicializando FluidSynth...")
            self.fs = fluidsynth.Synth()
            
            # Configuración optimizada para Raspberry Pi
            self.fs.setting('audio.driver', 'alsa')
            self.fs.setting('audio.alsa.device', self.audio_device or 'hw:0,0')
            self.fs.setting('synth.gain', 1.0)
            self.fs.setting('audio.periods', 2)
            self.fs.setting('audio.sample_rate', 44100)
            self.fs.setting('synth.cpu_cores', 4)
            
            self.fs.start()
            
            # Cargar SoundFont
            sf_path = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
            if os.path.exists(sf_path):
                self.sfid = self.fs.sfload(sf_path)
                print(f"   ✅ SoundFont cargado: {sf_path}")
            else:
                print(f"   ⚠️  SoundFont no encontrado: {sf_path}")
                return False
            
            # Configurar instrumento inicial
            self._set_instrument(0)
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando FluidSynth: {e}")
            return False
    
    def _init_midi_input(self) -> bool:
        """Inicializar entrada MIDI"""
        try:
            print("🎛️ Inicializando MIDI input...")
            self.midi_in = rtmidi.MidiIn()
            available_ports = self.midi_in.get_ports()
            
            if available_ports:
                self.midi_in.open_port(0)
                self.midi_in.set_callback(self._midi_callback)
                print(f"   ✅ MIDI conectado: {available_ports[0]}")
                return True
            else:
                print("   ⚠️  No se encontraron puertos MIDI")
                return False
                
        except Exception as e:
            print(f"❌ Error inicializando MIDI: {e}")
            return False
    
    def _midi_callback(self, message, data):
        """Callback para mensajes MIDI entrantes"""
        msg, delta_time = message
        
        if len(msg) >= 2:
            status = msg[0]
            
            # Program Change (0xC0-0xCF)
            if 0xC0 <= status <= 0xCF:
                pc_number = msg[1]
                if 0 <= pc_number <= 7:
                    self._set_instrument(pc_number)
                    # Notificar a clientes web
                    if self.socketio:
                        self.socketio.emit('instrument_changed', {
                            'pc': pc_number,
                            'name': self.instruments[pc_number]['name']
                        })
    
    def _set_instrument(self, pc: int) -> bool:
        """Cambiar instrumento activo"""
        try:
            if pc not in self.instruments:
                return False
            
            instrument = self.instruments[pc]
            
            if self.fs and self.sfid is not None:
                channel = instrument['channel']
                bank = instrument['bank']
                program = instrument['program']
                
                self.fs.program_select(channel, self.sfid, bank, program)
                self.current_instrument = pc
                
                # Guardar en base de datos
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', 
                                 ('current_instrument', str(pc)))
                    conn.commit()
                
                print(f"🎹 Instrumento: {instrument['name']} (PC: {pc})")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error cambiando instrumento: {e}")
            return False
    
    def _set_effect(self, effect_name: str, value: int) -> bool:
        """Aplicar efecto global"""
        try:
            if effect_name == 'master_volume' and self.fs:
                gain = (value / 100.0) * 2.0
                self.fs.setting('synth.gain', gain)
            
            self.effects[effect_name] = value
            
            # Guardar en base de datos
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', 
                             (effect_name, str(value)))
                conn.commit()
            
            print(f"🎛️ {effect_name}: {value}%")
            return True
            
        except Exception as e:
            print(f"❌ Error aplicando efecto: {e}")
            return False
    
    def _panic(self) -> bool:
        """Detener todas las notas (PANIC)"""
        try:
            if self.fs:
                for channel in range(16):
                    self.fs.cc(channel, 123, 0)  # All Notes Off
                    self.fs.cc(channel, 120, 0)  # All Sound Off
                print("🚨 PANIC: Todas las notas detenidas")
                return True
            return False
        except Exception as e:
            print(f"❌ Error en PANIC: {e}")
            return False
    
    def _init_web_server(self):
        """Inicializar servidor web integrado"""
        print("🌐 Inicializando servidor web...")
        
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'guitar-midi-complete-2024'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Rutas principales
        @self.app.route('/')
        def index():
            return self._render_interface()
        
        # API Routes
        @self.app.route('/api/instruments/<int:pc>/activate', methods=['POST'])
        def activate_instrument(pc):
            success = self._set_instrument(pc)
            if success and self.socketio:
                self.socketio.emit('instrument_changed', {
                    'pc': pc,
                    'name': self.instruments[pc]['name']
                })
            return jsonify({'success': success, 'current_instrument': pc if success else None})
        
        @self.app.route('/api/effects', methods=['POST'])
        def update_effects():
            data = request.get_json()
            results = []
            for effect, value in data.items():
                success = self._set_effect(effect, value)
                results.append({'effect': effect, 'value': value, 'success': success})
            return jsonify({'success': True, 'results': results})
        
        @self.app.route('/api/system/panic', methods=['POST'])
        def panic():
            success = self._panic()
            return jsonify({'success': success})
        
        @self.app.route('/api/system/status', methods=['GET'])
        def system_status():
            return jsonify({
                'success': True,
                'current_instrument': self.current_instrument,
                'instruments': self.instruments,
                'effects': self.effects,
                'audio_device': self.audio_device,
                'timestamp': time.time()
            })
        
        # WebSocket Events
        @self.socketio.on('connect')
        def handle_connect():
            print("📱 Cliente conectado")
            emit('status_update', {
                'current_instrument': self.current_instrument,
                'instruments': self.instruments,
                'effects': self.effects
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print("📱 Cliente desconectado")
        
        print("✅ Servidor web listo")
    
    def _render_interface(self):
        """Renderizar interfaz web móvil integrada"""
        return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎸 Guitar-MIDI Complete</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0a0a0a, #1a1a2e);
            color: white; user-select: none; min-height: 100vh;
        }
        .header { 
            background: linear-gradient(135deg, #16213e, #0f3460);
            padding: 20px; text-align: center; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        }
        .title { font-size: 1.8rem; font-weight: bold; margin-bottom: 10px; }
        .status { 
            padding: 8px 20px; background: #4CAF50; border-radius: 25px; 
            display: inline-block; font-size: 0.9rem; font-weight: 500;
        }
        .main { padding: 20px; max-width: 600px; margin: 0 auto; padding-bottom: 100px; }
        
        .current-instrument {
            text-align: center; padding: 25px;
            background: linear-gradient(135deg, #4CAF50, #66BB6A);
            border-radius: 15px; margin-bottom: 25px;
            box-shadow: 0 8px 25px rgba(76, 175, 80, 0.3);
        }
        .current-icon { font-size: 4rem; margin-bottom: 15px; }
        .current-name { font-size: 1.5rem; font-weight: bold; }
        .current-pc { margin-top: 10px; font-size: 1rem; opacity: 0.9; }
        
        .panic-btn {
            background: linear-gradient(135deg, #f44336, #d32f2f);
            color: white; border: none; border-radius: 15px;
            padding: 18px 30px; font-size: 1.2rem; font-weight: bold;
            cursor: pointer; width: 100%; margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(244, 67, 54, 0.4);
            transition: all 0.2s;
        }
        .panic-btn:active { transform: scale(0.95); }
        
        .section {
            background: rgba(255,255,255,0.05); border-radius: 15px; 
            padding: 25px; margin-bottom: 25px; 
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        }
        .section-title { 
            font-size: 1.3rem; margin-bottom: 20px; color: #4CAF50; 
            font-weight: 600;
        }
        
        .instrument-grid {
            display: grid; grid-template-columns: repeat(2, 1fr);
            gap: 15px; margin-bottom: 20px;
        }
        .instrument-btn {
            background: rgba(255,255,255,0.08); 
            border: 2px solid rgba(255,255,255,0.2);
            border-radius: 15px; padding: 20px; text-align: center; 
            cursor: pointer; transition: all 0.3s; color: white; 
            position: relative; backdrop-filter: blur(5px);
        }
        .instrument-btn:active { transform: scale(0.95); }
        .instrument-btn.active { 
            border-color: #4CAF50; 
            background: rgba(76, 175, 80, 0.2);
            box-shadow: 0 0 20px rgba(76, 175, 80, 0.3);
        }
        .pc-number {
            position: absolute; top: 10px; left: 10px; 
            background: #4CAF50; color: white; width: 28px; height: 28px; 
            border-radius: 50%; display: flex; align-items: center; 
            justify-content: center; font-size: 0.9rem; font-weight: bold;
        }
        .instrument-icon { font-size: 2.5rem; margin-bottom: 10px; display: block; }
        .instrument-name { font-weight: 600; font-size: 1rem; }
        
        .control-item {
            display: flex; align-items: center; margin-bottom: 20px;
        }
        .control-label { flex: 1; margin-right: 20px; font-weight: 500; }
        .control-slider {
            flex: 2; height: 45px; background: rgba(255,255,255,0.1);
            border-radius: 25px; outline: none; -webkit-appearance: none;
            cursor: pointer;
        }
        .control-slider::-webkit-slider-thumb {
            -webkit-appearance: none; width: 35px; height: 35px;
            background: linear-gradient(135deg, #4CAF50, #66BB6A);
            border-radius: 50%; cursor: pointer;
            box-shadow: 0 2px 10px rgba(76, 175, 80, 0.5);
        }
        
        .footer {
            text-align: center; padding: 20px; 
            color: rgba(255,255,255,0.7); font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <header class="header">
        <h1 class="title">🎸 Guitar-MIDI Complete</h1>
        <div class="status" id="status">✅ Sistema Listo</div>
    </header>

    <main class="main">
        <div class="current-instrument">
            <div class="current-icon" id="currentIcon">🎹</div>
            <div class="current-name" id="currentName">Piano</div>
            <div class="current-pc">PC: <span id="currentPC">0</span></div>
        </div>

        <button class="panic-btn" onclick="panic()">🚨 PANIC - Detener Todo</button>

        <div class="section">
            <h2 class="section-title">🎛️ Instrumentos</h2>
            <div class="instrument-grid">
                <div class="instrument-btn active" onclick="changeInstrument(0, '🎹', 'Piano')">
                    <div class="pc-number">0</div>
                    <span class="instrument-icon">🎹</span>
                    <div class="instrument-name">Piano</div>
                </div>
                <div class="instrument-btn" onclick="changeInstrument(1, '🥁', 'Drums')">
                    <div class="pc-number">1</div>
                    <span class="instrument-icon">🥁</span>
                    <div class="instrument-name">Drums</div>
                </div>
                <div class="instrument-btn" onclick="changeInstrument(2, '🎸', 'Bass')">
                    <div class="pc-number">2</div>
                    <span class="instrument-icon">🎸</span>
                    <div class="instrument-name">Bass</div>
                </div>
                <div class="instrument-btn" onclick="changeInstrument(3, '🎸', 'Guitar')">
                    <div class="pc-number">3</div>
                    <span class="instrument-icon">🎸</span>
                    <div class="instrument-name">Guitar</div>
                </div>
                <div class="instrument-btn" onclick="changeInstrument(4, '🎷', 'Sax')">
                    <div class="pc-number">4</div>
                    <span class="instrument-icon">🎷</span>
                    <div class="instrument-name">Sax</div>
                </div>
                <div class="instrument-btn" onclick="changeInstrument(5, '🎻', 'Strings')">
                    <div class="pc-number">5</div>
                    <span class="instrument-icon">🎻</span>
                    <div class="instrument-name">Strings</div>
                </div>
                <div class="instrument-btn" onclick="changeInstrument(6, '🎹', 'Organ')">
                    <div class="pc-number">6</div>
                    <span class="instrument-icon">🎹</span>
                    <div class="instrument-name">Organ</div>
                </div>
                <div class="instrument-btn" onclick="changeInstrument(7, '🪈', 'Flute')">
                    <div class="pc-number">7</div>
                    <span class="instrument-icon">🪈</span>
                    <div class="instrument-name">Flute</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">🔊 Controles</h2>
            <div class="control-item">
                <label class="control-label">🔊 Volumen Master</label>
                <input type="range" class="control-slider" min="0" max="100" value="80" 
                       oninput="updateEffect('master_volume', this.value)">
            </div>
            <div class="control-item">
                <label class="control-label">🌊 Reverb Global</label>
                <input type="range" class="control-slider" min="0" max="100" value="50"
                       oninput="updateEffect('global_reverb', this.value)">
            </div>
            <div class="control-item">
                <label class="control-label">🎵 Chorus Global</label>
                <input type="range" class="control-slider" min="0" max="100" value="30"
                       oninput="updateEffect('global_chorus', this.value)">
            </div>
        </div>
    </main>

    <footer class="footer">
        🎸 Guitar-MIDI Complete System v2.0<br>
        ⌨️ Atajos: P=PANIC, 0-7=Instrumentos
    </footer>

    <script>
        let currentInstrument = 0;

        function changeInstrument(pc, icon, name) {
            document.querySelectorAll('.instrument-btn').forEach(btn => btn.classList.remove('active'));
            event.target.closest('.instrument-btn').classList.add('active');
            
            document.getElementById('currentIcon').textContent = icon;
            document.getElementById('currentName').textContent = name;
            document.getElementById('currentPC').textContent = pc;
            currentInstrument = pc;
            
            fetch(`/api/instruments/${pc}/activate`, { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus(`✅ ${name} activado`, '#4CAF50');
                    } else {
                        showStatus('❌ Error activando', '#f44336');
                    }
                })
                .catch(() => showStatus('❌ Error conexión', '#f44336'));
        }

        function updateEffect(effect, value) {
            const data = {};
            data[effect] = parseInt(value);
            
            fetch('/api/effects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            }).then(response => response.json())
              .then(data => {
                  if (data.success) {
                      showStatus(`🎛️ ${effect}: ${value}%`, '#4CAF50');
                  }
              })
              .catch(() => showStatus('❌ Error efecto', '#f44336'));
        }

        function panic() {
            fetch('/api/system/panic', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showStatus('🚨 PANIC - Todo detenido', '#f44336');
                    }
                })
                .catch(() => showStatus('❌ Error PANIC', '#f44336'));
        }

        function showStatus(message, color) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.style.background = color;
            setTimeout(() => {
                status.textContent = '✅ Sistema Listo';
                status.style.background = '#4CAF50';
            }, 3000);
        }

        // Atajos de teclado
        document.addEventListener('keydown', function(e) {
            if (e.target.tagName === 'INPUT') return;
            
            if (e.key === 'p' || e.key === 'P') {
                e.preventDefault();
                panic();
            } else if (e.key >= '0' && e.key <= '7') {
                e.preventDefault();
                const pc = parseInt(e.key);
                const instruments = ['🎹', '🥁', '🎸', '🎸', '🎷', '🎻', '🎹', '🪈'];
                const names = ['Piano', 'Drums', 'Bass', 'Guitar', 'Sax', 'Strings', 'Organ', 'Flute'];
                changeInstrument(pc, instruments[pc], names[pc]);
            }
        });

        console.log('🎸 Guitar-MIDI Complete System Listo');
        console.log('⌨️ Atajos: P=PANIC, 0-7=Instrumentos');
    </script>
</body>
</html>'''
    
    def run(self):
        """Ejecutar sistema completo"""
        try:
            print("🚀 Iniciando Guitar-MIDI Complete System...")
            
            # 1. Auto-detectar audio
            self._auto_detect_audio()
            
            # 2. Inicializar FluidSynth
            if not self._init_fluidsynth():
                print("❌ Error crítico: FluidSynth no pudo inicializarse")
                return False
            
            # 3. Inicializar MIDI (opcional)
            self._init_midi_input()
            
            # 4. Inicializar servidor web
            self._init_web_server()
            
            # 5. Mostrar información del sistema
            self._show_system_info()
            
            # 6. Ejecutar servidor (bloqueante)
            self.is_running = True
            print("🌐 Servidor web iniciando...")
            self.socketio.run(self.app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
            
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo sistema...")
        except Exception as e:
            print(f"❌ Error crítico: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Detener sistema completo"""
        self.is_running = False
        
        if self.midi_in:
            try:
                self.midi_in.close_port()
            except:
                pass
        
        if self.fs:
            try:
                self.fs.delete()
            except:
                pass
        
        print("✅ Guitar-MIDI Complete System detenido")
    
    def _signal_handler(self, signum, frame):
        """Manejador de señales del sistema"""
        print(f"\n🛑 Señal recibida: {signum}")
        self.stop()
        sys.exit(0)
    
    def _show_system_info(self):
        """Mostrar información del sistema"""
        print("\n" + "="*60)
        print("🎯 GUITAR-MIDI COMPLETE SYSTEM LISTO")
        print("="*60)
        
        # Obtener IP
        try:
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
            ip = result.stdout.strip().split()[0] if result.stdout.strip() else 'desconocida'
        except:
            ip = 'desconocida'
        
        print(f"🌐 IP del sistema: {ip}")
        print(f"📱 URL móvil: http://{ip}:5000")
        print(f"🔊 Audio: {self.audio_device or 'Automático'}")
        
        current_name = self.instruments[self.current_instrument]['name']
        print(f"🎹 Instrumento actual: {current_name} (PC {self.current_instrument})")
        
        print("\n📱 Para conectar desde celular:")
        print("1. Conectar a WiFi 'Guitar-MIDI' (contraseña: guitarmidi2024)")
        print("2. Abrir: http://192.168.4.1:5000")
        print("\n⌨️  Atajos: P=PANIC, 0-7=Instrumentos")
        print("🔴 Ctrl+C para detener")
        print("="*60 + "\n")

def main():
    """Función principal"""
    print("🎸 Guitar-MIDI Complete System v2.0")
    print("Sistema 100% unificado - UN SOLO ARCHIVO")
    print("-" * 50)
    
    system = GuitarMIDIComplete()
    system.run()

if __name__ == "__main__":
    main()