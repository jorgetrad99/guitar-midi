#!/usr/bin/env python3
"""
🎸 Guitar-MIDI Modular System v2.0
Sistema modular para múltiples controladores MIDI específicos

Arquitectura:
- MVAVE Pocket Controller → 4 presets percusivos (canal 9)
- Hexaphonic Controller → 6 cuerdas → canales melódicos (0-5)  
- MIDI Captain Controller → control maestro de presets
- Interfaz web modular con configuración por dispositivo
- Sistema de presets configurables al 100%
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
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

# Verificar dependencias críticas
try:
    import rtmidi
    import fluidsynth
    from flask import Flask, render_template_string, jsonify, request
    from flask_socketio import SocketIO, emit
except ImportError as e:
    print(f"❌ Error: Dependencia faltante: {e}")
    print("💡 Instalar con: pip install python-rtmidi pyfluidsynth Flask Flask-SocketIO")
    sys.exit(1)

# ========================================================================================
# CLASES BASE Y ENUMS
# ========================================================================================

class ControllerType(Enum):
    """Tipos de controladores MIDI soportados"""
    MVAVE_POCKET = "mvave_pocket"
    HEXAPHONIC = "hexaphonic" 
    MIDI_CAPTAIN = "midi_captain"
    GENERIC = "generic"

class InstrumentCategory(Enum):
    """Categorías de instrumentos General MIDI"""
    PIANO = "piano"
    PERCUSSION = "percussion"
    GUITAR = "guitar"
    BASS = "bass"
    STRINGS = "strings"
    BRASS = "brass"
    REED = "reed"
    PIPE = "pipe"
    SYNTH_LEAD = "synth_lead"
    SYNTH_PAD = "synth_pad"
    ETHNIC = "ethnic"
    SOUND_EFFECTS = "sound_effects"

@dataclass
class PresetConfig:
    """Configuración de un preset"""
    id: int
    name: str
    program: int
    bank: int
    channel: int
    category: InstrumentCategory
    icon: str
    volume: int = 100
    reverb: int = 40
    chorus: int = 20
    cutoff: int = 64
    resonance: int = 64

@dataclass
class ControllerConfig:
    """Configuración de un controlador MIDI"""
    controller_type: ControllerType
    device_patterns: List[str]
    channels: List[int]
    max_presets: int
    default_category: InstrumentCategory
    midi_mappings: Dict[str, Any]
    effects_config: Dict[str, int]

# ========================================================================================
# CONTROLADOR BASE
# ========================================================================================

class MIDIController(ABC):
    """Clase base para controladores MIDI específicos"""
    
    def __init__(self, controller_type: ControllerType, device_patterns: List[str]):
        self.controller_type = controller_type
        self.device_patterns = device_patterns
        self.device_name = None
        self.client_port = None
        self.is_connected = False
        self.presets: Dict[int, PresetConfig] = {}
        self.current_preset = 0
        self.midi_mappings = {}
        self.effects_config = {}
        
    @abstractmethod
    def setup_presets(self) -> None:
        """Configurar presets específicos del controlador"""
        pass
    
    @abstractmethod
    def handle_midi_message(self, message: List[int], timestamp: float) -> bool:
        """Procesar mensaje MIDI específico del controlador"""
        pass
    
    def get_config(self) -> ControllerConfig:
        """Obtener configuración del controlador"""
        return ControllerConfig(
            controller_type=self.controller_type,
            device_patterns=self.device_patterns,
            channels=list(self.presets.keys()),
            max_presets=len(self.presets),
            default_category=InstrumentCategory.PIANO,
            midi_mappings=self.midi_mappings,
            effects_config=self.effects_config
        )
    
    def set_preset(self, preset_id: int, audio_engine) -> bool:
        """Cambiar a un preset específico"""
        if preset_id not in self.presets:
            return False
            
        preset = self.presets[preset_id]
        success = audio_engine.set_instrument(
            preset.channel, preset.bank, preset.program
        )
        
        if success:
            # Aplicar efectos del preset
            audio_engine.set_channel_effects(
                preset.channel, 
                volume=preset.volume,
                reverb=preset.reverb,
                chorus=preset.chorus,
                cutoff=preset.cutoff,
                resonance=preset.resonance
            )
            self.current_preset = preset_id
            print(f"🎹 {self.controller_type.value}: Preset {preset_id} - {preset.name}")
            
        return success

# ========================================================================================
# CONTROLADORES ESPECÍFICOS
# ========================================================================================

class MVAVEPocketController(MIDIController):
    """Controlador MVAVE Pocket - 4 presets percusivos"""
    
    def __init__(self):
        super().__init__(
            ControllerType.MVAVE_POCKET, 
            ["MVAVE.*Pocket", "Pocket.*MVAVE", "MVAVE.*"]
        )
        self.setup_presets()
        self.setup_midi_mappings()
    
    def setup_presets(self):
        """4 presets percusivos optimizados"""
        self.presets = {
            0: PresetConfig(
                id=0, name="Standard Kit", program=0, bank=128, channel=9,
                category=InstrumentCategory.PERCUSSION, icon="🥁",
                volume=100, reverb=30, chorus=10
            ),
            1: PresetConfig(
                id=1, name="Rock Kit", program=16, bank=128, channel=9,
                category=InstrumentCategory.PERCUSSION, icon="🤘",
                volume=110, reverb=20, chorus=5
            ),
            2: PresetConfig(
                id=2, name="Electronic Kit", program=25, bank=128, channel=9,
                category=InstrumentCategory.PERCUSSION, icon="🔊",
                volume=105, reverb=50, chorus=30
            ),
            3: PresetConfig(
                id=3, name="Jazz Kit", program=32, bank=128, channel=9,
                category=InstrumentCategory.PERCUSSION, icon="🎷",
                volume=95, reverb=40, chorus=15
            )
        }
    
    def setup_midi_mappings(self):
        """Mapeo MIDI específico para MVAVE Pocket"""
        self.midi_mappings = {
            'preset_change_notes': [36, 37, 38, 39],  # C2, C#2, D2, D#2 para cambiar presets
            'velocity_curve': 'linear',
            'note_range': (35, 81),  # Rango GM drums
            'pad_sensitivity': 127
        }
    
    def handle_midi_message(self, message: List[int], timestamp: float) -> bool:
        """Procesar mensajes MIDI del MVAVE Pocket"""
        if len(message) < 2:
            return False
            
        status, data1 = message[0], message[1]
        velocity = message[2] if len(message) > 2 else 64
        
        # Note On para cambio de presets
        if (status & 0xF0) == 0x90 and velocity > 0:
            if data1 in self.midi_mappings['preset_change_notes']:
                preset_id = self.midi_mappings['preset_change_notes'].index(data1)
                print(f"🥁 MVAVE: Cambio a preset {preset_id} via nota {data1}")
                return True
        
        # Program Change directo
        elif (status & 0xF0) == 0xC0:
            if 0 <= data1 <= 3:
                print(f"🥁 MVAVE: Program Change a preset {data1}")
                return True
                
        return False

class HexaphonicController(MIDIController):
    """Controlador Hexafónico - 6 cuerdas → canales melódicos"""
    
    def __init__(self):
        super().__init__(
            ControllerType.HEXAPHONIC,
            ["HEX.*", "Hexaphonic.*", "Guitar.*Synth", ".*Hexaphonic.*"]
        )
        self.setup_presets()
        self.setup_midi_mappings()
    
    def setup_presets(self):
        """Presets por cuerda - sintetizadores, cuerdas, vientos"""
        self.presets = {
            # Cuerda E grave (Canal 0) - Bass/Low instruments
            0: PresetConfig(
                id=0, name="Synth Bass", program=38, bank=0, channel=0,
                category=InstrumentCategory.BASS, icon="🎸",
                volume=110, reverb=20, chorus=10
            ),
            # Cuerda A (Canal 1) - Strings/Ensemble
            1: PresetConfig(
                id=1, name="String Ensemble", program=48, bank=0, channel=1,
                category=InstrumentCategory.STRINGS, icon="🎻",
                volume=100, reverb=50, chorus=25
            ),
            # Cuerda D (Canal 2) - Synth Lead
            2: PresetConfig(
                id=2, name="Lead Synth", program=80, bank=0, channel=2,
                category=InstrumentCategory.SYNTH_LEAD, icon="🎹",
                volume=105, reverb=30, chorus=20
            ),
            # Cuerda G (Canal 3) - Brass
            3: PresetConfig(
                id=3, name="Trumpet Section", program=56, bank=0, channel=3,
                category=InstrumentCategory.BRASS, icon="🎺",
                volume=100, reverb=25, chorus=15
            ),
            # Cuerda B (Canal 4) - Reed/Woodwinds
            4: PresetConfig(
                id=4, name="Tenor Sax", program=66, bank=0, channel=4,
                category=InstrumentCategory.REED, icon="🎷",
                volume=95, reverb=35, chorus=18
            ),
            # Cuerda E aguda (Canal 5) - Pipe/Flutes
            5: PresetConfig(
                id=5, name="Flute", program=73, bank=0, channel=5,
                category=InstrumentCategory.PIPE, icon="🪈",
                volume=90, reverb=40, chorus=22
            )
        }
    
    def setup_midi_mappings(self):
        """Mapeo MIDI para controlador hexafónico"""
        self.midi_mappings = {
            'string_channels': {
                'E_low': 0,   # Cuerda E grave → Canal 0
                'A': 1,       # Cuerda A → Canal 1  
                'D': 2,       # Cuerda D → Canal 2
                'G': 3,       # Cuerda G → Canal 3
                'B': 4,       # Cuerda B → Canal 4
                'E_high': 5   # Cuerda E aguda → Canal 5
            },
            'note_ranges': {
                0: (40, 52),  # E2-E3 (E grave)
                1: (45, 57),  # A2-A3 (A)
                2: (50, 62),  # D3-D4 (D)
                3: (55, 67),  # G3-G4 (G)
                4: (59, 71),  # B3-B4 (B)
                5: (64, 76)   # E4-E5 (E aguda)
            },
            'bend_range': 2,  # Semitones
            'expression_cc': 11
        }
    
    def handle_midi_message(self, message: List[int], timestamp: float) -> bool:
        """Procesar mensajes MIDI del controlador hexafónico"""
        if len(message) < 2:
            return False
            
        status, data1 = message[0], message[1]
        channel = status & 0x0F
        velocity = message[2] if len(message) > 2 else 64
        
        # Verificar que el canal esté en nuestro rango (0-5)
        if channel not in range(6):
            return False
            
        # Note On/Off - routing por canal de cuerda
        if (status & 0xF0) in [0x90, 0x80]:
            note_ranges = self.midi_mappings['note_ranges']
            if channel in note_ranges:
                min_note, max_note = note_ranges[channel]
                if min_note <= data1 <= max_note:
                    print(f"🎸 HEX: Cuerda {channel} → Nota {data1} (vel: {velocity})")
                    return True
        
        # Control Change para expresión
        elif (status & 0xF0) == 0xB0:
            if data1 == self.midi_mappings['expression_cc']:
                print(f"🎸 HEX: Expression cuerda {channel} → {velocity}")
                return True
        
        return False

class MIDICaptainController(MIDIController):
    """MIDI Captain - Control maestro de presets"""
    
    def __init__(self):
        super().__init__(
            ControllerType.MIDI_CAPTAIN,
            [".*Captain.*", "Captain.*", "Pico.*Captain.*", "MIDI.*Captain.*"]
        )
        self.setup_presets()
        self.setup_midi_mappings()
    
    def setup_presets(self):
        """Presets de control maestro - 8 configuraciones globales"""
        self.presets = {
            0: PresetConfig(
                id=0, name="Rock Setup", program=0, bank=0, channel=15,
                category=InstrumentCategory.GUITAR, icon="🤘",
                volume=100, reverb=25, chorus=15
            ),
            1: PresetConfig(
                id=1, name="Jazz Setup", program=0, bank=0, channel=15,
                category=InstrumentCategory.PIANO, icon="🎷",
                volume=90, reverb=45, chorus=25
            ),
            2: PresetConfig(
                id=2, name="Electronic Setup", program=0, bank=0, channel=15,
                category=InstrumentCategory.SYNTH_LEAD, icon="🔊",
                volume=110, reverb=60, chorus=40
            ),
            3: PresetConfig(
                id=3, name="Classical Setup", program=0, bank=0, channel=15,
                category=InstrumentCategory.STRINGS, icon="🎻",
                volume=95, reverb=55, chorus=20
            ),
            4: PresetConfig(
                id=4, name="Funk Setup", program=0, bank=0, channel=15,
                category=InstrumentCategory.BASS, icon="🎸",
                volume=105, reverb=20, chorus=10
            ),
            5: PresetConfig(
                id=5, name="Ambient Setup", program=0, bank=0, channel=15,
                category=InstrumentCategory.SYNTH_PAD, icon="🌊",
                volume=85, reverb=80, chorus=50
            ),
            6: PresetConfig(
                id=6, name="Latin Setup", program=0, bank=0, channel=15,
                category=InstrumentCategory.ETHNIC, icon="🪘",
                volume=100, reverb=35, chorus=30
            ),
            7: PresetConfig(
                id=7, name="Experimental Setup", program=0, bank=0, channel=15,
                category=InstrumentCategory.SOUND_EFFECTS, icon="🚀",
                volume=120, reverb=70, chorus=60
            )
        }
    
    def setup_midi_mappings(self):
        """Mapeo MIDI para MIDI Captain"""
        self.midi_mappings = {
            'preset_buttons': list(range(8)),  # Botones 0-7 para presets
            'bank_select': [0, 32],  # CC 0 y 32 para bank select
            'effect_controls': {
                'volume': 7,      # CC 7
                'reverb': 91,     # CC 91  
                'chorus': 93,     # CC 93
                'cutoff': 74,     # CC 74
                'resonance': 71,  # CC 71
                'expression': 11  # CC 11
            },
            'global_functions': {
                'panic': 120,     # CC 120 - All Sound Off
                'reset': 121      # CC 121 - Reset All Controllers
            }
        }
    
    def handle_midi_message(self, message: List[int], timestamp: float) -> bool:
        """Procesar mensajes MIDI del MIDI Captain"""
        if len(message) < 2:
            return False
            
        status, data1 = message[0], message[1]
        value = message[2] if len(message) > 2 else 0
        
        # Program Change para presets globales
        if (status & 0xF0) == 0xC0:
            if 0 <= data1 <= 7:
                print(f"🎚️ CAPTAIN: Preset global {data1}")
                return True
        
        # Control Change para efectos
        elif (status & 0xF0) == 0xB0:
            effect_controls = self.midi_mappings['effect_controls']
            
            if data1 == effect_controls['volume']:
                print(f"🎚️ CAPTAIN: Volumen global → {value}")
                return True
            elif data1 == effect_controls['reverb']:
                print(f"🎚️ CAPTAIN: Reverb global → {value}")
                return True
            elif data1 == effect_controls['chorus']:
                print(f"🎚️ CAPTAIN: Chorus global → {value}")
                return True
            elif data1 in self.midi_mappings['global_functions'].values():
                print(f"🎚️ CAPTAIN: Función global CC{data1}")
                return True
                
        return False

# ========================================================================================
# MOTOR DE AUDIO MEJORADO
# ========================================================================================

class AudioEngine:
    """Motor de audio FluidSynth multi-canal mejorado"""
    
    def __init__(self):
        self.fs = None
        self.sfid = None
        self.audio_device = None
        self.channel_instruments = {}  # Canal → Instrumento actual
        self.channel_effects = {}      # Canal → Efectos actuales
        
    def initialize(self, audio_device: str = None) -> bool:
        """Inicializar FluidSynth con configuración multi-canal"""
        try:
            print("🎹 Inicializando AudioEngine multi-canal...")
            self.fs = fluidsynth.Synth(gain=1.0, samplerate=44100)
            
            # Configuración optimizada para múltiples canales
            self.fs.setting('synth.midi-channels', 32)  # 32 canales internos
            self.fs.setting('audio.driver', 'alsa')
            if audio_device:
                self.fs.setting('audio.alsa.device', audio_device)
            self.fs.setting('synth.gain', 1.5)
            self.fs.setting('synth.effects-groups', 8)  # 8 grupos de efectos
            
            self.fs.start()
            
            # Cargar SoundFont
            sf_path = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
            if os.path.exists(sf_path):
                self.sfid = self.fs.sfload(sf_path)
                print(f"   ✅ SoundFont cargado: {sf_path}")
            else:
                print(f"   ⚠️  SoundFont no encontrado: {sf_path}")
                return False
            
            # Inicializar efectos por canal
            self._initialize_channel_effects()
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando AudioEngine: {e}")
            return False
    
    def _initialize_channel_effects(self):
        """Inicializar efectos por canal"""
        for channel in range(16):
            self.channel_effects[channel] = {
                'volume': 100,
                'reverb': 40,
                'chorus': 20,
                'cutoff': 64,
                'resonance': 64
            }
    
    def set_instrument(self, channel: int, bank: int, program: int) -> bool:
        """Configurar instrumento en canal específico"""
        try:
            if self.fs and self.sfid is not None:
                # Bank Select
                self.fs.cc(channel, 0, (bank >> 7) & 0x7F)  # MSB
                self.fs.cc(channel, 32, bank & 0x7F)        # LSB
                
                # Program Change
                self.fs.program_select(channel, self.sfid, bank, program)
                
                self.channel_instruments[channel] = {
                    'bank': bank, 'program': program
                }
                
                print(f"   🎹 Canal {channel}: Bank {bank}, Program {program}")
                return True
            return False
        except Exception as e:
            print(f"❌ Error configurando instrumento canal {channel}: {e}")
            return False
    
    def set_channel_effects(self, channel: int, volume: int = None, 
                           reverb: int = None, chorus: int = None,
                           cutoff: int = None, resonance: int = None) -> bool:
        """Configurar efectos específicos por canal"""
        try:
            if not self.fs:
                return False
                
            effects = self.channel_effects.get(channel, {})
            
            if volume is not None:
                self.fs.cc(channel, 7, min(127, max(0, volume)))
                effects['volume'] = volume
                
            if reverb is not None:
                self.fs.cc(channel, 91, min(127, max(0, reverb)))
                effects['reverb'] = reverb
                
            if chorus is not None:
                self.fs.cc(channel, 93, min(127, max(0, chorus)))
                effects['chorus'] = chorus
                
            if cutoff is not None:
                self.fs.cc(channel, 74, min(127, max(0, cutoff)))
                effects['cutoff'] = cutoff
                
            if resonance is not None:
                self.fs.cc(channel, 71, min(127, max(0, resonance)))
                effects['resonance'] = resonance
            
            self.channel_effects[channel] = effects
            return True
            
        except Exception as e:
            print(f"❌ Error configurando efectos canal {channel}: {e}")
            return False
    
    def note_on(self, channel: int, note: int, velocity: int) -> bool:
        """Tocar nota en canal específico"""
        try:
            if self.fs:
                self.fs.noteon(channel, note, velocity)
                return True
            return False
        except Exception as e:
            print(f"❌ Error note_on canal {channel}: {e}")
            return False
    
    def note_off(self, channel: int, note: int) -> bool:
        """Detener nota en canal específico"""
        try:
            if self.fs:
                self.fs.noteoff(channel, note)
                return True
            return False
        except Exception as e:
            print(f"❌ Error note_off canal {channel}: {e}")
            return False
    
    def panic(self) -> bool:
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
    
    def get_channel_status(self, channel: int) -> Dict[str, Any]:
        """Obtener estado actual de un canal"""
        return {
            'instrument': self.channel_instruments.get(channel, {}),
            'effects': self.channel_effects.get(channel, {}),
            'active': channel in self.channel_instruments
        }
    
    def stop(self):
        """Detener AudioEngine"""
        if self.fs:
            try:
                self.fs.delete()
            except:
                pass
        print("✅ AudioEngine detenido")

# ========================================================================================
# GESTOR DE DISPOSITIVOS MIDI
# ========================================================================================

class DeviceManager:
    """Gestor de múltiples controladores MIDI"""
    
    def __init__(self, audio_engine: AudioEngine):
        self.audio_engine = audio_engine
        self.controllers: Dict[str, MIDIController] = {}
        self.midi_inputs: Dict[str, rtmidi.MidiIn] = {}
        self.device_mappings: Dict[str, str] = {}  # device_name → controller_type
        self.monitoring = False
        self.monitor_thread = None
        
    def initialize(self) -> bool:
        """Inicializar gestor de dispositivos"""
        try:
            print("🎛️ Inicializando DeviceManager...")
            
            # Registrar controladores disponibles
            self._register_controllers()
            
            # Detectar y conectar dispositivos existentes
            self._detect_and_connect_devices()
            
            # Iniciar monitoreo de hot-plug
            self._start_monitoring()
            
            return True
        except Exception as e:
            print(f"❌ Error inicializando DeviceManager: {e}")
            return False
    
    def _register_controllers(self):
        """Registrar tipos de controladores disponibles"""
        # MVAVE Pocket Controller
        mvave = MVAVEPocketController()
        self.controllers['mvave_pocket'] = mvave
        
        # Hexaphonic Controller  
        hexaphonic = HexaphonicController()
        self.controllers['hexaphonic'] = hexaphonic
        
        # MIDI Captain Controller
        captain = MIDICaptainController()
        self.controllers['midi_captain'] = captain
        
        print(f"   📝 Registrados {len(self.controllers)} tipos de controladores")
    
    def _detect_and_connect_devices(self):
        """Detectar y conectar dispositivos MIDI existentes"""
        try:
            midi_in = rtmidi.MidiIn()
            available_ports = midi_in.get_ports()
            
            print(f"   🔍 Detectando dispositivos MIDI...")
            for i, port_name in enumerate(available_ports):
                print(f"      {i}: {port_name}")
                controller = self._match_device_to_controller(port_name)
                if controller:
                    self._connect_device(port_name, i, controller)
            
        except Exception as e:
            print(f"⚠️  Error detectando dispositivos: {e}")
    
    def _match_device_to_controller(self, device_name: str) -> Optional[MIDIController]:
        """Hacer match de dispositivo con controlador específico"""
        for controller in self.controllers.values():
            for pattern in controller.device_patterns:
                if re.search(pattern, device_name, re.IGNORECASE):
                    print(f"      ✅ Match: {device_name} → {controller.controller_type.value}")
                    return controller
        return None
    
    def _connect_device(self, device_name: str, port_index: int, controller: MIDIController):
        """Conectar dispositivo MIDI específico"""
        try:
            # Crear entrada MIDI para este dispositivo
            midi_input = rtmidi.MidiIn()
            midi_input.open_port(port_index)
            
            # Configurar callback específico
            def device_callback(message, data):
                self._handle_device_message(controller, message, data)
            
            midi_input.set_callback(device_callback)
            
            # Registrar dispositivo
            self.midi_inputs[device_name] = midi_input
            self.device_mappings[device_name] = controller.controller_type.value
            controller.device_name = device_name
            controller.is_connected = True
            
            # Configurar presets del controlador en AudioEngine
            self._setup_controller_presets(controller)
            
            print(f"      🔗 Conectado: {device_name} ({controller.controller_type.value})")
            
        except Exception as e:
            print(f"❌ Error conectando {device_name}: {e}")
    
    def _setup_controller_presets(self, controller: MIDIController):
        """Configurar presets del controlador en AudioEngine"""
        for preset_id, preset in controller.presets.items():
            success = self.audio_engine.set_instrument(
                preset.channel, preset.bank, preset.program
            )
            if success:
                self.audio_engine.set_channel_effects(
                    preset.channel,
                    volume=preset.volume,
                    reverb=preset.reverb,
                    chorus=preset.chorus,
                    cutoff=preset.cutoff,
                    resonance=preset.resonance
                )
        
        # Activar preset 0 por defecto
        if 0 in controller.presets:
            controller.set_preset(0, self.audio_engine)
    
    def _handle_device_message(self, controller: MIDIController, message, timestamp):
        """Manejar mensaje MIDI de dispositivo específico"""
        try:
            msg, delta_time = message
            
            # Procesar mensaje con el controlador específico
            handled = controller.handle_midi_message(msg, timestamp)
            
            if handled:
                # Si el controlador indica cambio de preset, procesarlo
                self._process_controller_action(controller, msg)
            else:
                # Enviar mensaje MIDI directo al AudioEngine
                self._forward_midi_message(controller, msg)
                
        except Exception as e:
            print(f"⚠️  Error procesando mensaje de {controller.controller_type.value}: {e}")
    
    def _process_controller_action(self, controller: MIDIController, message: List[int]):
        """Procesar acciones específicas del controlador"""
        if len(message) < 2:
            return
            
        status, data1 = message[0], message[1]
        
        # Program Change para cambio de presets
        if (status & 0xF0) == 0xC0:
            if data1 in controller.presets:
                controller.set_preset(data1, self.audio_engine)
        
        # Control Change para efectos
        elif (status & 0xF0) == 0xB0:
            self._handle_controller_effects(controller, data1, message[2] if len(message) > 2 else 0)
    
    def _handle_controller_effects(self, controller: MIDIController, cc_number: int, value: int):
        """Manejar efectos específicos del controlador"""
        # Mapeo de CC a efectos
        effect_map = {
            7: 'volume',
            91: 'reverb', 
            93: 'chorus',
            74: 'cutoff',
            71: 'resonance'
        }
        
        if cc_number in effect_map:
            effect_name = effect_map[cc_number]
            
            # Aplicar efecto a todos los canales del controlador
            for channel in controller.presets.keys():
                preset = controller.presets[channel]
                kwargs = {effect_name: value}
                self.audio_engine.set_channel_effects(preset.channel, **kwargs)
    
    def _forward_midi_message(self, controller: MIDIController, message: List[int]):
        """Enviar mensaje MIDI directo al AudioEngine"""
        if len(message) < 2:
            return
            
        status, data1 = message[0], message[1]
        channel = status & 0x0F
        velocity = message[2] if len(message) > 2 else 64
        
        # Note On
        if (status & 0xF0) == 0x90 and velocity > 0:
            self.audio_engine.note_on(channel, data1, velocity)
        # Note Off
        elif (status & 0xF0) == 0x80 or ((status & 0xF0) == 0x90 and velocity == 0):
            self.audio_engine.note_off(channel, data1)
    
    def _start_monitoring(self):
        """Iniciar monitoreo de hot-plug"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_devices, daemon=True)
        self.monitor_thread.start()
        print("   🔍 Monitoreo hot-plug iniciado")
    
    def _monitor_devices(self):
        """Monitorear cambios en dispositivos MIDI"""
        known_devices = set()
        
        while self.monitoring:
            try:
                midi_in = rtmidi.MidiIn()
                current_devices = set(midi_in.get_ports())
                
                # Detectar nuevos dispositivos
                new_devices = current_devices - known_devices
                for device in new_devices:
                    controller = self._match_device_to_controller(device)
                    if controller and device not in self.midi_inputs:
                        port_index = midi_in.get_ports().index(device)
                        self._connect_device(device, port_index, controller)
                        print(f"🔌 Dispositivo conectado: {device}")
                
                # Detectar dispositivos desconectados
                removed_devices = known_devices - current_devices
                for device in removed_devices:
                    if device in self.midi_inputs:
                        self._disconnect_device(device)
                        print(f"🔌 Dispositivo desconectado: {device}")
                
                known_devices = current_devices
                time.sleep(2)  # Verificar cada 2 segundos
                
            except Exception as e:
                print(f"⚠️  Error en monitoreo: {e}")
                time.sleep(5)
    
    def _disconnect_device(self, device_name: str):
        """Desconectar dispositivo MIDI"""
        try:
            if device_name in self.midi_inputs:
                midi_input = self.midi_inputs[device_name]
                midi_input.close_port()
                del self.midi_inputs[device_name]
                
            if device_name in self.device_mappings:
                controller_type = self.device_mappings[device_name]
                if controller_type in self.controllers:
                    self.controllers[controller_type].is_connected = False
                del self.device_mappings[device_name]
                
        except Exception as e:
            print(f"❌ Error desconectando {device_name}: {e}")
    
    def get_connected_devices(self) -> Dict[str, Dict[str, Any]]:
        """Obtener información de dispositivos conectados"""
        devices = {}
        for device_name, controller_type in self.device_mappings.items():
            controller = self.controllers[controller_type]
            devices[device_name] = {
                'type': controller_type,
                'connected': controller.is_connected,
                'current_preset': controller.current_preset,
                'presets': {pid: {'name': p.name, 'icon': p.icon} 
                           for pid, p in controller.presets.items()},
                'channels': [p.channel for p in controller.presets.values()]
            }
        return devices
    
    def set_device_preset(self, device_name: str, preset_id: int) -> bool:
        """Cambiar preset de un dispositivo específico"""
        if device_name not in self.device_mappings:
            return False
            
        controller_type = self.device_mappings[device_name]
        controller = self.controllers[controller_type]
        return controller.set_preset(preset_id, self.audio_engine)
    
    def stop(self):
        """Detener DeviceManager"""
        self.monitoring = False
        
        # Cerrar todas las conexiones MIDI
        for device_name in list(self.midi_inputs.keys()):
            self._disconnect_device(device_name)
            
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
            
        print("✅ DeviceManager detenido")

# ========================================================================================
# GESTOR DE PRESETS
# ========================================================================================

class PresetManager:
    """Gestor de presets configurables por dispositivo"""
    
    def __init__(self, db_path: str = "guitar_midi_modular.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """Inicializar base de datos de presets"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabla de controladores
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS controllers (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        device_patterns TEXT NOT NULL,
                        max_presets INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Tabla de presets por controlador
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS presets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        controller_id TEXT NOT NULL,
                        preset_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        program INTEGER NOT NULL,
                        bank INTEGER NOT NULL,
                        channel INTEGER NOT NULL,
                        category TEXT NOT NULL,
                        icon TEXT NOT NULL,
                        volume INTEGER DEFAULT 100,
                        reverb INTEGER DEFAULT 40,
                        chorus INTEGER DEFAULT 20,
                        cutoff INTEGER DEFAULT 64,
                        resonance INTEGER DEFAULT 64,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (controller_id) REFERENCES controllers (id),
                        UNIQUE (controller_id, preset_id)
                    )
                ''')
                
                # Tabla de configuración global
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS config (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                print("✅ Base de datos de presets inicializada")
                
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")
    
    def save_controller_presets(self, controller: MIDIController):
        """Guardar presets de un controlador en la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insertar/actualizar controlador
                cursor.execute('''
                    INSERT OR REPLACE INTO controllers 
                    (id, name, type, device_patterns, max_presets)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    controller.controller_type.value,
                    controller.controller_type.value.replace('_', ' ').title(),
                    controller.controller_type.value,
                    json.dumps(controller.device_patterns),
                    len(controller.presets)
                ))
                
                # Insertar/actualizar presets
                for preset_id, preset in controller.presets.items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO presets
                        (controller_id, preset_id, name, program, bank, channel,
                         category, icon, volume, reverb, chorus, cutoff, resonance)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        controller.controller_type.value,
                        preset.id,
                        preset.name,
                        preset.program,
                        preset.bank,
                        preset.channel,
                        preset.category.value,
                        preset.icon,
                        preset.volume,
                        preset.reverb,
                        preset.chorus,
                        preset.cutoff,
                        preset.resonance
                    ))
                
                conn.commit()
                print(f"💾 Presets guardados: {controller.controller_type.value}")
                
        except Exception as e:
            print(f"❌ Error guardando presets: {e}")
    
    def load_controller_presets(self, controller: MIDIController) -> bool:
        """Cargar presets de un controlador desde la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT preset_id, name, program, bank, channel, category, icon,
                           volume, reverb, chorus, cutoff, resonance
                    FROM presets
                    WHERE controller_id = ?
                    ORDER BY preset_id
                ''', (controller.controller_type.value,))
                
                rows = cursor.fetchall()
                if not rows:
                    return False
                
                # Cargar presets
                loaded_presets = {}
                for row in rows:
                    preset_id, name, program, bank, channel, category, icon, \
                    volume, reverb, chorus, cutoff, resonance = row
                    
                    loaded_presets[preset_id] = PresetConfig(
                        id=preset_id,
                        name=name,
                        program=program,
                        bank=bank,
                        channel=channel,
                        category=InstrumentCategory(category),
                        icon=icon,
                        volume=volume,
                        reverb=reverb,
                        chorus=chorus,
                        cutoff=cutoff,
                        resonance=resonance
                    )
                
                controller.presets = loaded_presets
                print(f"📂 Presets cargados: {controller.controller_type.value} ({len(loaded_presets)} presets)")
                return True
                
        except Exception as e:
            print(f"❌ Error cargando presets: {e}")
            return False
    
    def update_preset(self, controller_id: str, preset_id: int, 
                     updates: Dict[str, Any]) -> bool:
        """Actualizar preset específico"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Construir query de actualización dinámicamente
                set_clauses = []
                values = []
                
                for key, value in updates.items():
                    if key in ['name', 'program', 'bank', 'channel', 'category', 
                              'icon', 'volume', 'reverb', 'chorus', 'cutoff', 'resonance']:
                        set_clauses.append(f"{key} = ?")
                        values.append(value)
                
                if not set_clauses:
                    return False
                
                set_clauses.append("updated_at = CURRENT_TIMESTAMP")
                values.extend([controller_id, preset_id])
                
                query = f'''
                    UPDATE presets 
                    SET {', '.join(set_clauses)}
                    WHERE controller_id = ? AND preset_id = ?
                '''
                
                cursor.execute(query, values)
                conn.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"❌ Error actualizando preset: {e}")
            return False
    
    def get_available_instruments(self, category: InstrumentCategory = None) -> List[Dict[str, Any]]:
        """Obtener lista de instrumentos General MIDI disponibles"""
        # Instrumento General MIDI completo (128 instrumentos)
        gm_instruments = [
            # Piano (1-8)
            {"program": 0, "name": "Acoustic Grand Piano", "category": "piano", "icon": "🎹"},
            {"program": 1, "name": "Bright Acoustic Piano", "category": "piano", "icon": "🎹"},
            {"program": 2, "name": "Electric Grand Piano", "category": "piano", "icon": "🎹"},
            {"program": 3, "name": "Honky-tonk Piano", "category": "piano", "icon": "🎹"},
            {"program": 4, "name": "Electric Piano 1", "category": "piano", "icon": "🎹"},
            {"program": 5, "name": "Electric Piano 2", "category": "piano", "icon": "🎹"},
            {"program": 6, "name": "Harpsichord", "category": "piano", "icon": "🎹"},
            {"program": 7, "name": "Clavi", "category": "piano", "icon": "🎹"},
            
            # Chromatic Percussion (9-16)
            {"program": 8, "name": "Celesta", "category": "percussion", "icon": "🔔"},
            {"program": 9, "name": "Glockenspiel", "category": "percussion", "icon": "🔔"},
            {"program": 10, "name": "Music Box", "category": "percussion", "icon": "🎵"},
            {"program": 11, "name": "Vibraphone", "category": "percussion", "icon": "🎵"},
            {"program": 12, "name": "Marimba", "category": "percussion", "icon": "🥁"},
            {"program": 13, "name": "Xylophone", "category": "percussion", "icon": "🥁"},
            {"program": 14, "name": "Tubular Bells", "category": "percussion", "icon": "🔔"},
            {"program": 15, "name": "Dulcimer", "category": "percussion", "icon": "🎵"},
            
            # Guitar (25-32)
            {"program": 24, "name": "Acoustic Guitar (nylon)", "category": "guitar", "icon": "🎸"},
            {"program": 25, "name": "Acoustic Guitar (steel)", "category": "guitar", "icon": "🎸"},
            {"program": 26, "name": "Electric Guitar (jazz)", "category": "guitar", "icon": "🎸"},
            {"program": 27, "name": "Electric Guitar (clean)", "category": "guitar", "icon": "🎸"},
            {"program": 28, "name": "Electric Guitar (muted)", "category": "guitar", "icon": "🎸"},
            {"program": 29, "name": "Overdriven Guitar", "category": "guitar", "icon": "🎸"},
            {"program": 30, "name": "Distortion Guitar", "category": "guitar", "icon": "🎸"},
            {"program": 31, "name": "Guitar harmonics", "category": "guitar", "icon": "🎸"},
            
            # Bass (33-40)
            {"program": 32, "name": "Acoustic Bass", "category": "bass", "icon": "🎸"},
            {"program": 33, "name": "Electric Bass (finger)", "category": "bass", "icon": "🎸"},
            {"program": 34, "name": "Electric Bass (pick)", "category": "bass", "icon": "🎸"},
            {"program": 35, "name": "Fretless Bass", "category": "bass", "icon": "🎸"},
            {"program": 36, "name": "Slap Bass 1", "category": "bass", "icon": "🎸"},
            {"program": 37, "name": "Slap Bass 2", "category": "bass", "icon": "🎸"},
            {"program": 38, "name": "Synth Bass 1", "category": "bass", "icon": "🎸"},
            {"program": 39, "name": "Synth Bass 2", "category": "bass", "icon": "🎸"},
            
            # Strings (41-48)
            {"program": 40, "name": "Violin", "category": "strings", "icon": "🎻"},
            {"program": 41, "name": "Viola", "category": "strings", "icon": "🎻"},
            {"program": 42, "name": "Cello", "category": "strings", "icon": "🎻"},
            {"program": 43, "name": "Contrabass", "category": "strings", "icon": "🎻"},
            {"program": 44, "name": "Tremolo Strings", "category": "strings", "icon": "🎻"},
            {"program": 45, "name": "Pizzicato Strings", "category": "strings", "icon": "🎻"},
            {"program": 46, "name": "Orchestral Harp", "category": "strings", "icon": "🎻"},
            {"program": 47, "name": "Timpani", "category": "strings", "icon": "🥁"},
            
            # Ensemble (49-56)
            {"program": 48, "name": "String Ensemble 1", "category": "strings", "icon": "🎻"},
            {"program": 49, "name": "String Ensemble 2", "category": "strings", "icon": "🎻"},
            {"program": 50, "name": "SynthStrings 1", "category": "synth_pad", "icon": "🎹"},
            {"program": 51, "name": "SynthStrings 2", "category": "synth_pad", "icon": "🎹"},
            {"program": 52, "name": "Choir Aahs", "category": "strings", "icon": "👥"},
            {"program": 53, "name": "Voice Oohs", "category": "strings", "icon": "👥"},
            {"program": 54, "name": "Synth Voice", "category": "synth_lead", "icon": "🎤"},
            {"program": 55, "name": "Orchestra Hit", "category": "strings", "icon": "💥"},
            
            # Brass (57-64)
            {"program": 56, "name": "Trumpet", "category": "brass", "icon": "🎺"},
            {"program": 57, "name": "Trombone", "category": "brass", "icon": "🎺"},
            {"program": 58, "name": "Tuba", "category": "brass", "icon": "🎺"},
            {"program": 59, "name": "Muted Trumpet", "category": "brass", "icon": "🎺"},
            {"program": 60, "name": "French Horn", "category": "brass", "icon": "🎺"},
            {"program": 61, "name": "Brass Section", "category": "brass", "icon": "🎺"},
            {"program": 62, "name": "SynthBrass 1", "category": "synth_lead", "icon": "🎹"},
            {"program": 63, "name": "SynthBrass 2", "category": "synth_lead", "icon": "🎹"},
            
            # Reed (65-72)
            {"program": 64, "name": "Soprano Sax", "category": "reed", "icon": "🎷"},
            {"program": 65, "name": "Alto Sax", "category": "reed", "icon": "🎷"},
            {"program": 66, "name": "Tenor Sax", "category": "reed", "icon": "🎷"},
            {"program": 67, "name": "Baritone Sax", "category": "reed", "icon": "🎷"},
            {"program": 68, "name": "Oboe", "category": "reed", "icon": "🪈"},
            {"program": 69, "name": "English Horn", "category": "reed", "icon": "🪈"},
            {"program": 70, "name": "Bassoon", "category": "reed", "icon": "🪈"},
            {"program": 71, "name": "Clarinet", "category": "reed", "icon": "🪈"},
            
            # Pipe (73-80)
            {"program": 72, "name": "Piccolo", "category": "pipe", "icon": "🪈"},
            {"program": 73, "name": "Flute", "category": "pipe", "icon": "🪈"},
            {"program": 74, "name": "Recorder", "category": "pipe", "icon": "🪈"},
            {"program": 75, "name": "Pan Flute", "category": "pipe", "icon": "🪈"},
            {"program": 76, "name": "Blown Bottle", "category": "pipe", "icon": "🍾"},
            {"program": 77, "name": "Shakuhachi", "category": "ethnic", "icon": "🪈"},
            {"program": 78, "name": "Whistle", "category": "pipe", "icon": "🪈"},
            {"program": 79, "name": "Ocarina", "category": "pipe", "icon": "🪈"},
            
            # Synth Lead (81-88)
            {"program": 80, "name": "Lead 1 (square)", "category": "synth_lead", "icon": "🎹"},
            {"program": 81, "name": "Lead 2 (sawtooth)", "category": "synth_lead", "icon": "🎹"},
            {"program": 82, "name": "Lead 3 (calliope)", "category": "synth_lead", "icon": "🎹"},
            {"program": 83, "name": "Lead 4 (chiff)", "category": "synth_lead", "icon": "🎹"},
            {"program": 84, "name": "Lead 5 (charang)", "category": "synth_lead", "icon": "🎹"},
            {"program": 85, "name": "Lead 6 (voice)", "category": "synth_lead", "icon": "🎤"},
            {"program": 86, "name": "Lead 7 (fifths)", "category": "synth_lead", "icon": "🎹"},
            {"program": 87, "name": "Lead 8 (bass + lead)", "category": "synth_lead", "icon": "🎹"},
            
            # Synth Pad (89-96)
            {"program": 88, "name": "Pad 1 (new age)", "category": "synth_pad", "icon": "🌊"},
            {"program": 89, "name": "Pad 2 (warm)", "category": "synth_pad", "icon": "🌊"},
            {"program": 90, "name": "Pad 3 (polysynth)", "category": "synth_pad", "icon": "🌊"},
            {"program": 91, "name": "Pad 4 (choir)", "category": "synth_pad", "icon": "👥"},
            {"program": 92, "name": "Pad 5 (bowed)", "category": "synth_pad", "icon": "🌊"},
            {"program": 93, "name": "Pad 6 (metallic)", "category": "synth_pad", "icon": "⚡"},
            {"program": 94, "name": "Pad 7 (halo)", "category": "synth_pad", "icon": "✨"},
            {"program": 95, "name": "Pad 8 (sweep)", "category": "synth_pad", "icon": "🌊"},
        ]
        
        # Agregar kits de percusión (Bank 128)
        percussion_kits = [
            {"program": 0, "name": "Standard Kit", "category": "percussion", "icon": "🥁", "bank": 128},
            {"program": 8, "name": "Room Kit", "category": "percussion", "icon": "🏠", "bank": 128},
            {"program": 16, "name": "Power Kit", "category": "percussion", "icon": "⚡", "bank": 128},
            {"program": 24, "name": "Electronic Kit", "category": "percussion", "icon": "🔊", "bank": 128},
            {"program": 25, "name": "TR-808 Kit", "category": "percussion", "icon": "🤖", "bank": 128},
            {"program": 32, "name": "Jazz Kit", "category": "percussion", "icon": "🎷", "bank": 128},
            {"program": 40, "name": "Brush Kit", "category": "percussion", "icon": "🖌️", "bank": 128},
            {"program": 48, "name": "Orchestra Kit", "category": "percussion", "icon": "🎼", "bank": 128},
        ]
        
        # Combinar instrumentos melódicos y percusivos
        all_instruments = gm_instruments + percussion_kits
        
        # Filtrar por categoría si se especifica
        if category:
            category_name = category.value
            return [inst for inst in all_instruments if inst.get("category") == category_name]
        
        return all_instruments
    
    def export_controller_config(self, controller_id: str) -> Optional[Dict[str, Any]]:
        """Exportar configuración completa de un controlador"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Obtener info del controlador
                cursor.execute('''
                    SELECT name, type, device_patterns, max_presets
                    FROM controllers WHERE id = ?
                ''', (controller_id,))
                
                controller_info = cursor.fetchone()
                if not controller_info:
                    return None
                
                # Obtener presets
                cursor.execute('''
                    SELECT preset_id, name, program, bank, channel, category, icon,
                           volume, reverb, chorus, cutoff, resonance
                    FROM presets WHERE controller_id = ?
                    ORDER BY preset_id
                ''', (controller_id,))
                
                presets = []
                for row in cursor.fetchall():
                    presets.append({
                        'preset_id': row[0],
                        'name': row[1],
                        'program': row[2],
                        'bank': row[3],
                        'channel': row[4],
                        'category': row[5],
                        'icon': row[6],
                        'volume': row[7],
                        'reverb': row[8],
                        'chorus': row[9],
                        'cutoff': row[10],
                        'resonance': row[11]
                    })
                
                return {
                    'controller': {
                        'id': controller_id,
                        'name': controller_info[0],
                        'type': controller_info[1],
                        'device_patterns': json.loads(controller_info[2]),
                        'max_presets': controller_info[3]
                    },
                    'presets': presets,
                    'exported_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
        except Exception as e:
            print(f"❌ Error exportando configuración: {e}")
            return None

# ========================================================================================
# SISTEMA PRINCIPAL MODULAR
# ========================================================================================

class GuitarMIDIModular:
    """Sistema Guitar-MIDI Modular - Arquitectura multi-controlador"""
    
    def __init__(self):
        print("🎸 Guitar-MIDI Modular System v2.0 - Iniciando...")
        
        # Componentes principales
        self.audio_engine = AudioEngine()
        self.device_manager = None
        self.preset_manager = PresetManager()
        self.web_server = None
        self.socketio = None
        
        # Estado del sistema
        self.is_running = False
        
        # Configurar manejadores de señales
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        print("✅ Guitar-MIDI Modular inicializado")
    
    def initialize(self) -> bool:
        """Inicializar sistema completo"""
        try:
            print("🚀 Inicializando sistema modular...")
            
            # 1. Inicializar AudioEngine
            if not self.audio_engine.initialize():
                print("❌ Error crítico: AudioEngine no pudo inicializarse")
                return False
            
            # 2. Inicializar DeviceManager
            self.device_manager = DeviceManager(self.audio_engine)
            if not self.device_manager.initialize():
                print("❌ Error crítico: DeviceManager no pudo inicializarse")
                return False
            
            # 3. Cargar presets existentes para cada controlador
            self._load_saved_presets()
            
            # 4. Inicializar servidor web
            self._init_web_server()
            
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando sistema: {e}")
            return False
    
    def _load_saved_presets(self):
        """Cargar presets guardados para cada controlador"""
        for controller in self.device_manager.controllers.values():
            # Intentar cargar presets desde base de datos
            if not self.preset_manager.load_controller_presets(controller):
                # Si no hay presets guardados, usar los por defecto y guardarlos
                self.preset_manager.save_controller_presets(controller)
    
    def _init_web_server(self):
        """Inicializar servidor web modular"""
        print("🌐 Inicializando servidor web modular...")
        
        self.web_server = Flask(__name__)
        self.web_server.config['SECRET_KEY'] = 'guitar-midi-modular-2024'
        self.socketio = SocketIO(self.web_server, cors_allowed_origins="*")
        
        # Rutas principales
        @self.web_server.route('/')
        def index():
            return self._render_modular_interface()
        
        # API Routes para dispositivos
        @self.web_server.route('/api/devices', methods=['GET'])
        def get_devices():
            devices = self.device_manager.get_connected_devices()
            return jsonify({
                'success': True,
                'devices': devices,
                'count': len(devices)
            })
        
        @self.web_server.route('/api/devices/<device_name>/preset/<int:preset_id>', methods=['POST'])
        def set_device_preset(device_name, preset_id):
            success = self.device_manager.set_device_preset(device_name, preset_id)
            if success:
                # Notificar a clientes web
                self.socketio.emit('preset_changed', {
                    'device': device_name,
                    'preset_id': preset_id
                })
            return jsonify({'success': success})
        
        # API Routes para sistema
        @self.web_server.route('/api/system/panic', methods=['POST'])
        def panic():
            success = self.audio_engine.panic()
            if success:
                self.socketio.emit('panic_triggered', {
                    'timestamp': time.time()
                })
            return jsonify({'success': success})
        
        # WebSocket Events
        @self.socketio.on('connect')
        def handle_connect():
            print("📱 Cliente web conectado")
            emit('system_status', {
                'devices': self.device_manager.get_connected_devices(),
                'system': 'Guitar-MIDI Modular v2.0'
            })
        
        print("✅ Servidor web modular listo")
    
    def _render_modular_interface(self):
        """Renderizar interfaz web modular"""
        return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎸 Guitar-MIDI Modular v2.0</title>
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
        .subtitle { font-size: 1rem; opacity: 0.8; margin-bottom: 15px; }
        .status { 
            padding: 8px 20px; background: #4CAF50; border-radius: 25px; 
            display: inline-block; font-size: 0.9rem; font-weight: 500;
        }
        
        .main { padding: 20px; max-width: 1200px; margin: 0 auto; padding-bottom: 100px; }
        
        .devices-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px; margin-bottom: 30px;
        }
        
        .device-card {
            background: rgba(255,255,255,0.05); border-radius: 15px; 
            padding: 25px; border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        }
        
        .panic-btn {
            background: linear-gradient(135deg, #f44336, #d32f2f);
            color: white; border: none; border-radius: 15px;
            padding: 18px 30px; font-size: 1.2rem; font-weight: bold;
            cursor: pointer; width: 100%; margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(244, 67, 54, 0.4);
            transition: all 0.2s;
        }
        .panic-btn:active { transform: scale(0.95); }
        
        .loading {
            text-align: center; padding: 40px;
            font-size: 1.2rem; opacity: 0.7;
        }
    </style>
</head>
<body>
    <header class="header">
        <h1 class="title">🎸 Guitar-MIDI Modular System</h1>
        <p class="subtitle">Control Multi-Dispositivo • Presets Configurables • Efectos en Tiempo Real</p>
        <div class="status" id="status">🔄 Conectando...</div>
    </header>

    <main class="main">
        <button class="panic-btn" onclick="panic()">🚨 PANIC - Detener Todo</button>
        
        <div id="devices-container" class="loading">
            🔄 Detectando dispositivos MIDI...
        </div>
    </main>

    <script>
        function panic() {
            fetch('/api/system/panic', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('status').textContent = '🚨 PANIC activado';
                        document.getElementById('status').style.background = '#f44336';
                    }
                });
        }
        
        function loadDevices() {
            fetch('/api/devices')
                .then(response => response.json())
                .then(data => {
                    const container = document.getElementById('devices-container');
                    if (data.success && data.count > 0) {
                        container.innerHTML = `
                            <div class="devices-grid">
                                ${Object.entries(data.devices).map(([name, device]) => `
                                    <div class="device-card">
                                        <h3>🎛️ ${name}</h3>
                                        <p>Tipo: ${device.type}</p>
                                        <p>Estado: ${device.connected ? '✅ Conectado' : '❌ Desconectado'}</p>
                                        <p>Preset actual: ${device.current_preset}</p>
                                    </div>
                                `).join('')}
                            </div>
                        `;
                        document.getElementById('status').textContent = `✅ ${data.count} dispositivos`;
                        document.getElementById('status').style.background = '#4CAF50';
                    } else {
                        container.innerHTML = `
                            <div class="loading">
                                🎛️ No hay dispositivos MIDI conectados<br>
                                <small>Conecta tu MVAVE Pocket, controlador hexafónico o MIDI Captain</small>
                            </div>
                        `;
                    }
                })
                .catch(() => {
                    document.getElementById('status').textContent = '❌ Error cargando';
                    document.getElementById('status').style.background = '#f44336';
                });
        }
        
        // Cargar dispositivos al inicio y cada 10 segundos
        loadDevices();
        setInterval(loadDevices, 10000);
        
        console.log('🎸 Guitar-MIDI Modular System v2.0 Cargado');
    </script>
</body>
</html>'''
    
    def run(self):
        """Ejecutar sistema modular completo"""
        try:
            print("🚀 Iniciando Guitar-MIDI Modular System...")
            
            if not self.initialize():
                print("❌ Error crítico: Sistema no pudo inicializarse")
                return False
            
            # Mostrar información del sistema
            self._show_system_info()
            
            # Ejecutar servidor web (bloqueante)
            self.is_running = True
            print("🌐 Servidor web modular iniciando...")
            self.socketio.run(
                self.web_server, 
                host='0.0.0.0', 
                port=5000, 
                debug=False, 
                allow_unsafe_werkzeug=True
            )
            
        except KeyboardInterrupt:
            print("\n🛑 Deteniendo sistema modular...")
        except Exception as e:
            print(f"❌ Error crítico: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Detener sistema modular completo"""
        self.is_running = False
        
        if self.device_manager:
            self.device_manager.stop()
            
        if self.audio_engine:
            self.audio_engine.stop()
        
        print("✅ Guitar-MIDI Modular System detenido")
    
    def _signal_handler(self, signum, frame):
        """Manejador de señales del sistema"""
        print(f"\n🛑 Señal recibida: {signum}")
        self.stop()
        sys.exit(0)
    
    def _show_system_info(self):
        """Mostrar información del sistema modular"""
        print("\n" + "="*70)
        print("🎯 GUITAR-MIDI MODULAR SYSTEM v2.0 LISTO")
        print("="*70)
        
        # Obtener IP
        try:
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
            ip = result.stdout.strip().split()[0] if result.stdout.strip() else 'localhost'
        except:
            ip = 'localhost'
        
        print(f"🌐 IP del sistema: {ip}")
        print(f"📱 URL móvil: http://{ip}:5000")
        
        # Mostrar dispositivos conectados
        connected_devices = self.device_manager.get_connected_devices()
        print(f"🎛️ Dispositivos conectados: {len(connected_devices)}")
        
        for device_name, info in connected_devices.items():
            device_type = info['type'].replace('_', ' ').title()
            preset_count = len(info['presets'])
            current_preset = info['current_preset']
            print(f"   • {device_type}: {preset_count} presets (actual: {current_preset})")
        
        if not connected_devices:
            print("   ⚠️  No hay dispositivos MIDI conectados")
            print("   💡 Conecta: MVAVE Pocket, Controlador Hexafónico, MIDI Captain")
        
        print("\n📱 Para conectar desde celular:")
        print("1. Conectar a WiFi 'Guitar-MIDI' (contraseña: guitarmidi2024)")
        print("2. Abrir: http://192.168.4.1:5000")
        print("\n⌨️  Atajos: P=PANIC, 0-7=Presets")
        print("🔴 Ctrl+C para detener")
        print("="*70 + "\n")

def main():
    """Función principal"""
    print("🎸 Guitar-MIDI Modular System v2.0")
    print("Arquitectura Multi-Controlador")
    print("• MVAVE Pocket → 4 presets percusivos")
    print("• Hexafónico → 6 cuerdas → canales melódicos")  
    print("• MIDI Captain → control maestro")
    print("-" * 50)
    
    system = GuitarMIDIModular()
    system.run()

if __name__ == "__main__":
    main()