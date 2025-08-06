#!/usr/bin/env python3
"""
🎸 MIDI Interceptor - SOLUCIÓN SIMPLE Y DIRECTA
- Intercepta TODAS las notas MIDI del controlador
- Las reenvía a FluidSynth con el preset correcto
- Web cambia preset = inmediatamente se escucha diferente
"""

import os
import sys
import time
import threading
import subprocess
from typing import Dict, List, Any

try:
    import rtmidi
    import fluidsynth
    from flask import Flask, jsonify, request
    from flask_socketio import SocketIO
except ImportError as e:
    print(f"❌ Instalar: pip3 install python-rtmidi pyfluidsynth flask flask-socketio")
    sys.exit(1)

class MIDIInterceptor:
    def __init__(self):
        print("🎸 MIDI Interceptor Professional - Sistema de Live Performance")
        
        # Estado del sistema
        self.current_preset = 0
        self.system_status = 'initializing'
        self.last_activity = time.time()
        
        # 8 Presets profesionales (editables en vivo)
        self.presets = {
            0: {
                'name': 'Piano', 
                'program': 0, 
                'bank': 0,
                'volume': 100, 
                'icon': '🎹',
                'category': 'Keys',
                'color': '#4A90E2'
            },
            1: {
                'name': 'Guitar', 
                'program': 27, 
                'bank': 0,
                'volume': 100, 
                'icon': '🎸',
                'category': 'Strings',
                'color': '#F5A623'
            }, 
            2: {
                'name': 'Bass', 
                'program': 33, 
                'bank': 0,
                'volume': 100, 
                'icon': '🎸',
                'category': 'Bass',
                'color': '#BD10E0'
            },
            3: {
                'name': 'Strings', 
                'program': 48, 
                'bank': 0,
                'volume': 100, 
                'icon': '🎻',
                'category': 'Orchestral',
                'color': '#50E3C2'
            },
            4: {
                'name': 'Trumpet', 
                'program': 56, 
                'bank': 0,
                'volume': 100, 
                'icon': '🎺',
                'category': 'Brass',
                'color': '#D0021B'
            },
            5: {
                'name': 'Sax', 
                'program': 65, 
                'bank': 0,
                'volume': 100, 
                'icon': '🎷',
                'category': 'Brass',
                'color': '#F8E71C'
            },
            6: {
                'name': 'Synth', 
                'program': 80, 
                'bank': 0,
                'volume': 100, 
                'icon': '🎛️',
                'category': 'Synth',
                'color': '#7ED321'
            },
            7: {
                'name': 'Organ', 
                'program': 16, 
                'bank': 0,
                'volume': 100, 
                'icon': '🎹',
                'category': 'Keys',
                'color': '#9013FE'
            }
        }
        
        # Controladores MIDI detectados
        self.midi_controllers = {}
        
        # Interfaces de audio detectadas
        self.audio_interfaces = {}
        
        # Configuración de volúmenes
        self.volumes = {
            'master': 100,
            'input_gain': 75,
            'output_level': 90,
            'preset_volumes': {i: 100 for i in range(8)}
        }
        
        # FluidSynth
        self.fs = None
        self.sfid = None
        
        # MIDI
        self.midi_inputs = []
        self.is_running = False
        
        # Web
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.setup_routes()

    def start(self):
        print("\n🚀 Iniciando interceptor...")
        
        # 1. Desconectar controladores de FluidSynth (queremos interceptar)
        self.disconnect_all_from_fluidsynth()
        
        # 2. FluidSynth
        self.init_fluidsynth()
        
        # 3. MIDI Input (interceptar)
        self.setup_midi_input()
        
        # 4. Detectar dispositivos
        self.detect_controllers()
        self.detect_audio_interfaces()
        
        # 5. Preset inicial
        self.change_preset(0)
        
        # 6. Estado del sistema listo
        self.system_status = 'running'
        
        print("\n✅ Sistema Profesional de Live Performance LISTO")
        print("🌐 Web Interface: http://localhost:5000")
        print(f"🎛️ {len(self.midi_controllers)} controladores MIDI detectados")
        print(f"🎧 {len(self.audio_interfaces)} interfaces de audio detectadas")
        print("🎹 Sistema interceptor funcionando perfectamente")
        
        # Web server
        self.is_running = True
        self.socketio.run(self.app, host='0.0.0.0', port=5000, debug=False)

    def disconnect_all_from_fluidsynth(self):
        """Desconectar controladores de FluidSynth para poder interceptar"""
        try:
            print("🔌 Desconectando controladores de FluidSynth...")
            
            result = subprocess.run(['aconnect', '-l'], capture_output=True, text=True)
            if result.returncode != 0:
                return
            
            # Encontrar controladores y FluidSynth
            controllers = []
            fluidsynth_client = None
            
            for line in result.stdout.split('\n'):
                if 'client' in line:
                    if any(keyword in line.lower() for keyword in ['sinco', 'usb device', 'mpk', 'akai']):
                        try:
                            client_num = line.split('client ')[1].split(':')[0]
                            controllers.append(client_num)
                        except:
                            pass
                    elif 'FLUID Synth' in line:
                        try:
                            fluidsynth_client = line.split('client ')[1].split(':')[0]
                        except:
                            pass
            
            # Desconectar cada controlador de FluidSynth
            if fluidsynth_client:
                for controller_client in controllers:
                    try:
                        cmd = ['aconnect', '-d', f'{controller_client}:0', f'{fluidsynth_client}:0']
                        subprocess.run(cmd, capture_output=True)
                        print(f"🔌 Desconectado: {controller_client} de FluidSynth")
                    except:
                        pass
            
        except Exception as e:
            print(f"❌ Error desconectando: {e}")

    def init_fluidsynth(self):
        """Inicializar FluidSynth"""
        try:
            print("🎹 Iniciando FluidSynth...")
            
            self.fs = fluidsynth.Synth()
            self.fs.start(driver="alsa")
            
            # SoundFont
            sf_paths = [
                "/usr/share/sounds/sf2/FluidR3_GM.sf2",
                "/usr/share/sounds/sf2/default.sf2"
            ]
            
            for sf_path in sf_paths:
                if os.path.exists(sf_path):
                    self.sfid = self.fs.sfload(sf_path)
                    print(f"✅ SoundFont: {sf_path}")
                    break
            
            if self.sfid is None:
                raise Exception("SoundFont no encontrado")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ FluidSynth error: {e}")
            raise

    def setup_midi_input(self):
        """Configurar MIDI Input para interceptar"""
        try:
            print("🎛️ Configurando interceptor MIDI...")
            
            midi_in = rtmidi.MidiIn()
            ports = midi_in.get_ports()
            print(f"Puertos disponibles: {ports}")
            
            # Conectar a todos los controladores conocidos
            connected = 0
            for i, port in enumerate(ports):
                if any(keyword in port.lower() for keyword in 
                      ['sinco', 'usb device', 'mpk', 'akai', 'mvave', 'captain', 'pico']):
                    try:
                        input_instance = rtmidi.MidiIn()
                        input_instance.open_port(i)
                        input_instance.set_callback(self.intercept_midi)
                        self.midi_inputs.append({
                            'name': port,
                            'instance': input_instance
                        })
                        print(f"🔌 Interceptando: {port}")
                        connected += 1
                    except Exception as e:
                        print(f"❌ Error: {e}")
            
            midi_in.close_port()
            print(f"🎛️ {connected} controladores interceptados")
            
        except Exception as e:
            print(f"❌ Error MIDI input: {e}")

    def intercept_midi(self, message, data):
        """INTERCEPTAR Y REENVIAR - AQUÍ ESTÁ LA MAGIA"""
        msg, _ = message
        
        if len(msg) >= 1:
            command = msg[0] & 0xF0
            channel = msg[0] & 0x0F
            
            # INTERCEPTAR NOTAS (Note On/Off)
            if command == 0x90 and len(msg) >= 3:  # Note On
                note = msg[1]
                velocity = msg[2]
                
                if velocity > 0:  # Note On real
                    # REENVIAR A FLUIDSYNTH CON PRESET CORRECTO
                    self.fs.noteon(0, note, velocity)  # Siempre canal 0
                    print(f"🎵 Interceptado y reenviado: nota {note}, vel {velocity} -> preset {self.current_preset}")
                else:  # Note Off (velocity 0)
                    self.fs.noteoff(0, note)
            
            elif command == 0x80 and len(msg) >= 2:  # Note Off explícito
                note = msg[1]
                self.fs.noteoff(0, note)
            
            # INTERCEPTAR PROGRAM CHANGE DEL CONTROLADOR
            elif command == 0xC0 and len(msg) >= 2:
                preset = msg[1]
                if 0 <= preset <= 7:
                    print(f"🎛️ Program Change interceptado: {preset}")
                    self.change_preset(preset)

    def change_preset(self, preset_num: int):
        """Cambiar preset - INMEDIATO"""
        try:
            if preset_num not in self.presets:
                return False
            
            preset_info = self.presets[preset_num]
            print(f"\n🎵 CAMBIANDO A: {preset_num} - {preset_info['name']}")
            
            # Cambiar en FluidSynth
            if self.fs and self.sfid is not None:
                result = self.fs.program_select(0, self.sfid, 0, preset_info['program'])
                if result == 0:
                    print(f"✅ FluidSynth: {preset_info['name']}")
                    
                    # Tocar nota de confirmación
                    self.fs.noteon(0, 60, 100)
                    time.sleep(0.1)
                    self.fs.noteoff(0, 60)
                    
                    self.current_preset = preset_num
                    
                    # Notificar web
                    if hasattr(self, 'socketio'):
                        self.socketio.emit('preset_changed', {
                            'preset': preset_num,
                            'name': preset_info['name']
                        })
                    
                    return True
                else:
                    print(f"❌ Error FluidSynth: {result}")
                    return False
            
        except Exception as e:
            print(f"❌ Error cambiando preset: {e}")
            return False

    def detect_controllers(self):
        """🔍 Detectar todos los controladores MIDI disponibles"""
        try:
            # Limpiar controladores previos
            self.midi_controllers = {}
            
            result = subprocess.run(['aconnect', '-l'], capture_output=True, text=True)
            if result.returncode != 0:
                return
            
            for line in result.stdout.split('\n'):
                if 'client' in line and any(keyword in line.lower() for keyword in 
                                          ['sinco', 'usb device', 'mpk', 'akai', 'mvave', 'captain', 'pico']):
                    try:
                        client_num = line.split('client ')[1].split(':')[0]
                        device_name = line.split("'")[1] if "'" in line else line.split(':')[1].strip()
                        
                        self.midi_controllers[device_name] = {
                            'client': client_num,
                            'name': device_name,
                            'status': 'connected',
                            'last_message': None,
                            'message_count': 0,
                            'type': self._identify_controller_type(device_name)
                        }
                        
                    except Exception as e:
                        continue
            
            print(f"🎛️ Detectados {len(self.midi_controllers)} controladores MIDI")
            
        except Exception as e:
            print(f"❌ Error detectando controladores: {e}")

    def detect_audio_interfaces(self):
        """🎧 Detectar interfaces de audio disponibles"""
        try:
            # Limpiar interfaces previas
            self.audio_interfaces = {}
            
            # Detectar dispositivos de audio ALSA
            result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'card' in line.lower() and 'device' in line.lower():
                        try:
                            # Extraer información de la tarjeta de audio
                            parts = line.split(':')
                            if len(parts) >= 2:
                                card_info = parts[1].strip()
                                device_name = card_info.split(',')[0] if ',' in card_info else card_info
                                
                                self.audio_interfaces[device_name] = {
                                    'name': device_name,
                                    'type': 'audio_input',
                                    'status': 'available',
                                    'sample_rate': 44100,
                                    'channels': 2,
                                    'input_level': 0
                                }
                        except:
                            continue
            
            # Agregar interface virtual para testing
            self.audio_interfaces['Virtual Guitar Input'] = {
                'name': 'Virtual Guitar Input',
                'type': 'virtual_input',
                'status': 'available',
                'sample_rate': 44100,
                'channels': 1,
                'input_level': 0
            }
            
            print(f"🎧 Detectadas {len(self.audio_interfaces)} interfaces de audio")
            
        except Exception as e:
            print(f"❌ Error detectando audio interfaces: {e}")

    def _identify_controller_type(self, device_name: str) -> str:
        """🎛️ Identificar tipo de controlador basado en el nombre"""
        name_lower = device_name.lower()
        if 'mpk' in name_lower or 'akai' in name_lower:
            return 'keyboard'
        elif 'captain' in name_lower:
            return 'foot_controller'
        elif 'sinco' in name_lower or 'pad' in name_lower:
            return 'drum_pad'
        elif 'usb device' in name_lower:
            return 'generic_midi'
        else:
            return 'unknown'

    def get_system_status(self):
        """📊 Obtener estado completo del sistema"""
        return {
            'current_preset': self.current_preset,
            'preset_info': self.presets[self.current_preset],
            'system_status': self.system_status,
            'last_activity': self.last_activity,
            'midi_controllers': self.midi_controllers,
            'audio_interfaces': self.audio_interfaces,
            'volumes': self.volumes,
            'presets': self.presets,
            'timestamp': time.time()
        }

    def update_preset(self, preset_id: int, updates: dict):
        """✏️ Actualizar preset en vivo"""
        try:
            if preset_id not in self.presets:
                return False
            
            # Actualizar campos permitidos
            allowed_fields = ['name', 'program', 'bank', 'volume', 'icon', 'category', 'color']
            for field, value in updates.items():
                if field in allowed_fields:
                    self.presets[preset_id][field] = value
            
            # Si es el preset actual, aplicar cambios inmediatamente
            if preset_id == self.current_preset:
                self.change_preset(preset_id)
            
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando preset {preset_id}: {e}")
            return False

    def set_volume(self, volume_type: str, value: int):
        """🔊 Controlar volúmenes del sistema"""
        try:
            if volume_type == 'master':
                self.volumes['master'] = max(0, min(100, value))
                # Aplicar volumen master a FluidSynth
                if self.fs:
                    # FluidSynth volume control (0.0 to 1.0)
                    volume_float = self.volumes['master'] / 100.0
                    # Nota: FluidSynth no tiene control directo de volumen master
                    # Se implementaría con gain en cada nota
                    
            elif volume_type == 'input_gain':
                self.volumes['input_gain'] = max(0, min(100, value))
                
            elif volume_type == 'output_level':
                self.volumes['output_level'] = max(0, min(100, value))
                
            elif volume_type.startswith('preset_'):
                preset_id = int(volume_type.split('_')[1])
                if preset_id in self.presets:
                    self.volumes['preset_volumes'][preset_id] = max(0, min(100, value))
                    self.presets[preset_id]['volume'] = value
            
            return True
            
        except Exception as e:
            print(f"❌ Error configurando volumen {volume_type}: {e}")
            return False

    def setup_routes(self):
        """🌐 Interfaz Web Profesional Completa"""
        
        @self.app.route('/')
        def index():
            return '''
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>🎸 Guitar-MIDI Live Performance System</title>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.4/socket.io.js"></script>
                <style>
                    * {
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }
                    
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
                        color: #ffffff;
                        height: 100vh;
                        overflow: hidden;
                    }
                    
                    .main-container {
                        display: grid;
                        grid-template-columns: 300px 1fr 280px;
                        grid-template-rows: 60px 1fr;
                        height: 100vh;
                        gap: 0;
                    }
                    
                    /* HEADER */
                    .header {
                        grid-column: 1 / -1;
                        background: rgba(0, 0, 0, 0.3);
                        backdrop-filter: blur(10px);
                        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        padding: 0 20px;
                    }
                    
                    .header h1 {
                        font-size: 20px;
                        font-weight: 700;
                        background: linear-gradient(45deg, #4A90E2, #50E3C2);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                    }
                    
                    .status-indicator {
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        font-size: 14px;
                    }
                    
                    .status-dot {
                        width: 8px;
                        height: 8px;
                        border-radius: 50%;
                        background: #50E3C2;
                        animation: pulse 2s infinite;
                    }
                    
                    @keyframes pulse {
                        0%, 100% { opacity: 1; }
                        50% { opacity: 0.5; }
                    }
                    
                    /* SIDEBAR IZQUIERDO - CONTROLADORES */
                    .left-sidebar {
                        background: rgba(0, 0, 0, 0.2);
                        backdrop-filter: blur(10px);
                        border-right: 1px solid rgba(255, 255, 255, 0.1);
                        padding: 20px;
                        overflow-y: auto;
                    }
                    
                    .sidebar-section {
                        margin-bottom: 30px;
                    }
                    
                    .sidebar-title {
                        font-size: 16px;
                        font-weight: 600;
                        margin-bottom: 15px;
                        color: #4A90E2;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }
                    
                    .device-item {
                        background: rgba(255, 255, 255, 0.05);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 8px;
                        padding: 12px;
                        margin-bottom: 8px;
                        transition: all 0.3s ease;
                    }
                    
                    .device-item:hover {
                        background: rgba(255, 255, 255, 0.1);
                        transform: translateY(-1px);
                    }
                    
                    .device-name {
                        font-size: 13px;
                        font-weight: 500;
                        margin-bottom: 4px;
                    }
                    
                    .device-status {
                        font-size: 11px;
                        opacity: 0.7;
                        display: flex;
                        align-items: center;
                        gap: 6px;
                    }
                    
                    .device-icon {
                        width: 6px;
                        height: 6px;
                        border-radius: 50%;
                        background: #50E3C2;
                    }
                    
                    /* ÁREA PRINCIPAL - PRESETS */
                    .main-content {
                        padding: 30px;
                        display: flex;
                        flex-direction: column;
                        gap: 20px;
                        overflow-y: auto;
                    }
                    
                    .current-preset {
                        background: linear-gradient(135deg, rgba(74, 144, 226, 0.2), rgba(80, 227, 194, 0.2));
                        border: 1px solid rgba(74, 144, 226, 0.3);
                        border-radius: 16px;
                        padding: 24px;
                        text-align: center;
                        backdrop-filter: blur(10px);
                        margin-bottom: 10px;
                    }
                    
                    .current-preset-number {
                        font-size: 48px;
                        font-weight: 800;
                        margin-bottom: 8px;
                        background: linear-gradient(45deg, #4A90E2, #50E3C2);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                    }
                    
                    .current-preset-name {
                        font-size: 24px;
                        font-weight: 600;
                        margin-bottom: 4px;
                    }
                    
                    .current-preset-category {
                        font-size: 14px;
                        opacity: 0.7;
                    }
                    
                    .presets-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 16px;
                        flex: 1;
                    }
                    
                    .preset-card {
                        background: rgba(255, 255, 255, 0.05);
                        border: 2px solid rgba(255, 255, 255, 0.1);
                        border-radius: 12px;
                        padding: 20px;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        position: relative;
                        overflow: hidden;
                    }
                    
                    .preset-card:hover {
                        transform: translateY(-4px);
                        border-color: rgba(255, 255, 255, 0.3);
                        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
                    }
                    
                    .preset-card.active {
                        border-color: #4A90E2;
                        background: rgba(74, 144, 226, 0.15);
                        box-shadow: 0 0 20px rgba(74, 144, 226, 0.3);
                    }
                    
                    .preset-number {
                        font-size: 18px;
                        font-weight: 700;
                        position: absolute;
                        top: 12px;
                        right: 12px;
                        opacity: 0.6;
                    }
                    
                    .preset-icon {
                        font-size: 32px;
                        margin-bottom: 12px;
                        display: block;
                    }
                    
                    .preset-name {
                        font-size: 16px;
                        font-weight: 600;
                        margin-bottom: 6px;
                    }
                    
                    .preset-category {
                        font-size: 12px;
                        opacity: 0.7;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                    }
                    
                    /* SIDEBAR DERECHO - CONTROLES */
                    .right-sidebar {
                        background: rgba(0, 0, 0, 0.2);
                        backdrop-filter: blur(10px);
                        border-left: 1px solid rgba(255, 255, 255, 0.1);
                        padding: 20px;
                        overflow-y: auto;
                    }
                    
                    .volume-control {
                        margin-bottom: 20px;
                    }
                    
                    .volume-label {
                        font-size: 12px;
                        font-weight: 500;
                        margin-bottom: 8px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }
                    
                    .volume-slider {
                        width: 100%;
                        height: 6px;
                        border-radius: 3px;
                        background: rgba(255, 255, 255, 0.1);
                        outline: none;
                        -webkit-appearance: none;
                        cursor: pointer;
                    }
                    
                    .volume-slider::-webkit-slider-thumb {
                        -webkit-appearance: none;
                        width: 16px;
                        height: 16px;
                        border-radius: 50%;
                        background: #4A90E2;
                        cursor: pointer;
                        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
                        transition: all 0.3s ease;
                    }
                    
                    .volume-slider::-webkit-slider-thumb:hover {
                        background: #50E3C2;
                        transform: scale(1.2);
                    }
                    
                    /* RESPONSIVE */
                    @media (max-width: 1200px) {
                        .main-container {
                            grid-template-columns: 250px 1fr 250px;
                        }
                    }
                    
                    @media (max-width: 900px) {
                        .main-container {
                            grid-template-columns: 1fr;
                            grid-template-rows: 60px 200px 1fr 200px;
                        }
                        
                        .left-sidebar, .right-sidebar {
                            border: none;
                            border-top: 1px solid rgba(255, 255, 255, 0.1);
                            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                        }
                        
                        .presets-grid {
                            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                        }
                    }
                    
                    @media (max-width: 600px) {
                        .header h1 {
                            font-size: 16px;
                        }
                        
                        .current-preset-number {
                            font-size: 36px;
                        }
                        
                        .current-preset-name {
                            font-size: 18px;
                        }
                        
                        .presets-grid {
                            grid-template-columns: repeat(2, 1fr);
                        }
                    }
                </style>
            </head>
            <body>
                <div class="main-container">
                    <!-- HEADER -->
                    <div class="header">
                        <h1>🎸 Guitar-MIDI Live Performance System</h1>
                        <div class="status-indicator">
                            <div class="status-dot"></div>
                            <span id="system-status">Sistema Activo</span>
                        </div>
                    </div>
                    
                    <!-- SIDEBAR IZQUIERDO - CONTROLADORES -->
                    <div class="left-sidebar">
                        <div class="sidebar-section">
                            <div class="sidebar-title">🎛️ Controladores MIDI</div>
                            <div id="midi-controllers"></div>
                        </div>
                        
                        <div class="sidebar-section">
                            <div class="sidebar-title">🎧 Interfaces de Audio</div>
                            <div id="audio-interfaces"></div>
                        </div>
                    </div>
                    
                    <!-- ÁREA PRINCIPAL -->
                    <div class="main-content">
                        <div class="current-preset">
                            <div class="current-preset-number" id="current-number">0</div>
                            <div class="current-preset-name" id="current-name">Piano</div>
                            <div class="current-preset-category" id="current-category">Keys</div>
                        </div>
                        
                        <div class="presets-grid" id="presets-grid">
                            <!-- Presets se cargan dinámicamente -->
                        </div>
                    </div>
                    
                    <!-- SIDEBAR DERECHO - CONTROLES -->
                    <div class="right-sidebar">
                        <div class="sidebar-section">
                            <div class="sidebar-title">🔊 Control de Volumen</div>
                            
                            <div class="volume-control">
                                <div class="volume-label">
                                    <span>Master</span>
                                    <span id="master-value">100</span>
                                </div>
                                <input type="range" class="volume-slider" id="master-volume" min="0" max="100" value="100">
                            </div>
                            
                            <div class="volume-control">
                                <div class="volume-label">
                                    <span>Input Gain</span>
                                    <span id="input-value">75</span>
                                </div>
                                <input type="range" class="volume-slider" id="input-gain" min="0" max="100" value="75">
                            </div>
                            
                            <div class="volume-control">
                                <div class="volume-label">
                                    <span>Output Level</span>
                                    <span id="output-value">90</span>
                                </div>
                                <input type="range" class="volume-slider" id="output-level" min="0" max="100" value="90">
                            </div>
                        </div>
                        
                        <div class="sidebar-section">
                            <div class="sidebar-title">⚙️ Sistema</div>
                            <button onclick="refreshDevices()" style="width: 100%; padding: 10px; background: rgba(74, 144, 226, 0.2); border: 1px solid #4A90E2; border-radius: 6px; color: white; cursor: pointer; margin-bottom: 10px;">
                                🔄 Actualizar Dispositivos
                            </button>
                            <button onclick="toggleEditMode()" style="width: 100%; padding: 10px; background: rgba(80, 227, 194, 0.2); border: 1px solid #50E3C2; border-radius: 6px; color: white; cursor: pointer;">
                                ✏️ Editar Presets
                            </button>
                        </div>
                    </div>
                </div>
                
                <script>
                    const socket = io();
                    let currentPreset = 0;
                    let systemData = {};
                    let editMode = false;
                    
                    // Inicializar sistema
                    async function initSystem() {
                        try {
                            const response = await fetch('/api/status');
                            const data = await response.json();
                            systemData = data;
                            updateUI(data);
                        } catch (error) {
                            console.error('Error inicializando:', error);
                        }
                    }
                    
                    // Actualizar interfaz completa
                    function updateUI(data) {
                        // Preset actual
                        document.getElementById('current-number').textContent = data.current_preset;
                        document.getElementById('current-name').textContent = data.preset_info.name;
                        document.getElementById('current-category').textContent = data.preset_info.category;
                        
                        // Grid de presets
                        updatePresetsGrid(data.presets);
                        
                        // Controladores MIDI
                        updateMIDIControllers(data.midi_controllers);
                        
                        // Interfaces de audio
                        updateAudioInterfaces(data.audio_interfaces);
                        
                        // Volúmenes
                        updateVolumeControls(data.volumes);
                        
                        currentPreset = data.current_preset;
                    }
                    
                    function updatePresetsGrid(presets) {
                        const grid = document.getElementById('presets-grid');
                        grid.innerHTML = '';
                        
                        for (let i = 0; i < 8; i++) {
                            const preset = presets[i];
                            const card = document.createElement('div');
                            card.className = `preset-card ${i === currentPreset ? 'active' : ''}`;
                            card.onclick = () => changePreset(i);
                            
                            card.innerHTML = `
                                <div class="preset-number">${i}</div>
                                <div class="preset-icon">${preset.icon}</div>
                                <div class="preset-name">${preset.name}</div>
                                <div class="preset-category">${preset.category}</div>
                            `;
                            
                            grid.appendChild(card);
                        }
                    }
                    
                    function updateMIDIControllers(controllers) {
                        const container = document.getElementById('midi-controllers');
                        container.innerHTML = '';
                        
                        Object.values(controllers).forEach(controller => {
                            const item = document.createElement('div');
                            item.className = 'device-item';
                            item.innerHTML = `
                                <div class="device-name">${controller.name}</div>
                                <div class="device-status">
                                    <div class="device-icon"></div>
                                    <span>${controller.type} • ${controller.status}</span>
                                </div>
                            `;
                            container.appendChild(item);
                        });
                        
                        if (Object.keys(controllers).length === 0) {
                            container.innerHTML = '<div style="opacity: 0.5; font-size: 12px;">No hay controladores detectados</div>';
                        }
                    }
                    
                    function updateAudioInterfaces(interfaces) {
                        const container = document.getElementById('audio-interfaces');
                        container.innerHTML = '';
                        
                        Object.values(interfaces).forEach(iface => {
                            const item = document.createElement('div');
                            item.className = 'device-item';
                            item.innerHTML = `
                                <div class="device-name">${iface.name}</div>
                                <div class="device-status">
                                    <div class="device-icon"></div>
                                    <span>${iface.type} • ${iface.status}</span>
                                </div>
                            `;
                            container.appendChild(item);
                        });
                    }
                    
                    function updateVolumeControls(volumes) {
                        document.getElementById('master-volume').value = volumes.master;
                        document.getElementById('master-value').textContent = volumes.master;
                        
                        document.getElementById('input-gain').value = volumes.input_gain;
                        document.getElementById('input-value').textContent = volumes.input_gain;
                        
                        document.getElementById('output-level').value = volumes.output_level;
                        document.getElementById('output-value').textContent = volumes.output_level;
                    }
                    
                    // Cambiar preset
                    async function changePreset(preset) {
                        try {
                            const response = await fetch(`/api/preset/${preset}`, {
                                method: 'POST'
                            });
                            const data = await response.json();
                            if (data.success) {
                                // La actualización llegará por WebSocket
                            }
                        } catch (error) {
                            console.error('Error cambiando preset:', error);
                        }
                    }
                    
                    // Control de volúmenes
                    document.getElementById('master-volume').addEventListener('input', (e) => {
                        const value = e.target.value;
                        document.getElementById('master-value').textContent = value;
                        setVolume('master', value);
                    });
                    
                    document.getElementById('input-gain').addEventListener('input', (e) => {
                        const value = e.target.value;
                        document.getElementById('input-value').textContent = value;
                        setVolume('input_gain', value);
                    });
                    
                    document.getElementById('output-level').addEventListener('input', (e) => {
                        const value = e.target.value;
                        document.getElementById('output-value').textContent = value;
                        setVolume('output_level', value);
                    });
                    
                    async function setVolume(type, value) {
                        try {
                            await fetch('/api/volume', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ type, value: parseInt(value) })
                            });
                        } catch (error) {
                            console.error('Error configurando volumen:', error);
                        }
                    }
                    
                    // Funciones de utilidad
                    async function refreshDevices() {
                        try {
                            await fetch('/api/refresh-devices', { method: 'POST' });
                            await initSystem(); // Recargar estado
                        } catch (error) {
                            console.error('Error actualizando dispositivos:', error);
                        }
                    }
                    
                    function toggleEditMode() {
                        editMode = !editMode;
                        // TODO: Implementar modo de edición
                        alert('Modo de edición próximamente disponible');
                    }
                    
                    // WebSocket events
                    socket.on('preset_changed', (data) => {
                        currentPreset = data.preset;
                        updatePresetsGrid(systemData.presets || {});
                        document.getElementById('current-number').textContent = data.preset;
                        document.getElementById('current-name').textContent = data.name;
                    });
                    
                    socket.on('system_status', (data) => {
                        systemData = data;
                        updateUI(data);
                    });
                    
                    // Atajos de teclado
                    document.addEventListener('keydown', (e) => {
                        if (e.key >= '0' && e.key <= '7') {
                            changePreset(parseInt(e.key));
                        }
                    });
                    
                    // Polling para sincronización
                    setInterval(async () => {
                        try {
                            const response = await fetch('/api/status');
                            const data = await response.json();
                            if (data.current_preset !== currentPreset) {
                                updateUI(data);
                            }
                        } catch (error) {
                            // Error silencioso para polling
                        }
                    }, 500);
                    
                    // Inicializar al cargar
                    initSystem();
                </script>
            </body>
            </html>
            '''
        
        # API ENDPOINTS PROFESIONALES
        @self.app.route('/api/status', methods=['GET'])
        def api_status():
            return jsonify(self.get_system_status())
        
        @self.app.route('/api/preset/<int:preset>', methods=['POST'])
        def api_change_preset(preset):
            success = self.change_preset(preset)
            return jsonify({
                'success': success,
                'preset': preset,
                'name': self.presets[preset]['name'] if success else None
            })
        
        @self.app.route('/api/volume', methods=['POST'])
        def api_set_volume():
            data = request.get_json()
            success = self.set_volume(data.get('type'), data.get('value'))
            return jsonify({'success': success})
        
        @self.app.route('/api/preset/<int:preset_id>', methods=['PUT'])
        def api_update_preset(preset_id):
            data = request.get_json()
            success = self.update_preset(preset_id, data)
            return jsonify({'success': success})
        
        @self.app.route('/api/refresh-devices', methods=['POST'])
        def api_refresh_devices():
            self.detect_controllers()
            self.detect_audio_interfaces()
            return jsonify({'success': True})

if __name__ == "__main__":
    try:
        interceptor = MIDIInterceptor()
        interceptor.start()
    except KeyboardInterrupt:
        print("\n🛑 Interceptor detenido")
    except Exception as e:
        print(f"❌ Error: {e}")