#!/usr/bin/env python3
"""
Guitar-MIDI Engine
Sistema MIDI integrado con comunicación web
"""

import time
import rtmidi
import fluidsynth
import threading
import json
import os
import queue
from typing import Dict, Any, Optional

class MIDIEngine:
    def __init__(self):
        print("🎸 Iniciando Guitar-MIDI Engine...")
        
        # Estado del sistema
        self.current_instrument = 0
        self.is_running = False
        self.command_queue = queue.Queue()
        
        # Configuración de instrumentos
        self.instruments = {
            0: {"name": "Piano", "program": 0, "bank": 0, "channel": 0},
            1: {"name": "Drums", "program": 0, "bank": 128, "channel": 9},
            2: {"name": "Bass", "program": 32, "bank": 0, "channel": 1},
            3: {"name": "Guitar", "program": 24, "bank": 0, "channel": 2},
            4: {"name": "Saxophone", "program": 64, "bank": 0, "channel": 3},
            5: {"name": "Strings", "program": 48, "bank": 0, "channel": 4},
            6: {"name": "Organ", "program": 16, "bank": 0, "channel": 5},
            7: {"name": "Flute", "program": 73, "bank": 0, "channel": 6}
        }
        
        # Efectos globales
        self.effects = {
            'master_volume': 80,
            'global_reverb': 50,
            'global_chorus': 30
        }
        
        # Inicializar FluidSynth
        self._init_fluidsynth()
        
        # Inicializar MIDI
        self._init_midi()
        
        # Archivo de comunicación con Flask
        self.state_file = '/tmp/guitar_midi_state.json'
        self.command_file = '/tmp/guitar_midi_commands.json'
        
        print("✅ Guitar-MIDI Engine listo")

    def _init_fluidsynth(self):
        """Inicializar FluidSynth"""
        try:
            print("🎹 Configurando FluidSynth...")
            self.fs = fluidsynth.Synth()
            
            # Configuración para Raspberry Pi
            self.fs.setting('audio.driver', 'alsa')
            self.fs.setting('audio.alsa.device', 'hw:0')
            self.fs.setting('synth.gain', 1.5)
            self.fs.setting('audio.periods', 2)
            self.fs.setting('audio.sample-rate', 44100)
            self.fs.setting('synth.cpu-cores', 4)
            
            self.fs.start()
            
            # Cargar SoundFont
            sf_path = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
            if os.path.exists(sf_path):
                self.sfid = self.fs.sfload(sf_path)
                print(f"✅ SoundFont cargado: {sf_path}")
            else:
                print(f"⚠️  SoundFont no encontrado: {sf_path}")
                self.sfid = None
            
            # Configurar instrumento inicial
            self.set_instrument(0)
            
        except Exception as e:
            print(f"❌ Error inicializando FluidSynth: {e}")
            self.fs = None

    def _init_midi(self):
        """Inicializar conexiones MIDI"""
        try:
            print("🎛️ Configurando MIDI...")
            self.midi_in = rtmidi.MidiIn()
            available_ports = self.midi_in.get_ports()
            
            print(f"📡 Puertos MIDI disponibles: {len(available_ports)}")
            for i, port in enumerate(available_ports):
                print(f"   {i}: {port}")
            
            # Conectar al primer puerto disponible
            if available_ports:
                self.midi_in.open_port(0)
                self.midi_in.set_callback(self._midi_callback)
                print(f"✅ Conectado a: {available_ports[0]}")
            else:
                print("⚠️  No se encontraron puertos MIDI")
                
        except Exception as e:
            print(f"❌ Error inicializando MIDI: {e}")
            self.midi_in = None

    def _midi_callback(self, message, data):
        """Callback para mensajes MIDI entrantes"""
        msg, delta_time = message
        
        if len(msg) >= 2:
            status = msg[0]
            
            # Program Change (0xC0-0xCF)
            if 0xC0 <= status <= 0xCF:
                pc_number = msg[1]
                if 0 <= pc_number <= 7:
                    print(f"🎹 MIDI: Program Change {pc_number}")
                    self.set_instrument(pc_number)
            
            # Note On/Off para debug
            elif 0x90 <= status <= 0x9F or 0x80 <= status <= 0x8F:
                note = msg[1]
                velocity = msg[2] if len(msg) > 2 else 0
                action = "ON" if velocity > 0 else "OFF"
                print(f"🎵 MIDI: Note {note} {action} (vel: {velocity})")

    def set_instrument(self, pc_number: int) -> bool:
        """Cambiar instrumento activo"""
        try:
            if pc_number not in self.instruments:
                print(f"⚠️  Instrumento no válido: {pc_number}")
                return False
            
            instrument = self.instruments[pc_number]
            
            if self.fs and self.sfid is not None:
                # Cambiar programa en FluidSynth
                channel = instrument.get('channel', 0)
                bank = instrument.get('bank', 0)
                program = instrument.get('program', 0)
                
                self.fs.program_select(channel, self.sfid, bank, program)
                
                print(f"🎹 Instrumento cambiado: {instrument['name']} (PC: {pc_number})")
                self.current_instrument = pc_number
                
                # Actualizar archivo de estado
                self._update_state_file()
                return True
            else:
                print("❌ FluidSynth no disponible")
                return False
                
        except Exception as e:
            print(f"❌ Error cambiando instrumento: {e}")
            return False

    def set_effect(self, effect_name: str, value: int) -> bool:
        """Cambiar efecto global"""
        try:
            if effect_name in self.effects:
                self.effects[effect_name] = max(0, min(100, value))
                print(f"🎛️ Efecto {effect_name}: {value}%")
                
                # Aplicar efecto en FluidSynth si es posible
                if self.fs:
                    if effect_name == 'master_volume':
                        # Cambiar ganancia general
                        gain = value / 100.0 * 2.0  # 0-2.0 range
                        self.fs.setting('synth.gain', gain)
                    
                self._update_state_file()
                return True
            else:
                print(f"⚠️  Efecto no reconocido: {effect_name}")
                return False
                
        except Exception as e:
            print(f"❌ Error cambiando efecto: {e}")
            return False

    def panic(self) -> bool:
        """Detener todas las notas (PANIC)"""
        try:
            if self.fs:
                # Enviar All Notes Off a todos los canales
                for channel in range(16):
                    self.fs.cc(channel, 123, 0)  # All Notes Off
                    self.fs.cc(channel, 120, 0)  # All Sound Off
                
                print("🚨 PANIC: Todas las notas detenidas")
                return True
            else:
                print("❌ FluidSynth no disponible para PANIC")
                return False
                
        except Exception as e:
            print(f"❌ Error en PANIC: {e}")
            return False

    def _update_state_file(self):
        """Actualizar archivo de estado para Flask"""
        try:
            state = {
                'current_instrument': self.current_instrument,
                'instruments': self.instruments,
                'effects': self.effects,
                'timestamp': time.time()
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
                
        except Exception as e:
            print(f"⚠️  Error actualizando estado: {e}")

    def _process_commands(self):
        """Procesar comandos desde Flask"""
        try:
            if os.path.exists(self.command_file):
                with open(self.command_file, 'r') as f:
                    commands = json.load(f)
                
                for cmd in commands:
                    self._execute_command(cmd)
                
                # Limpiar archivo de comandos
                os.remove(self.command_file)
                
        except Exception as e:
            print(f"⚠️  Error procesando comandos: {e}")

    def _execute_command(self, command: Dict[str, Any]):
        """Ejecutar un comando específico"""
        try:
            cmd_type = command.get('type')
            
            if cmd_type == 'set_instrument':
                pc = command.get('pc', 0)
                self.set_instrument(pc)
                
            elif cmd_type == 'set_effect':
                effect = command.get('effect')
                value = command.get('value', 0)
                self.set_effect(effect, value)
                
            elif cmd_type == 'panic':
                self.panic()
                
            elif cmd_type == 'update_instrument_config':
                pc = command.get('pc', 0)
                config = command.get('config', {})
                if 0 <= pc <= 7:
                    self.instruments[pc].update(config)
                    self._update_state_file()
                    
            else:
                print(f"⚠️  Comando no reconocido: {cmd_type}")
                
        except Exception as e:
            print(f"❌ Error ejecutando comando: {e}")

    def run(self):
        """Bucle principal del engine"""
        self.is_running = True
        print("🚀 Guitar-MIDI Engine ejecutándose...")
        print("🔴 Presiona Ctrl+C para detener")
        
        try:
            while self.is_running:
                # Procesar comandos desde Flask
                self._process_commands()
                
                # Actualizar estado cada segundo
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo Guitar-MIDI Engine...")
            self.stop()

    def stop(self):
        """Detener el engine"""
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
        
        # Limpiar archivos temporales
        for file_path in [self.state_file, self.command_file]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
        
        print("✅ Guitar-MIDI Engine detenido")

def main():
    """Función principal"""
    engine = MIDIEngine()
    
    try:
        engine.run()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
    finally:
        engine.stop()

if __name__ == "__main__":
    main()