#!/usr/bin/env python3
"""
🎸 Guitar-MIDI Universal - SOLUCIÓN GENERAL PARA CUALQUIER CONTROLADOR
- Auto-detecta TODOS los controladores MIDI
- Auto-conecta a FluidSynth para que suenen  
- Web interface con sincronización total
- 8 presets sincronizados entre todos los dispositivos
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
    print(f"❌ Instalar dependencias: pip3 install python-rtmidi pyfluidsynth flask flask-socketio")
    sys.exit(1)

class UniversalMIDISystem:
    def __init__(self):
        print("🎸 Guitar-MIDI Universal - Sistema General")
        
        # Estado del sistema
        self.current_preset = 0
        self.is_running = False
        
        # 8 Presets universales
        self.presets = {
            0: {'name': 'Acoustic Guitar', 'program': 24, 'bank': 0},
            1: {'name': 'Electric Guitar', 'program': 27, 'bank': 0},
            2: {'name': 'Piano', 'program': 0, 'bank': 0},
            3: {'name': 'Bass', 'program': 33, 'bank': 0},
            4: {'name': 'Strings', 'program': 48, 'bank': 0},
            5: {'name': 'Trumpet', 'program': 56, 'bank': 0},
            6: {'name': 'Sax', 'program': 65, 'bank': 0},
            7: {'name': 'Synth', 'program': 80, 'bank': 0}
        }
        
        # MIDI
        self.connected_controllers = []  # Lista de controladores conectados
        self.midi_inputs = []           # Instancias MIDI Input
        self.midi_outputs = []          # Instancias MIDI Output
        self.fluidsynth_client = None   # Cliente FluidSynth para aconnect
        
        # FluidSynth
        self.fs = None
        self.sfid = None
        
        # Web
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.setup_routes()
    
    def start(self):
        """Inicializar sistema completo"""
        print("\n🚀 Iniciando sistema universal...")
        
        try:
            # 1. FluidSynth
            self.init_fluidsynth()
            
            # 2. Auto-detectar controladores
            self.auto_detect_controllers()
            
            # 3. Auto-conectar a FluidSynth
            self.auto_connect_to_fluidsynth()
            
            # 4. Configurar MIDI bidireccional
            self.setup_midi_io()
            
            # 5. Preset inicial
            self.change_preset(0, "Sistema")
            
            # 6. Prueba de audio
            self.test_audio()
            
            print("\n✅ Sistema iniciado correctamente")
            print("🌐 Web: http://localhost:5000")
            print("🎹 Controladores conectados y sincronizados")
            
            # Iniciar web server
            self.is_running = True
            self.socketio.run(self.app, host='0.0.0.0', port=5000, debug=False)
            
        except Exception as e:
            print(f"❌ Error iniciando sistema: {e}")
            
    def init_fluidsynth(self):
        """Inicializar FluidSynth"""
        try:
            print("🎹 Iniciando FluidSynth...")
            
            self.fs = fluidsynth.Synth()
            self.fs.start(driver="alsa")
            
            # Cargar SoundFont
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
                
            time.sleep(1)  # Esperar que FluidSynth esté listo
            
        except Exception as e:
            print(f"❌ FluidSynth error: {e}")
            raise
    
    def auto_detect_controllers(self):
        """Auto-detectar TODOS los controladores MIDI conectados"""
        try:
            print("\n🔍 Auto-detectando controladores MIDI...")
            
            # Usar aconnect para ver clientes MIDI
            result = subprocess.run(['aconnect', '-l'], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ Error ejecutando aconnect")
                return
            
            self.connected_controllers = []
            
            for line in result.stdout.split('\n'):
                if 'client ' in line and ':' in line:
                    # Filtrar controladores físicos (excluir sistema)
                    exclude = ['Timer', 'Announce', 'Midi Through']
                    if not any(excl in line for excl in exclude):
                        try:
                            client_num = line.split('client ')[1].split(':')[0]
                            
                            if "'" in line:
                                device_name = line.split("'")[1]
                            else:
                                device_name = line.split(':')[1].strip()
                            
                            # Detectar si es controlador físico (tiene puertos de entrada)
                            if any(keyword in device_name.lower() for keyword in 
                                  ['pico', 'captain', 'mpk', 'akai', 'mvave', 'pocket', 'midi', 'keyboard']):
                                
                                controller = {
                                    'client': client_num,
                                    'name': device_name,
                                    'full_line': line.strip()
                                }
                                
                                self.connected_controllers.append(controller)
                                print(f"✅ Controlador: {device_name} (cliente {client_num})")
                                
                        except Exception as e:
                            continue
            
            print(f"📊 {len(self.connected_controllers)} controladores detectados")
            
        except Exception as e:
            print(f"❌ Error detectando controladores: {e}")
    
    def auto_connect_to_fluidsynth(self):
        """Auto-conectar TODOS los controladores a FluidSynth"""
        try:
            print("\n🔗 Auto-conectando controladores a FluidSynth...")
            
            # Encontrar cliente FluidSynth
            result = subprocess.run(['aconnect', '-l'], capture_output=True, text=True)
            fluidsynth_client = None
            
            for line in result.stdout.split('\n'):
                if 'FLUID' in line and 'Synth input' in line:
                    try:
                        fluidsynth_client = line.split('client ')[1].split(':')[0]
                        print(f"🎹 FluidSynth encontrado: cliente {fluidsynth_client}")
                        break
                    except:
                        continue
            
            if not fluidsynth_client:
                print("❌ FluidSynth cliente no encontrado")
                return
            
            self.fluidsynth_client = fluidsynth_client
            
            # Conectar cada controlador a FluidSynth
            connected_count = 0
            for controller in self.connected_controllers:
                try:
                    cmd = ['aconnect', f'{controller["client"]}:0', f'{fluidsynth_client}:0']
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print(f"✅ Conectado: {controller['name']} → FluidSynth")
                        connected_count += 1
                    else:
                        print(f"⚠️  Ya conectado: {controller['name']}")
                        connected_count += 1
                        
                except Exception as e:
                    print(f"❌ Error conectando {controller['name']}: {e}")
            
            print(f"🔗 {connected_count} controladores conectados a FluidSynth")
            
        except Exception as e:
            print(f"❌ Error auto-conectando: {e}")
    
    def setup_midi_io(self):
        """Configurar MIDI Input/Output bidireccional"""
        try:
            print("\n🎛️ Configurando MIDI bidireccional...")
            
            # MIDI Input (recibir Program Change)
            midi_in = rtmidi.MidiIn()
            in_ports = midi_in.get_ports()
            
            for i, port in enumerate(in_ports):
                # Conectar a controladores conocidos
                if any(keyword in port.lower() for keyword in 
                      ['pico', 'captain', 'mpk', 'akai', 'mvave', 'pocket']):
                    try:
                        input_instance = rtmidi.MidiIn()
                        input_instance.open_port(i)
                        input_instance.set_callback(self.on_midi_message)
                        self.midi_inputs.append({
                            'name': port,
                            'instance': input_instance
                        })
                        print(f"📥 Input: {port}")
                    except Exception as e:
                        print(f"❌ Error input {port}: {e}")
            
            # MIDI Output (enviar Program Change)
            midi_out = rtmidi.MidiOut()
            out_ports = midi_out.get_ports()
            
            for i, port in enumerate(out_ports):
                # Conectar a controladores físicos (no FluidSynth)
                if (any(keyword in port.lower() for keyword in 
                       ['pico', 'captain', 'mpk', 'akai', 'mvave', 'pocket']) and
                    'fluid' not in port.lower()):
                    try:
                        output_instance = rtmidi.MidiOut()
                        output_instance.open_port(i)
                        self.midi_outputs.append({
                            'name': port,
                            'instance': output_instance
                        })
                        print(f"📤 Output: {port}")
                    except Exception as e:
                        print(f"❌ Error output {port}: {e}")
            
            midi_in.close_port()
            midi_out.close_port()
            
            print(f"🔄 {len(self.midi_inputs)} inputs, {len(self.midi_outputs)} outputs configurados")
            
        except Exception as e:
            print(f"❌ Error configurando MIDI IO: {e}")
    
    def on_midi_message(self, message, data):
        """Callback cuando llega MIDI de cualquier controlador"""
        msg, _ = message
        
        # Program Change detectado
        if len(msg) >= 2 and 0xC0 <= msg[0] <= 0xCF:
            preset = msg[1]
            if 0 <= preset <= 7:
                print(f"🎛️ Program Change recibido: {preset}")
                self.change_preset(preset, "Controlador_MIDI")
    
    def change_preset(self, preset_num: int, source: str):
        """FUNCIÓN CENTRAL: Cambiar preset con sincronización total"""
        try:
            if preset_num not in self.presets:
                return False
            
            preset_info = self.presets[preset_num]
            print(f"\n🎵 Preset {preset_num}: {preset_info['name']} (desde {source})")
            
            # 1. Cambiar sonido en FluidSynth
            if self.fs and self.sfid is not None:
                result = self.fs.program_select(0, self.sfid, preset_info['bank'], preset_info['program'])
                if result != 0:
                    print(f"❌ Error FluidSynth: {result}")
                    return False
                print(f"✅ Sonido: {preset_info['name']}")
            
            # 2. Enviar Program Change a TODOS los controladores físicos
            sent_count = 0
            for output in self.midi_outputs:
                try:
                    pc_message = [0xC0, preset_num]
                    output['instance'].send_message(pc_message)
                    print(f"📤 PC {preset_num} → {output['name']}")
                    sent_count += 1
                except Exception as e:
                    print(f"❌ Error enviando: {e}")
            
            print(f"📡 Program Change enviado a {sent_count} controladores")
            
            # 3. Actualizar estado
            self.current_preset = preset_num
            
            # 4. Notificar web interface
            if source != "Web" and hasattr(self, 'socketio'):
                self.socketio.emit('preset_changed', {
                    'preset': preset_num,
                    'name': preset_info['name'],
                    'source': source
                })
            
            return True
            
        except Exception as e:
            print(f"❌ Error cambiando preset: {e}")
            return False
    
    def test_audio(self):
        """Probar que FluidSynth esté enviando audio correctamente"""
        try:
            print("\n🔊 Probando audio FluidSynth...")
            
            # Tocar nota de prueba
            self.fs.noteon(0, 60, 100)  # C4, velocity 100
            time.sleep(0.5)
            self.fs.noteoff(0, 60)
            
            print("🎵 Nota de prueba enviada - ¿Se escuchó?")
            
            # Verificar configuración de audio
            try:
                import subprocess
                
                # Verificar volumen ALSA
                result = subprocess.run(['amixer', 'get', 'Master'], capture_output=True, text=True)
                if result.returncode == 0:
                    print("🔊 Estado de volumen ALSA:")
                    for line in result.stdout.split('\n'):
                        if '[' in line and '%' in line:
                            print(f"   {line.strip()}")
                
                # Verificar dispositivos de audio
                result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
                if result.returncode == 0:
                    print("🎧 Dispositivos de audio disponibles:")
                    for line in result.stdout.split('\n')[:5]:  # Primeras 5 líneas
                        if line.strip():
                            print(f"   {line.strip()}")
                            
            except:
                pass
                
        except Exception as e:
            print(f"❌ Error probando audio: {e}")
    
    def fix_audio(self):
        """Intentar corregir problemas de audio"""
        try:
            print("🔧 Intentando corregir audio...")
            
            import subprocess
            
            # Comandos para configurar volumen
            commands = [
                ['amixer', 'set', 'Master', '100%'],
                ['amixer', 'set', 'Master', 'unmute'],
                ['amixer', 'set', 'PCM', '100%'],
                ['amixer', 'set', 'Headphone', '100%']
            ]
            
            for cmd in commands:
                try:
                    subprocess.run(cmd, capture_output=True)
                    print(f"✅ Ejecutado: {' '.join(cmd)}")
                except:
                    pass
            
            print("🔊 Audio configurado - prueba de nuevo")
            self.test_audio()
            
        except Exception as e:
            print(f"❌ Error corrigiendo audio: {e}")
    
    def setup_routes(self):
        """Configurar rutas web"""
        
        @self.app.route('/')
        def index():
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>🎸 Guitar-MIDI Universal</title>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.4/socket.io.js"></script>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 40px; background: #1a1a1a; color: white; }}
                    .header {{ text-align: center; margin-bottom: 40px; }}
                    .status {{ background: #333; padding: 20px; border-radius: 10px; margin-bottom: 30px; text-align: center; }}
                    .presets {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; max-width: 800px; margin: 0 auto; }}
                    .preset {{ 
                        background: #444; 
                        border: none; 
                        color: white; 
                        padding: 25px; 
                        border-radius: 10px; 
                        cursor: pointer; 
                        transition: all 0.3s;
                        font-size: 16px;
                        text-align: center;
                    }}
                    .preset:hover {{ background: #555; transform: translateY(-2px); }}
                    .preset.active {{ background: #007acc; box-shadow: 0 4px 15px rgba(0,122,204,0.4); }}
                    .controllers {{ margin-top: 40px; background: #2a2a2a; padding: 20px; border-radius: 10px; }}
                    .controller-list {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; }}
                    .controller {{ background: #444; padding: 10px 15px; border-radius: 5px; font-size: 14px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🎸 Guitar-MIDI Universal</h1>
                    <p>Sistema sincronizado para múltiples controladores MIDI</p>
                </div>
                
                <div class="status">
                    <h2>Preset Actual</h2>
                    <div id="current-preset">0 - Acoustic Guitar</div>
                </div>
                
                <div class="presets">
                    {" ".join([f'<button class="preset" onclick="changePreset({i})" id="preset-{i}"><strong>{i}</strong><br>{preset["name"]}</button>' for i, preset in self.presets.items()])}
                </div>
                
                <div class="controllers">
                    <h3>🎛️ Controladores Conectados ({len(self.connected_controllers)})</h3>
                    <div class="controller-list">
                        {" ".join([f'<div class="controller">{ctrl["name"]}</div>' for ctrl in self.connected_controllers])}
                    </div>
                    <div style="margin-top: 20px; text-align: center;">
                        <button onclick="testAudio()" style="background: #28a745; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-right: 10px;">🔊 Probar Audio</button>
                        <button onclick="fixAudio()" style="background: #ffc107; color: black; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">🔧 Corregir Audio</button>
                    </div>
                </div>
                
                <script>
                    const socket = io();
                    let currentPreset = 0;
                    
                    function changePreset(preset) {{
                        fetch(`/api/preset/${{preset}}`, {{method: 'POST'}})
                            .then(r => r.json())
                            .then(data => {{
                                if (data.success) {{
                                    updateUI(preset, data.name);
                                }}
                            }});
                    }}
                    
                    function updateUI(preset, name) {{
                        // Actualizar botones
                        document.querySelectorAll('.preset').forEach(btn => btn.classList.remove('active'));
                        document.getElementById(`preset-${{preset}}`).classList.add('active');
                        
                        // Actualizar display
                        document.getElementById('current-preset').textContent = `${{preset}} - ${{name}}`;
                        currentPreset = preset;
                    }}
                    
                    // Escuchar cambios desde controladores MIDI
                    socket.on('preset_changed', function(data) {{
                        updateUI(data.preset, data.name);
                    }});
                    
                    // Funciones de audio
                    function testAudio() {{
                        fetch('/api/test-audio', {{method: 'POST'}})
                            .then(r => r.json())
                            .then(data => {{
                                alert('Prueba de audio ejecutada - revisa la consola del servidor');
                            }});
                    }}
                    
                    function fixAudio() {{
                        fetch('/api/fix-audio', {{method: 'POST'}})
                            .then(r => r.json())
                            .then(data => {{
                                alert('Corrección de audio ejecutada - revisa la consola del servidor');
                            }});
                    }}
                    
                    // Atajos de teclado
                    document.addEventListener('keydown', function(e) {{
                        const key = e.key;
                        if (key >= '0' && key <= '7') {{
                            const preset = parseInt(key);
                            changePreset(preset);
                        }}
                    }});
                    
                    // Inicializar
                    updateUI(0, 'Acoustic Guitar');
                </script>
            </body>
            </html>
            '''
        
        @self.app.route('/api/preset/<int:preset>', methods=['POST'])
        def api_change_preset(preset):
            success = self.change_preset(preset, "Web")
            return jsonify({
                'success': success,
                'preset': preset,
                'name': self.presets[preset]['name'] if success else None
            })
        
        @self.app.route('/api/status')
        def api_status():
            return jsonify({
                'current_preset': self.current_preset,
                'controllers': len(self.connected_controllers),
                'presets': self.presets
            })
        
        @self.app.route('/api/test-audio', methods=['POST'])
        def api_test_audio():
            self.test_audio()
            return jsonify({'success': True, 'message': 'Prueba de audio ejecutada'})
        
        @self.app.route('/api/fix-audio', methods=['POST'])  
        def api_fix_audio():
            self.fix_audio()
            return jsonify({'success': True, 'message': 'Corrección de audio ejecutada'})

if __name__ == "__main__":
    try:
        system = UniversalMIDISystem()
        system.start()
    except KeyboardInterrupt:
        print("\n🛑 Sistema detenido")
    except Exception as e:
        print(f"❌ Error: {e}")