#!/usr/bin/env python3
"""
🎸 Guitar-MIDI Simple - SCRIPT NUEVO Y LIMPIO
Sincronización bidireccional: Web ↔ Controladores MIDI
"""

import rtmidi
import fluidsynth
from flask import Flask, jsonify
from flask_socketio import SocketIO

class SimpleMIDI:
    def __init__(self):
        print("🎸 Guitar-MIDI Simple - Iniciando...")
        
        # Presets básicos
        self.presets = {
            0: {'name': 'Piano', 'program': 0},
            1: {'name': 'Guitar', 'program': 27}, 
            2: {'name': 'Bass', 'program': 33},
            3: {'name': 'Strings', 'program': 48},
            4: {'name': 'Trumpet', 'program': 56},
            5: {'name': 'Sax', 'program': 65},
            6: {'name': 'Flute', 'program': 73},
            7: {'name': 'Synth', 'program': 80}
        }
        
        self.current_preset = 0
        self.fs = None
        self.midi_in = None
        self.midi_outputs = []
        
        # Web app
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.init_fluidsynth()
        self.init_midi()
        self.setup_routes()
    
    def init_fluidsynth(self):
        """Inicializar FluidSynth"""
        try:
            self.fs = fluidsynth.Synth()
            self.fs.start(driver="alsa")
            self.sfid = self.fs.sfload("/usr/share/sounds/sf2/FluidR3_GM.sf2")
            print("✅ FluidSynth OK")
        except Exception as e:
            print(f"❌ FluidSynth error: {e}")
    
    def init_midi(self):
        """Configurar MIDI Input/Output"""
        try:
            # MIDI Input (recibir de controladores)
            self.midi_in = rtmidi.MidiIn()
            in_ports = self.midi_in.get_ports()
            print(f"🎹 MIDI In: {in_ports}")
            
            for i, port in enumerate(in_ports):
                if any(word in port.lower() for word in ['pico', 'captain', 'mpk', 'akai']):
                    self.midi_in.open_port(i)
                    self.midi_in.set_callback(self.on_midi_message)
                    print(f"🔌 Conectado: {port}")
                    break
            
            # MIDI Output (enviar a controladores)
            midi_out = rtmidi.MidiOut()
            out_ports = midi_out.get_ports()
            print(f"📤 MIDI Out: {out_ports}")
            
            for i, port in enumerate(out_ports):
                if not any(skip in port for skip in ['Microsoft', 'Mapper', 'Timer']):
                    try:
                        output = rtmidi.MidiOut()
                        output.open_port(i)
                        self.midi_outputs.append({'name': port, 'out': output})
                        print(f"✅ Output: {port}")
                    except:
                        pass
            
        except Exception as e:
            print(f"❌ MIDI error: {e}")
    
    def on_midi_message(self, message, data):
        """Cuando llega MIDI del controlador"""
        msg, _ = message
        
        # Program Change (0xC0-0xCF)
        if len(msg) >= 2 and 0xC0 <= msg[0] <= 0xCF:
            preset = msg[1]
            if 0 <= preset <= 7:
                print(f"🎛️ MIDI: Preset {preset}")
                self.change_preset(preset, "MIDI")
    
    def change_preset(self, preset, source):
        """FUNCIÓN PRINCIPAL - Cambiar preset"""
        print(f"🎵 Preset {preset} desde {source}")
        
        if preset not in self.presets:
            return False
        
        # 1. Cambiar sonido FluidSynth
        info = self.presets[preset]
        self.fs.program_select(0, self.sfid, 0, info['program'])
        
        # 2. Enviar a controladores físicos
        for output in self.midi_outputs:
            try:
                output['out'].send_message([0xC0, preset])
                print(f"📤 PC {preset} → {output['name']}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # 3. Actualizar web
        self.current_preset = preset
        if source != "Web":
            self.socketio.emit('preset_changed', {
                'preset': preset, 
                'name': info['name']
            })
        
        return True
    
    def setup_routes(self):
        """Rutas web"""
        
        @self.app.route('/')
        def index():
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Guitar-MIDI Simple</title>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
                <style>
                    body { font-family: Arial; margin: 40px; background: #222; color: white; }
                    .preset { 
                        display: inline-block; margin: 10px; padding: 20px; 
                        background: #444; border: none; color: white; border-radius: 10px;
                        cursor: pointer; font-size: 16px;
                    }
                    .preset:hover { background: #666; }
                    .preset.active { background: #007acc; }
                    .current { margin: 20px 0; padding: 15px; background: #333; border-radius: 5px; }
                </style>
            </head>
            <body>
                <h1>🎸 Guitar-MIDI Simple</h1>
                <div class="current">Preset actual: <span id="current">0 - Piano</span></div>
                
                <div id="presets">
                    <button class="preset active" onclick="setPreset(0)">0 - Piano</button>
                    <button class="preset" onclick="setPreset(1)">1 - Guitar</button>
                    <button class="preset" onclick="setPreset(2)">2 - Bass</button>
                    <button class="preset" onclick="setPreset(3)">3 - Strings</button>
                    <button class="preset" onclick="setPreset(4)">4 - Trumpet</button>
                    <button class="preset" onclick="setPreset(5)">5 - Sax</button>
                    <button class="preset" onclick="setPreset(6)">6 - Flute</button>
                    <button class="preset" onclick="setPreset(7)">7 - Synth</button>
                </div>
                
                <script>
                    const socket = io();
                    
                    function setPreset(preset) {
                        fetch('/preset/' + preset, {method: 'POST'})
                            .then(r => r.json())
                            .then(data => {
                                if (data.success) {
                                    updateUI(preset, data.name);
                                }
                            });
                    }
                    
                    function updateUI(preset, name) {
                        document.querySelectorAll('.preset').forEach(p => p.classList.remove('active'));
                        document.querySelectorAll('.preset')[preset].classList.add('active');
                        document.getElementById('current').textContent = preset + ' - ' + name;
                    }
                    
                    socket.on('preset_changed', function(data) {
                        updateUI(data.preset, data.name);
                    });
                </script>
            </body>
            </html>
            '''
        
        @self.app.route('/preset/<int:preset>', methods=['POST'])
        def set_preset(preset):
            success = self.change_preset(preset, "Web")
            return jsonify({
                'success': success,
                'preset': preset,
                'name': self.presets[preset]['name'] if success else None
            })
    
    def run(self):
        """Ejecutar sistema"""
        print("🚀 Sistema listo en http://localhost:5000")
        self.socketio.run(self.app, host='0.0.0.0', port=5000, debug=False)

if __name__ == "__main__":
    try:
        system = SimpleMIDI()
        system.run()
    except KeyboardInterrupt:
        print("\n👋 Terminado")