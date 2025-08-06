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
    from flask import Flask, jsonify
    from flask_socketio import SocketIO
except ImportError as e:
    print(f"❌ Instalar: pip3 install python-rtmidi pyfluidsynth flask flask-socketio")
    sys.exit(1)

class MIDIInterceptor:
    def __init__(self):
        print("🎸 MIDI Interceptor - FUNCIONA SEGURO")
        
        # Preset actual
        self.current_preset = 0
        
        # 8 Presets
        self.presets = {
            0: {'name': 'Piano', 'program': 0},
            1: {'name': 'Guitar', 'program': 27}, 
            2: {'name': 'Bass', 'program': 33},
            3: {'name': 'Strings', 'program': 48},
            4: {'name': 'Trumpet', 'program': 56},
            5: {'name': 'Sax', 'program': 65},
            6: {'name': 'Synth', 'program': 80},
            7: {'name': 'Organ', 'program': 16}
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
        
        # 4. Preset inicial
        self.change_preset(0)
        
        print("\n✅ Interceptor funcionando")
        print("🌐 Web: http://localhost:5000")
        print("🎹 Toca el controlador - será interceptado y enviado a FluidSynth")
        
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

    def setup_routes(self):
        """Web interface simple"""
        
        @self.app.route('/')
        def index():
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>🎸 MIDI Interceptor</title>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.4/socket.io.js"></script>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 40px; background: #1a1a1a; color: white; text-align: center; }}
                    h1 {{ color: #007acc; }}
                    .preset {{ background: #444; border: none; color: white; padding: 20px; margin: 10px; border-radius: 10px; cursor: pointer; font-size: 18px; }}
                    .preset:hover {{ background: #555; }}
                    .preset.active {{ background: #007acc; }}
                    .current {{ font-size: 24px; margin: 30px 0; padding: 20px; background: #333; border-radius: 10px; }}
                </style>
            </head>
            <body>
                <h1>🎸 MIDI Interceptor</h1>
                <p>Intercepta controladores físicos y aplica presets inmediatamente</p>
                
                <div class="current" id="current">
                    Preset: {self.current_preset} - {self.presets[self.current_preset]['name']}
                </div>
                
                <div>
                    {' '.join([f'<button class="preset" onclick="changePreset({i})" id="preset-{i}">{i} - {preset["name"]}</button>' for i, preset in self.presets.items()])}
                </div>
                
                <script>
                    const socket = io();
                    
                    function changePreset(preset) {{
                        fetch(`/preset/${{preset}}`, {{method: 'POST'}})
                            .then(r => r.json())
                            .then(data => {{
                                if (data.success) {{
                                    updateUI(preset, data.name);
                                }}
                            }});
                    }}
                    
                    function updateUI(preset, name) {{
                        document.getElementById('current').textContent = `Preset: ${{preset}} - ${{name}}`;
                        document.querySelectorAll('.preset').forEach(btn => btn.classList.remove('active'));
                        document.getElementById(`preset-${{preset}}`).classList.add('active');
                    }}
                    
                    socket.on('preset_changed', function(data) {{
                        updateUI(data.preset, data.name);
                    }});
                    
                    // Atajos de teclado
                    document.addEventListener('keydown', function(e) {{
                        const key = e.key;
                        if (key >= '0' && key <= '7') {{
                            changePreset(parseInt(key));
                        }}
                    }});
                    
                    // Inicializar UI
                    updateUI({self.current_preset}, '{self.presets[self.current_preset]['name']}');
                </script>
            </body>
            </html>
            '''
        
        @self.app.route('/preset/<int:preset>', methods=['POST'])
        def api_change_preset(preset):
            success = self.change_preset(preset)
            return jsonify({
                'success': success,
                'preset': preset,
                'name': self.presets[preset]['name'] if success else None
            })

if __name__ == "__main__":
    try:
        interceptor = MIDIInterceptor()
        interceptor.start()
    except KeyboardInterrupt:
        print("\n🛑 Interceptor detenido")
    except Exception as e:
        print(f"❌ Error: {e}")