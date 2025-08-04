#!/usr/bin/env python3
"""
🎹 Akai MPK Mini Controller
Controlador específico para Akai MPK Mini (todas las versiones)
"""

import time
import rtmidi
from typing import List, Dict, Any
from ..instrument_controller import InstrumentController
import logging

logger = logging.getLogger(__name__)

class AkaiMPKMiniController(InstrumentController):
    """Controlador para Akai MPK Mini"""
    
    def __init__(self, device_name: str, device_info: Dict[str, Any], main_system_callback=None):
        # Configuración específica del MPK Mini
        self.midi_in = None
        self.port_index = device_info.get('port_index', 0)
        
        # Mapeo de controles del MPK Mini
        self.control_map = {
            # Knobs (CC)
            1: 'modulation',
            2: 'breath',
            3: 'vibrato_rate',
            4: 'cutoff',
            5: 'attack',
            6: 'decay',
            7: 'volume',
            8: 'sustain',
            
            # Pads (notas en canal 10 por defecto)
            36: 'pad_1',   # C2
            37: 'pad_2',   # C#2
            38: 'pad_3',   # D2
            39: 'pad_4',   # D#2
            40: 'pad_5',   # E2
            41: 'pad_6',   # F2
            42: 'pad_7',   # F#2
            43: 'pad_8'    # G2
        }
        
        # Estado de los controles
        self.knob_values = {i: 64 for i in range(1, 9)}  # Valores medios por defecto
        self.pad_states = {i: False for i in range(36, 44)}
        
        super().__init__(device_name, device_info, main_system_callback)
    
    def setup_presets(self):
        """Configurar presets específicos del MPK Mini"""
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
                # Presets por defecto optimizados para MPK Mini
                default_presets = [
                    {"name": "Grand Piano", "program": 0, "bank": 0, "icon": "🎹"},
                    {"name": "Electric Piano", "program": 4, "bank": 0, "icon": "🎹"},
                    {"name": "Hammond Organ", "program": 16, "bank": 0, "icon": "🎹"},
                    {"name": "Analog Synth", "program": 80, "bank": 0, "icon": "🎛️"},
                    {"name": "Synth Bass", "program": 38, "bank": 0, "icon": "🎸"},
                    {"name": "Synth Strings", "program": 50, "bank": 0, "icon": "🎻"},
                    {"name": "Synth Brass", "program": 62, "bank": 0, "icon": "🎺"},
                    {"name": "Synth Lead", "program": 81, "bank": 0, "icon": "🎛️"}
                ]
                
                for i, preset in enumerate(default_presets):
                    preset_id = self.preset_start + i
                    if preset_id <= self.preset_end:
                        self.presets[preset_id] = {
                            'name': preset['name'],
                            'program': preset['program'],
                            'bank': preset['bank'],
                            'channel': self.midi_channel,
                            'icon': preset['icon']
                        }
            
            print(f"🎹 MPK Mini: {len(self.presets)} presets configurados")
            
        except Exception as e:
            logger.error(f"Error configurando presets MPK Mini: {e}")
    
    def activate(self):
        """Activar el controlador MPK Mini"""
        try:
            super().activate()
            
            # Abrir puerto MIDI de entrada
            self._open_midi_port()
            
            # Configurar MPK Mini
            self._configure_mpk_mini()
            
        except Exception as e:
            logger.error(f"Error activando MPK Mini: {e}")
            self.is_active = False
    
    def deactivate(self):
        """Desactivar el controlador MPK Mini"""
        try:
            # Cerrar puerto MIDI
            self._close_midi_port()
            
            super().deactivate()
            
        except Exception as e:
            logger.error(f"Error desactivando MPK Mini: {e}")
    
    def _open_midi_port(self):
        """Abrir puerto MIDI de entrada"""
        try:
            self.midi_in = rtmidi.MidiIn()
            available_ports = self.midi_in.get_ports()
            
            if self.port_index < len(available_ports):
                self.midi_in.open_port(self.port_index)
                self.midi_in.set_callback(self._midi_callback)
                print(f"🔌 MPK Mini MIDI IN conectado: {available_ports[self.port_index]}")
            else:
                logger.error(f"Puerto MIDI {self.port_index} no disponible")
                
        except Exception as e:
            logger.error(f"Error abriendo puerto MIDI MPK Mini: {e}")
    
    def _close_midi_port(self):
        """Cerrar puerto MIDI"""
        try:
            if self.midi_in:
                self.midi_in.close_port()
                self.midi_in = None
                print("🔌 MPK Mini MIDI IN desconectado")
                
        except Exception as e:
            logger.error(f"Error cerrando puerto MIDI MPK Mini: {e}")
    
    def _configure_mpk_mini(self):
        """Configurar MPK Mini con ajustes optimizados"""
        try:
            if not self.midi_in:
                return
            
            # Enviar configuración inicial (si es necesario)
            # El MPK Mini generalmente no necesita configuración especial
            # pero podemos enviar algunos CC para establecer valores iniciales
            
            print("⚙️ MPK Mini configurado")
            
        except Exception as e:
            logger.error(f"Error configurando MPK Mini: {e}")
    
    def _midi_callback(self, message, delta_time):
        """Callback para mensajes MIDI recibidos"""
        try:
            if not self.is_active:
                return
            
            # Procesar mensaje
            self.handle_midi_message(message[0], delta_time)
            
        except Exception as e:
            logger.error(f"Error en callback MIDI MPK Mini: {e}")
    
    def handle_midi_message(self, message: List[int], delta_time: float):
        """Procesar mensaje MIDI del MPK Mini"""
        try:
            if len(message) < 2:
                return
            
            status = message[0]
            note_or_cc = message[1]
            velocity_or_value = message[2] if len(message) > 2 else 0
            
            # Determinar tipo de mensaje
            msg_type = status & 0xF0
            channel = status & 0x0F
            
            if msg_type == 0x90:  # Note On
                self._handle_note_on(note_or_cc, velocity_or_value, channel)
            elif msg_type == 0x80:  # Note Off
                self._handle_note_off(note_or_cc, velocity_or_value, channel)
            elif msg_type == 0xB0:  # Control Change
                self._handle_control_change(note_or_cc, velocity_or_value, channel)
            elif msg_type == 0xC0:  # Program Change
                self._handle_program_change(note_or_cc, channel)
            
        except Exception as e:
            logger.error(f"Error procesando mensaje MIDI MPK Mini: {e}")
    
    def _handle_note_on(self, note: int, velocity: int, channel: int):
        """Manejar Note On"""
        try:
            # Verificar si es un pad
            if note in self.control_map and 36 <= note <= 43:
                pad_name = self.control_map[note]
                self.pad_states[note] = True
                print(f"🥁 MPK Mini Pad: {pad_name} ON (velocity: {velocity})")
                
                # Activar preset si el pad corresponde a uno
                pad_num = note - 36  # Pads 0-7
                preset_id = self.preset_start + pad_num
                
                if preset_id in self.presets:
                    self.change_preset(preset_id)
            
            # Reenviar nota al sistema principal para síntesis
            if self.main_system and callable(self.main_system):
                self.main_system('midi_note', {
                    'type': 'note_on',
                    'note': note,
                    'velocity': velocity,
                    'channel': self.midi_channel,
                    'controller': self.device_name
                })
            
        except Exception as e:
            logger.error(f"Error en Note On MPK Mini: {e}")
    
    def _handle_note_off(self, note: int, velocity: int, channel: int):
        """Manejar Note Off"""
        try:
            # Actualizar estado de pads
            if note in self.pad_states:
                self.pad_states[note] = False
            
            # Reenviar nota al sistema principal
            if self.main_system and callable(self.main_system):
                self.main_system('midi_note', {
                    'type': 'note_off',
                    'note': note,
                    'velocity': velocity,
                    'channel': self.midi_channel,
                    'controller': self.device_name
                })
            
        except Exception as e:
            logger.error(f"Error en Note Off MPK Mini: {e}")
    
    def _handle_control_change(self, cc_number: int, value: int, channel: int):
        """Manejar Control Change"""
        try:
            if cc_number in self.control_map:
                control_name = self.control_map[cc_number]
                self.knob_values[cc_number] = value
                
                print(f"🎛️ MPK Mini Knob: {control_name} = {value}")
                
                # Aplicar control change al sistema principal
                if self.main_system and callable(self.main_system):
                    self.main_system('midi_cc', {
                        'cc_number': cc_number,
                        'value': value,
                        'channel': self.midi_channel,
                        'controller': self.device_name,
                        'control_name': control_name
                    })
            
        except Exception as e:
            logger.error(f"Error en Control Change MPK Mini: {e}")
    
    def _handle_program_change(self, program: int, channel: int):
        """Manejar Program Change"""
        try:
            # Cambiar preset basado en el program change
            preset_id = self.preset_start + (program % len(self.presets))
            
            if preset_id in self.presets:
                self.change_preset(preset_id)
            
        except Exception as e:
            logger.error(f"Error en Program Change MPK Mini: {e}")
    
    def requires_monitoring(self) -> bool:
        """MPK Mini requiere monitoreo para mensajes MIDI"""
        return True
    
    def _monitor_step(self):
        """Paso de monitoreo específico del MPK Mini"""
        try:
            # Verificar si el puerto MIDI sigue disponible
            if self.midi_in and not self.midi_in.is_port_open():
                print("⚠️ MPK Mini: Puerto MIDI desconectado, intentando reconectar...")
                self._open_midi_port()
            
        except Exception as e:
            logger.error(f"Error en monitoreo MPK Mini: {e}")
    
    def get_control_values(self) -> Dict[str, Any]:
        """Obtener valores actuales de los controles"""
        return {
            'knobs': {self.control_map.get(cc, f'CC{cc}'): value for cc, value in self.knob_values.items()},
            'pads': {self.control_map.get(note, f'Pad{note-35}'): state for note, state in self.pad_states.items()},
            'current_preset': self.current_preset,
            'preset_info': self.presets.get(self.current_preset, {})
        }
    
    def set_knob_value(self, knob_number: int, value: int):
        """Establecer valor de un knob programáticamente"""
        try:
            if 1 <= knob_number <= 8 and 0 <= value <= 127:
                self.knob_values[knob_number] = value
                
                # Enviar CC al sistema principal
                if self.main_system and callable(self.main_system):
                    self.main_system('midi_cc', {
                        'cc_number': knob_number,
                        'value': value,
                        'channel': self.midi_channel,
                        'controller': self.device_name,
                        'control_name': self.control_map.get(knob_number, f'Knob{knob_number}')
                    })
                
        except Exception as e:
            logger.error(f"Error estableciendo valor de knob MPK Mini: {e}")
    
    def trigger_pad(self, pad_number: int, velocity: int = 127):
        """Disparar un pad programáticamente"""
        try:
            if 1 <= pad_number <= 8:
                note = 35 + pad_number  # Pads están en notas 36-43
                self._handle_note_on(note, velocity, 0)
                
        except Exception as e:
            logger.error(f"Error disparando pad MPK Mini: {e}")