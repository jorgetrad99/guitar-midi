"""
MIDI Controller API
Interfaz para controlar el sistema MIDI desde la web
CON COMUNICACIÓN REAL al MIDI Engine
"""

import json
import os
import time
from typing import Dict, List, Any

class MIDIControllerAPI:
    def __init__(self):
        # Archivos de comunicación con MIDI Engine
        self.state_file = '/tmp/guitar_midi_state.json'
        self.command_file = '/tmp/guitar_midi_commands.json'
        
        # Configuración por defecto
        self.default_config = {
            'instruments': {
                0: {"name": "Piano", "program": 0, "bank": 0, "channel": 0},
                1: {"name": "Drums", "program": 0, "bank": 128, "channel": 9},
                2: {"name": "Bass", "program": 32, "bank": 0, "channel": 1},
                3: {"name": "Guitar", "program": 24, "bank": 0, "channel": 2},
                4: {"name": "Saxophone", "program": 64, "bank": 0, "channel": 3},
                5: {"name": "Strings", "program": 48, "bank": 0, "channel": 4},
                6: {"name": "Organ", "program": 16, "bank": 0, "channel": 5},
                7: {"name": "Flute", "program": 73, "bank": 0, "channel": 6}
            },
            'effects': {
                'master_volume': 80,
                'global_reverb': 50,
                'global_chorus': 30
            }
        }
        
        self.midi_activity = []
        
        # Lista completa de instrumentos General MIDI
        self.gm_instruments = self._load_gm_instruments()
    
    def get_current_state(self) -> Dict[str, Any]:
        """Obtener estado actual desde MIDI Engine"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                return state
            else:
                return self.default_config
        except Exception as e:
            print(f"Error leyendo estado: {e}")
            return self.default_config
    
    def get_default_instruments(self) -> Dict[int, Dict]:
        """Obtener configuración actual de instrumentos"""
        state = self.get_current_state()
        return state.get('instruments', self.default_config['instruments'])
    
    def change_instrument(self, pc_number: int, config: Dict) -> Dict:
        """Cambiar configuración de un instrumento específico"""
        try:
            if 0 <= pc_number <= 7:
                # Enviar comando al MIDI Engine
                command = {
                    'type': 'update_instrument_config',
                    'pc': pc_number,
                    'config': config,
                    'timestamp': time.time()
                }
                
                success = self._send_command(command)
                
                if success:
                    self._log_activity(f"Changed PC {pc_number} to {config['name']}")
                    return {
                        'success': True,
                        'message': f"Instrument PC {pc_number} changed to {config['name']}"
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Error comunicando con MIDI Engine'
                    }
            else:
                return {
                    'success': False,
                    'error': 'PC number must be between 0-7'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def activate_instrument(self, pc_number: int) -> Dict:
        """Activar instrumento específico (cambio rápido)"""
        try:
            if 0 <= pc_number <= 7:
                command = {
                    'type': 'set_instrument',
                    'pc': pc_number,
                    'timestamp': time.time()
                }
                
                success = self._send_command(command)
                
                if success:
                    state = self.get_current_state()
                    instrument_name = state.get('instruments', {}).get(pc_number, {}).get('name', f'PC {pc_number}')
                    self._log_activity(f"Activated {instrument_name} (PC {pc_number})")
                    
                    return {
                        'success': True,
                        'message': f"Activated {instrument_name}",
                        'current_instrument': pc_number
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Error comunicando con MIDI Engine'
                    }
            else:
                return {
                    'success': False,
                    'error': 'PC number must be between 0-7'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def set_effect(self, effect_name: str, value: int) -> Dict:
        """Configurar efecto global"""
        try:
            command = {
                'type': 'set_effect',
                'effect': effect_name,
                'value': value,
                'timestamp': time.time()
            }
            
            success = self._send_command(command)
            
            if success:
                self._log_activity(f"Set {effect_name} to {value}%")
                return {
                    'success': True,
                    'message': f"{effect_name} set to {value}%"
                }
            else:
                return {
                    'success': False,
                    'message': 'Error comunicando con MIDI Engine'
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def panic(self) -> Dict:
        """Detener todas las notas (PANIC)"""
        try:
            command = {
                'type': 'panic',
                'timestamp': time.time()
            }
            
            success = self._send_command(command)
            
            if success:
                self._log_activity("PANIC - All notes off")
            
            return {
                'success': True,
                'message': 'All notes stopped'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_recent_activity(self) -> List[Dict]:
        """Obtener actividad MIDI reciente"""
        return self.midi_activity[-10:]  # Últimas 10 actividades
    
    def get_gm_instruments(self) -> Dict:
        """Obtener lista completa de instrumentos General MIDI"""
        return self.gm_instruments
    
    def _log_activity(self, message: str):
        """Registrar actividad MIDI"""
        activity = {
            'timestamp': time.time(),
            'message': message
        }
        self.midi_activity.append(activity)
        
        # Mantener solo las últimas 50 actividades
        if len(self.midi_activity) > 50:
            self.midi_activity = self.midi_activity[-50:]
    
    def _load_gm_instruments(self) -> Dict:
        """Cargar lista de instrumentos General MIDI"""
        return {
            # Piano Family (0-7)
            0: "Acoustic Grand Piano", 1: "Bright Acoustic Piano", 2: "Electric Grand Piano",
            3: "Honky-tonk Piano", 4: "Electric Piano 1", 5: "Electric Piano 2",
            6: "Harpsichord", 7: "Clavi",
            
            # Chromatic Percussion (8-15)
            8: "Celesta", 9: "Glockenspiel", 10: "Music Box", 11: "Vibraphone",
            12: "Marimba", 13: "Xylophone", 14: "Tubular Bells", 15: "Dulcimer",
            
            # Organ (16-23)
            16: "Drawbar Organ", 17: "Percussive Organ", 18: "Rock Organ",
            19: "Church Organ", 20: "Reed Organ", 21: "Accordion",
            22: "Harmonica", 23: "Tango Accordion",
            
            # Guitar (24-31)
            24: "Acoustic Guitar (nylon)", 25: "Acoustic Guitar (steel)",
            26: "Electric Guitar (jazz)", 27: "Electric Guitar (clean)",
            28: "Electric Guitar (muted)", 29: "Overdriven Guitar",
            30: "Distortion Guitar", 31: "Guitar harmonics",
            
            # Bass (32-39)
            32: "Acoustic Bass", 33: "Electric Bass (finger)", 34: "Electric Bass (pick)",
            35: "Fretless Bass", 36: "Slap Bass 1", 37: "Slap Bass 2",
            38: "Synth Bass 1", 39: "Synth Bass 2",
            
            # Strings (40-47)
            40: "Violin", 41: "Viola", 42: "Cello", 43: "Contrabass",
            44: "Tremolo Strings", 45: "Pizzicato Strings", 46: "Orchestral Harp",
            47: "Timpani",
            
            # Ensemble (48-55)
            48: "String Ensemble 1", 49: "String Ensemble 2", 50: "SynthStrings 1",
            51: "SynthStrings 2", 52: "Choir Aahs", 53: "Voice Oohs",
            54: "Synth Voice", 55: "Orchestra Hit",
            
            # Brass (56-63)
            56: "Trumpet", 57: "Trombone", 58: "Tuba", 59: "Muted Trumpet",
            60: "French Horn", 61: "Brass Section", 62: "SynthBrass 1",
            63: "SynthBrass 2",
            
            # Reed (64-71)
            64: "Soprano Sax", 65: "Alto Sax", 66: "Tenor Sax", 67: "Baritone Sax",
            68: "Oboe", 69: "English Horn", 70: "Bassoon", 71: "Clarinet",
            
            # Pipe (72-79)
            72: "Piccolo", 73: "Flute", 74: "Recorder", 75: "Pan Flute",
            76: "Blown Bottle", 77: "Shakuhachi", 78: "Whistle", 79: "Ocarina",
            
            # Synth Lead (80-87)
            80: "Lead 1 (square)", 81: "Lead 2 (sawtooth)", 82: "Lead 3 (calliope)",
            83: "Lead 4 (chiff)", 84: "Lead 5 (charang)", 85: "Lead 6 (voice)",
            86: "Lead 7 (fifths)", 87: "Lead 8 (bass + lead)",
            
            # Synth Pad (88-95)
            88: "Pad 1 (new age)", 89: "Pad 2 (warm)", 90: "Pad 3 (polysynth)",
            91: "Pad 4 (choir)", 92: "Pad 5 (bowed)", 93: "Pad 6 (metallic)",
            94: "Pad 7 (halo)", 95: "Pad 8 (sweep)",
            
            # Synth Effects (96-103)
            96: "FX 1 (rain)", 97: "FX 2 (soundtrack)", 98: "FX 3 (crystal)",
            99: "FX 4 (atmosphere)", 100: "FX 5 (brightness)", 101: "FX 6 (goblins)",
            102: "FX 7 (echoes)", 103: "FX 8 (sci-fi)",
            
            # Ethnic (104-111)
            104: "Sitar", 105: "Banjo", 106: "Shamisen", 107: "Koto",
            108: "Kalimba", 109: "Bag pipe", 110: "Fiddle", 111: "Shanai",
            
            # Percussive (112-119)
            112: "Tinkle Bell", 113: "Agogo", 114: "Steel Drums", 115: "Woodblock",
            116: "Taiko Drum", 117: "Melodic Tom", 118: "Synth Drum", 119: "Reverse Cymbal",
            
            # Sound Effects (120-127)
            120: "Guitar Fret Noise", 121: "Breath Noise", 122: "Seashore",
            123: "Bird Tweet", 124: "Telephone Ring", 125: "Helicopter",
            126: "Applause", 127: "Gunshot"
        }
    
    def _send_command(self, command: Dict[str, Any]) -> bool:
        """Enviar comando al MIDI Engine"""
        try:
            # Leer comandos existentes
            commands = []
            if os.path.exists(self.command_file):
                try:
                    with open(self.command_file, 'r') as f:
                        commands = json.load(f)
                except:
                    commands = []
            
            # Agregar nuevo comando
            commands.append(command)
            
            # Escribir comandos actualizados
            with open(self.command_file, 'w') as f:
                json.dump(commands, f)
            
            return True
            
        except Exception as e:
            print(f"Error enviando comando: {e}")
            return False
    
    def is_engine_running(self) -> bool:
        """Verificar si el MIDI Engine está ejecutándose"""
        try:
            if os.path.exists(self.state_file):
                # Verificar que el archivo sea reciente (menos de 10 segundos)
                mtime = os.path.getmtime(self.state_file)
                return (time.time() - mtime) < 10
            return False
        except:
            return False