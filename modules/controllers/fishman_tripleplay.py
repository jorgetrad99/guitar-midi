#!/usr/bin/env python3
"""
🎸 Fishman TriplePlay Controller
Controlador específico para Fishman TriplePlay (pickup MIDI hexafónico)
"""

import time
import rtmidi
from typing import List, Dict, Any
from ..instrument_controller import InstrumentController
import logging

logger = logging.getLogger(__name__)

class FishmanTriplePlayController(InstrumentController):
    """Controlador para Fishman TriplePlay"""
    
    def __init__(self, device_name: str, device_info: Dict[str, Any], main_system_callback=None):
        # Configuración específica del TriplePlay
        self.midi_in = None
        self.port_index = device_info.get('port_index', 0)
        
        # Mapeo de cuerdas a canales MIDI (hexafónico)
        self.string_channels = {
            1: 0,  # Cuerda E grave -> Canal 0
            2: 1,  # Cuerda A -> Canal 1
            3: 2,  # Cuerda D -> Canal 2
            4: 3,  # Cuerda G -> Canal 3
            5: 4,  # Cuerda B -> Canal 4
            6: 5   # Cuerda E aguda -> Canal 5
        }
        
        # Estado de las cuerdas
        self.string_states = {i: {'active': False, 'last_note': 0, 'last_velocity': 0} for i in range(1, 7)}
        
        # Configuración de sensibilidad y procesamiento
        self.string_sensitivity = {i: 1.0 for i in range(1, 7)}
        self.polyphonic_mode = True
        self.string_mute = {i: False for i in range(1, 7)}
        
        super().__init__(device_name, device_info, main_system_callback)
    
    def setup_presets(self):
        """Configurar presets específicos del TriplePlay"""
        try:
            # Cargar presets desde base de datos
            from ..device_manager import DeviceManager
            dm = DeviceManager()
            presets_list = dm.get_device_presets(self.device_name)
            
            if presets_list:
                # Usar presets de la base de datos
                for preset in presets_list:
                    self.presets[preset['preset_id']] = {
                        'name': preset['name'],
                        'program': preset['program'],
                        'bank': preset['bank'],
                        'channel': preset['channel'],
                        'icon': preset['icon']
                    }
            else:
                # Presets por defecto optimizados para TriplePlay hexafónico
                default_presets = [
                    # Preset 0: Configuración por cuerdas
                    {
                        "name": "Hexaphonic Guitar",
                        "strings": {
                            1: {"program": 24, "bank": 0, "icon": "🎸"},  # Acoustic Guitar
                            2: {"program": 27, "bank": 0, "icon": "🎸"},  # Electric Clean
                            3: {"program": 29, "bank": 0, "icon": "🎸"},  # Overdriven
                            4: {"program": 30, "bank": 0, "icon": "🎸"},  # Distortion
                            5: {"program": 31, "bank": 0, "icon": "🎸"},  # Harmonics
                            6: {"program": 80, "bank": 0, "icon": "🎛️"}   # Synth Lead
                        }
                    },
                    # Preset 1: Modo orquesta
                    {
                        "name": "Orchestra Mode",
                        "strings": {
                            1: {"program": 42, "bank": 0, "icon": "🎻"},  # Cello
                            2: {"program": 41, "bank": 0, "icon": "🎻"},  # Viola
                            3: {"program": 40, "bank": 0, "icon": "🎻"},  # Violin
                            4: {"program": 48, "bank": 0, "icon": "🎻"},  # Strings
                            5: {"program": 56, "bank": 0, "icon": "🎺"},  # Trumpet
                            6: {"program": 73, "bank": 0, "icon": "🎼"}   # Flute
                        }
                    },
                    # Preset 2: Modo sintetizador
                    {
                        "name": "Synth Mode",
                        "strings": {
                            1: {"program": 38, "bank": 0, "icon": "🎛️"},  # Synth Bass
                            2: {"program": 80, "bank": 0, "icon": "🎛️"},  # Square Lead
                            3: {"program": 81, "bank": 0, "icon": "🎛️"},  # Sawtooth Lead
                            4: {"program": 82, "bank": 0, "icon": "🎛️"},  # Calliope Lead
                            5: {"program": 83, "bank": 0, "icon": "🎛️"},  # Chiff Lead
                            6: {"program": 84, "bank": 0, "icon": "🎛️"}   # Charang Lead
                        }
                    },
                    # Preset 3: Modo piano/teclado
                    {
                        "name": "Piano Mode",
                        "strings": {
                            1: {"program": 32, "bank": 0, "icon": "🎸"},  # Acoustic Bass
                            2: {"program": 0, "bank": 0, "icon": "🎹"},   # Grand Piano
                            3: {"program": 4, "bank": 0, "icon": "🎹"},   # Electric Piano
                            4: {"program": 16, "bank": 0, "icon": "🎹"},  # Organ
                            5: {"program": 11, "bank": 0, "icon": "🔔"},  # Vibraphone
                            6: {"program": 88, "bank": 0, "icon": "🎛️"}   # New Age Pad
                        }
                    },
                    # Preset 4: Modo tradicional (todas las cuerdas igual instrumento)
                    {
                        "name": "Acoustic Guitar",
                        "program": 24, "bank": 0, "icon": "🎸",
                        "unified": True  # Todas las cuerdas usan el mismo programa
                    },
                    {
                        "name": "Electric Clean",
                        "program": 27, "bank": 0, "icon": "🎸",
                        "unified": True
                    },
                    {
                        "name": "Distortion Guitar",
                        "program": 30, "bank": 0, "icon": "🎸",
                        "unified": True
                    },
                    {
                        "name": "Violin Section",
                        "program": 40, "bank": 0, "icon": "🎻",
                        "unified": True
                    }
                ]
                
                for i, preset in enumerate(default_presets):
                    preset_id = self.preset_start + i
                    if preset_id <= self.preset_end:
                        self.presets[preset_id] = preset
            
            print(f"🎸 TriplePlay: {len(self.presets)} presets configurados")
            
        except Exception as e:
            logger.error(f"Error configurando presets TriplePlay: {e}")
    
    def activate(self):
        """Activar el controlador TriplePlay"""
        try:
            super().activate()
            
            # Abrir puerto MIDI de entrada
            self._open_midi_port()
            
            # Configurar TriplePlay
            self._configure_tripleplay()
            
        except Exception as e:
            logger.error(f"Error activando TriplePlay: {e}")
            self.is_active = False
    
    def deactivate(self):
        """Desactivar el controlador TriplePlay"""
        try:
            # Cerrar puerto MIDI
            self._close_midi_port()
            
            super().deactivate()
            
        except Exception as e:
            logger.error(f"Error desactivando TriplePlay: {e}")
    
    def _open_midi_port(self):
        """Abrir puerto MIDI de entrada"""
        try:
            self.midi_in = rtmidi.MidiIn()
            available_ports = self.midi_in.get_ports()
            
            if self.port_index < len(available_ports):
                self.midi_in.open_port(self.port_index)
                self.midi_in.set_callback(self._midi_callback)
                print(f"🔌 TriplePlay MIDI IN conectado: {available_ports[self.port_index]}")
            else:
                logger.error(f"Puerto MIDI {self.port_index} no disponible")
                
        except Exception as e:
            logger.error(f"Error abriendo puerto MIDI TriplePlay: {e}")
    
    def _close_midi_port(self):
        """Cerrar puerto MIDI"""
        try:
            if self.midi_in:
                self.midi_in.close_port()
                self.midi_in = None
                print("🔌 TriplePlay MIDI IN desconectado")
                
        except Exception as e:
            logger.error(f"Error cerrando puerto MIDI TriplePlay: {e}")
    
    def _configure_tripleplay(self):
        """Configurar TriplePlay con ajustes optimizados"""
        try:
            if not self.midi_in:
                return
            
            # El TriplePlay generalmente se configura desde su app
            # pero podemos establecer algunos parámetros por MIDI
            
            print("⚙️ TriplePlay configurado para modo hexafónico")
            
        except Exception as e:
            logger.error(f"Error configurando TriplePlay: {e}")
    
    def _midi_callback(self, message, delta_time):
        """Callback para mensajes MIDI recibidos"""
        try:
            if not self.is_active:
                return
            
            # Procesar mensaje
            self.handle_midi_message(message[0], delta_time)
            
        except Exception as e:
            logger.error(f"Error en callback MIDI TriplePlay: {e}")
    
    def handle_midi_message(self, message: List[int], delta_time: float):
        """Procesar mensaje MIDI del TriplePlay"""
        try:
            if len(message) < 2:
                return
            
            status = message[0]
            note_or_cc = message[1]
            velocity_or_value = message[2] if len(message) > 2 else 0
            
            # Determinar tipo de mensaje
            msg_type = status & 0xF0
            channel = status & 0x0F
            
            # El TriplePlay envía cada cuerda en un canal diferente (0-5)
            string_number = channel + 1 if channel < 6 else 1
            
            if msg_type == 0x90:  # Note On
                self._handle_string_note_on(string_number, note_or_cc, velocity_or_value)
            elif msg_type == 0x80:  # Note Off
                self._handle_string_note_off(string_number, note_or_cc, velocity_or_value)
            elif msg_type == 0xB0:  # Control Change
                self._handle_control_change(note_or_cc, velocity_or_value, channel)
            elif msg_type == 0xE0:  # Pitch Bend (común en TriplePlay)
                self._handle_pitch_bend(string_number, velocity_or_value, message[2] if len(message) > 2 else 0)
            
        except Exception as e:
            logger.error(f"Error procesando mensaje MIDI TriplePlay: {e}")
    
    def _handle_string_note_on(self, string_number: int, note: int, velocity: int):
        """Manejar Note On por cuerda específica"""
        try:
            if string_number < 1 or string_number > 6:
                return
            
            # Verificar si la cuerda está silenciada
            if self.string_mute.get(string_number, False):
                return
            
            # Aplicar sensibilidad de cuerda
            adjusted_velocity = int(velocity * self.string_sensitivity.get(string_number, 1.0))
            adjusted_velocity = max(1, min(127, adjusted_velocity))
            
            # Actualizar estado de la cuerda
            self.string_states[string_number].update({
                'active': True,
                'last_note': note,
                'last_velocity': adjusted_velocity
            })
            
            # Obtener configuración del preset actual
            current_preset = self.presets.get(self.current_preset, {})
            
            # Determinar canal y programa para esta cuerda
            target_channel = self.string_channels[string_number]
            
            if current_preset.get('unified', False):
                # Modo unificado: todas las cuerdas usan el mismo instrumento
                program = current_preset.get('program', 0)
                bank = current_preset.get('bank', 0)
            else:
                # Modo hexafónico: cada cuerda puede tener su instrumento
                string_config = current_preset.get('strings', {}).get(string_number, {})
                program = string_config.get('program', 24)  # Default: Acoustic Guitar
                bank = string_config.get('bank', 0)
            
            print(f"🎸 TriplePlay Cuerda {string_number}: Nota {note} (vel: {adjusted_velocity}) -> Canal {target_channel}")
            
            # Enviar al sistema principal
            if self.main_system and callable(self.main_system):
                self.main_system('midi_note', {
                    'type': 'note_on',
                    'note': note,
                    'velocity': adjusted_velocity,
                    'channel': target_channel,
                    'controller': self.device_name,
                    'string_number': string_number,
                    'program': program,
                    'bank': bank
                })
            
        except Exception as e:
            logger.error(f"Error en Note On TriplePlay cuerda {string_number}: {e}")
    
    def _handle_string_note_off(self, string_number: int, note: int, velocity: int):
        """Manejar Note Off por cuerda específica"""
        try:
            if string_number < 1 or string_number > 6:
                return
            
            # Actualizar estado de la cuerda
            self.string_states[string_number]['active'] = False
            
            # Determinar canal
            target_channel = self.string_channels[string_number]
            
            # Enviar al sistema principal
            if self.main_system and callable(self.main_system):
                self.main_system('midi_note', {
                    'type': 'note_off',
                    'note': note,
                    'velocity': velocity,
                    'channel': target_channel,
                    'controller': self.device_name,
                    'string_number': string_number
                })
            
        except Exception as e:
            logger.error(f"Error en Note Off TriplePlay cuerda {string_number}: {e}")
    
    def _handle_control_change(self, cc_number: int, value: int, channel: int):
        """Manejar Control Change"""
        try:
            string_number = channel + 1 if channel < 6 else 0
            target_channel = self.string_channels.get(string_number, channel)
            
            print(f"🎛️ TriplePlay CC{cc_number}: {value} (Cuerda {string_number} -> Canal {target_channel})")
            
            # Enviar al sistema principal
            if self.main_system and callable(self.main_system):
                self.main_system('midi_cc', {
                    'cc_number': cc_number,
                    'value': value,
                    'channel': target_channel,
                    'controller': self.device_name,
                    'string_number': string_number
                })
            
        except Exception as e:
            logger.error(f"Error en Control Change TriplePlay: {e}")
    
    def _handle_pitch_bend(self, string_number: int, lsb: int, msb: int):
        """Manejar Pitch Bend por cuerda"""
        try:
            # Combinar LSB y MSB en valor de 14 bits
            pitch_value = (msb << 7) | lsb
            
            target_channel = self.string_channels.get(string_number, 0)
            
            print(f"🎵 TriplePlay Pitch Bend Cuerda {string_number}: {pitch_value} -> Canal {target_channel}")
            
            # Enviar al sistema principal
            if self.main_system and callable(self.main_system):
                self.main_system('midi_pitch_bend', {
                    'value': pitch_value,
                    'channel': target_channel,
                    'controller': self.device_name,
                    'string_number': string_number
                })
            
        except Exception as e:
            logger.error(f"Error en Pitch Bend TriplePlay: {e}")
    
    def _apply_preset(self, preset_id: int) -> bool:
        """Aplicar preset específico del TriplePlay"""
        try:
            if preset_id not in self.presets:
                return False
            
            preset_info = self.presets[preset_id]
            
            if preset_info.get('unified', False):
                # Modo unificado: configurar el mismo instrumento en todos los canales
                program = preset_info.get('program', 0)
                bank = preset_info.get('bank', 0)
                
                for string_num in range(1, 7):
                    channel = self.string_channels[string_num]
                    
                    if self.main_system and callable(self.main_system):
                        self.main_system('apply_preset', {
                            'controller': self.device_name,
                            'preset_id': preset_id,
                            'channel': channel,
                            'program': program,
                            'bank': bank,
                            'string_number': string_num
                        })
            else:
                # Modo hexafónico: configurar instrumento diferente por cuerda
                strings_config = preset_info.get('strings', {})
                
                for string_num, string_config in strings_config.items():
                    if isinstance(string_num, str):
                        string_num = int(string_num)
                    
                    if 1 <= string_num <= 6:
                        channel = self.string_channels[string_num]
                        program = string_config.get('program', 0)
                        bank = string_config.get('bank', 0)
                        
                        if self.main_system and callable(self.main_system):
                            self.main_system('apply_preset', {
                                'controller': self.device_name,
                                'preset_id': preset_id,
                                'channel': channel,
                                'program': program,
                                'bank': bank,
                                'string_number': string_num
                            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error aplicando preset TriplePlay {preset_id}: {e}")
            return False
    
    def requires_monitoring(self) -> bool:
        """TriplePlay requiere monitoreo para mensajes MIDI"""
        return True
    
    def _monitor_step(self):
        """Paso de monitoreo específico del TriplePlay"""
        try:
            # Verificar si el puerto MIDI sigue disponible
            if self.midi_in and not self.midi_in.is_port_open():
                print("⚠️ TriplePlay: Puerto MIDI desconectado, intentando reconectar...")
                self._open_midi_port()
            
        except Exception as e:
            logger.error(f"Error en monitoreo TriplePlay: {e}")
    
    def set_string_sensitivity(self, string_number: int, sensitivity: float):
        """Establecer sensibilidad de una cuerda específica"""
        try:
            if 1 <= string_number <= 6 and 0.1 <= sensitivity <= 2.0:
                self.string_sensitivity[string_number] = sensitivity
                print(f"🎸 TriplePlay Cuerda {string_number}: Sensibilidad = {sensitivity}")
                
        except Exception as e:
            logger.error(f"Error estableciendo sensibilidad TriplePlay: {e}")
    
    def mute_string(self, string_number: int, muted: bool = True):
        """Silenciar/activar una cuerda específica"""
        try:
            if 1 <= string_number <= 6:
                self.string_mute[string_number] = muted
                status = "silenciada" if muted else "activada"
                print(f"🔇 TriplePlay Cuerda {string_number}: {status}")
                
        except Exception as e:
            logger.error(f"Error silenciando cuerda TriplePlay: {e}")
    
    def get_string_status(self) -> Dict[str, Any]:
        """Obtener estado de todas las cuerdas"""
        return {
            'strings': self.string_states.copy(),
            'sensitivity': self.string_sensitivity.copy(),
            'muted': self.string_mute.copy(),
            'channels': self.string_channels.copy(),
            'current_preset': self.current_preset,
            'polyphonic_mode': self.polyphonic_mode
        }