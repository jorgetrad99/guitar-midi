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

# Import web modules
from web.api.routes import init_api
from utils.fluidsynth_utils import FluidSynthInstrumentExtractor

# Verificar dependencias críticas al inicio
try:
    import rtmidi
    import fluidsynth
    from flask import Flask, render_template, jsonify, request
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
        
        # Sistema modular (NUEVO)
        self.modular_system = None
        self.device_manager = None
        self.active_controllers = {}
        
        # Base de datos SQLite integrada
        self.db_path = "guitar_midi.db"
        self._init_database()
        self._load_effects_from_db()
        
        # Librería completa de instrumentos General MIDI
        self.all_instruments = {
            # PIANOS (0-7)
            0: {"name": "Acoustic Grand Piano", "program": 0, "bank": 0, "channel": 0, "icon": "🎹", "category": "Piano"},
            1: {"name": "Bright Acoustic Piano", "program": 1, "bank": 0, "channel": 0, "icon": "🎹", "category": "Piano"},
            2: {"name": "Electric Grand Piano", "program": 2, "bank": 0, "channel": 0, "icon": "🎹", "category": "Piano"},
            3: {"name": "Honky-tonk Piano", "program": 3, "bank": 0, "channel": 0, "icon": "🎹", "category": "Piano"},
            4: {"name": "Electric Piano 1", "program": 4, "bank": 0, "channel": 0, "icon": "🎹", "category": "Piano"},
            5: {"name": "Electric Piano 2", "program": 5, "bank": 0, "channel": 0, "icon": "🎹", "category": "Piano"},
            6: {"name": "Harpsichord", "program": 6, "bank": 0, "channel": 0, "icon": "🎹", "category": "Piano"},
            7: {"name": "Clavi", "program": 7, "bank": 0, "channel": 0, "icon": "🎹", "category": "Piano"},
            # PERCUSION (8-15)
            8: {"name": "Celesta", "program": 8, "bank": 0, "channel": 0, "icon": "🔔", "category": "Chromatic Percussion"},
            9: {"name": "Glockenspiel", "program": 9, "bank": 0, "channel": 0, "icon": "🔔", "category": "Chromatic Percussion"},
            10: {"name": "Music Box", "program": 10, "bank": 0, "channel": 0, "icon": "🎵", "category": "Chromatic Percussion"},
            11: {"name": "Vibraphone", "program": 11, "bank": 0, "channel": 0, "icon": "🎤", "category": "Chromatic Percussion"},
            12: {"name": "Marimba", "program": 12, "bank": 0, "channel": 0, "icon": "🥁", "category": "Chromatic Percussion"},
            13: {"name": "Xylophone", "program": 13, "bank": 0, "channel": 0, "icon": "🎼", "category": "Chromatic Percussion"},
            14: {"name": "Tubular Bells", "program": 14, "bank": 0, "channel": 0, "icon": "🔔", "category": "Chromatic Percussion"},
            15: {"name": "Dulcimer", "program": 15, "bank": 0, "channel": 0, "icon": "🎻", "category": "Chromatic Percussion"},
            # ORGANOS (16-23)
            16: {"name": "Drawbar Organ", "program": 16, "bank": 0, "channel": 0, "icon": "🎹", "category": "Organ"},
            17: {"name": "Percussive Organ", "program": 17, "bank": 0, "channel": 0, "icon": "🎹", "category": "Organ"},
            18: {"name": "Rock Organ", "program": 18, "bank": 0, "channel": 0, "icon": "🎸", "category": "Organ"},
            19: {"name": "Church Organ", "program": 19, "bank": 0, "channel": 0, "icon": "⛪", "category": "Organ"},
            20: {"name": "Reed Organ", "program": 20, "bank": 0, "channel": 0, "icon": "🎹", "category": "Organ"},
            21: {"name": "Accordion", "program": 21, "bank": 0, "channel": 0, "icon": "🪗", "category": "Organ"},
            22: {"name": "Harmonica", "program": 22, "bank": 0, "channel": 0, "icon": "🎼", "category": "Organ"},
            23: {"name": "Tango Accordion", "program": 23, "bank": 0, "channel": 0, "icon": "🪗", "category": "Organ"},
            # GUITARRAS (24-31)
            24: {"name": "Acoustic Guitar (nylon)", "program": 24, "bank": 0, "channel": 0, "icon": "🎸", "category": "Guitar"},
            25: {"name": "Acoustic Guitar (steel)", "program": 25, "bank": 0, "channel": 0, "icon": "🎸", "category": "Guitar"},
            26: {"name": "Electric Guitar (jazz)", "program": 26, "bank": 0, "channel": 0, "icon": "🎸", "category": "Guitar"},
            27: {"name": "Electric Guitar (clean)", "program": 27, "bank": 0, "channel": 0, "icon": "🎸", "category": "Guitar"},
            28: {"name": "Electric Guitar (muted)", "program": 28, "bank": 0, "channel": 0, "icon": "🎸", "category": "Guitar"},
            29: {"name": "Overdriven Guitar", "program": 29, "bank": 0, "channel": 0, "icon": "🎸", "category": "Guitar"},
            30: {"name": "Distortion Guitar", "program": 30, "bank": 0, "channel": 0, "icon": "🎸", "category": "Guitar"},
            31: {"name": "Guitar harmonics", "program": 31, "bank": 0, "channel": 0, "icon": "🎸", "category": "Guitar"},
            # BAJOS (32-39)
            32: {"name": "Acoustic Bass", "program": 32, "bank": 0, "channel": 1, "icon": "🎸", "category": "Bass"},
            33: {"name": "Electric Bass (finger)", "program": 33, "bank": 0, "channel": 1, "icon": "🎸", "category": "Bass"},
            34: {"name": "Electric Bass (pick)", "program": 34, "bank": 0, "channel": 1, "icon": "🎸", "category": "Bass"},
            35: {"name": "Fretless Bass", "program": 35, "bank": 0, "channel": 1, "icon": "🎸", "category": "Bass"},
            36: {"name": "Slap Bass 1", "program": 36, "bank": 0, "channel": 1, "icon": "🎸", "category": "Bass"},
            37: {"name": "Slap Bass 2", "program": 37, "bank": 0, "channel": 1, "icon": "🎸", "category": "Bass"},
            38: {"name": "Synth Bass 1", "program": 38, "bank": 0, "channel": 1, "icon": "🎛️", "category": "Bass"},
            39: {"name": "Synth Bass 2", "program": 39, "bank": 0, "channel": 1, "icon": "🎛️", "category": "Bass"},
            # CUERDAS (40-47)
            40: {"name": "Violin", "program": 40, "bank": 0, "channel": 2, "icon": "🎻", "category": "Strings"},
            41: {"name": "Viola", "program": 41, "bank": 0, "channel": 2, "icon": "🎻", "category": "Strings"},
            42: {"name": "Cello", "program": 42, "bank": 0, "channel": 2, "icon": "🎻", "category": "Strings"},
            43: {"name": "Contrabass", "program": 43, "bank": 0, "channel": 2, "icon": "🎻", "category": "Strings"},
            44: {"name": "Tremolo Strings", "program": 44, "bank": 0, "channel": 2, "icon": "🎻", "category": "Strings"},
            45: {"name": "Pizzicato Strings", "program": 45, "bank": 0, "channel": 2, "icon": "🎻", "category": "Strings"},
            46: {"name": "Orchestral Harp", "program": 46, "bank": 0, "channel": 2, "icon": "🎼", "category": "Strings"},
            47: {"name": "Timpani", "program": 47, "bank": 0, "channel": 2, "icon": "🥁", "category": "Strings"},
            # ENSEMBLES (48-55)
            48: {"name": "String Ensemble 1", "program": 48, "bank": 0, "channel": 3, "icon": "🎻", "category": "Ensemble"},
            49: {"name": "String Ensemble 2", "program": 49, "bank": 0, "channel": 3, "icon": "🎻", "category": "Ensemble"},
            50: {"name": "SynthStrings 1", "program": 50, "bank": 0, "channel": 3, "icon": "🎛️", "category": "Ensemble"},
            51: {"name": "SynthStrings 2", "program": 51, "bank": 0, "channel": 3, "icon": "🎛️", "category": "Ensemble"},
            52: {"name": "Choir Aahs", "program": 52, "bank": 0, "channel": 3, "icon": "👥", "category": "Ensemble"},
            53: {"name": "Voice Oohs", "program": 53, "bank": 0, "channel": 3, "icon": "👥", "category": "Ensemble"},
            54: {"name": "Synth Voice", "program": 54, "bank": 0, "channel": 3, "icon": "🎛️", "category": "Ensemble"},
            55: {"name": "Orchestra Hit", "program": 55, "bank": 0, "channel": 3, "icon": "🎺", "category": "Ensemble"},
            # BRONCES (56-63)
            56: {"name": "Trumpet", "program": 56, "bank": 0, "channel": 4, "icon": "🎺", "category": "Brass"},
            57: {"name": "Trombone", "program": 57, "bank": 0, "channel": 4, "icon": "🎺", "category": "Brass"},
            58: {"name": "Tuba", "program": 58, "bank": 0, "channel": 4, "icon": "🎺", "category": "Brass"},
            59: {"name": "Muted Trumpet", "program": 59, "bank": 0, "channel": 4, "icon": "🎺", "category": "Brass"},
            60: {"name": "French Horn", "program": 60, "bank": 0, "channel": 4, "icon": "🎺", "category": "Brass"},
            61: {"name": "Brass Section", "program": 61, "bank": 0, "channel": 4, "icon": "🎺", "category": "Brass"},
            62: {"name": "SynthBrass 1", "program": 62, "bank": 0, "channel": 4, "icon": "🎛️", "category": "Brass"},
            63: {"name": "SynthBrass 2", "program": 63, "bank": 0, "channel": 4, "icon": "🎛️", "category": "Brass"},
            # LENGÜETAS (64-71)
            64: {"name": "Soprano Sax", "program": 64, "bank": 0, "channel": 5, "icon": "🎷", "category": "Reed"},
            65: {"name": "Alto Sax", "program": 65, "bank": 0, "channel": 5, "icon": "🎷", "category": "Reed"},
            66: {"name": "Tenor Sax", "program": 66, "bank": 0, "channel": 5, "icon": "🎷", "category": "Reed"},
            67: {"name": "Baritone Sax", "program": 67, "bank": 0, "channel": 5, "icon": "🎷", "category": "Reed"},
            68: {"name": "Oboe", "program": 68, "bank": 0, "channel": 5, "icon": "🪈", "category": "Reed"},
            69: {"name": "English Horn", "program": 69, "bank": 0, "channel": 5, "icon": "🪈", "category": "Reed"},
            70: {"name": "Bassoon", "program": 70, "bank": 0, "channel": 5, "icon": "🪈", "category": "Reed"},
            71: {"name": "Clarinet", "program": 71, "bank": 0, "channel": 5, "icon": "🪈", "category": "Reed"},
            # VIENTOS (72-79)
            72: {"name": "Piccolo", "program": 72, "bank": 0, "channel": 6, "icon": "🪈", "category": "Pipe"},
            73: {"name": "Flute", "program": 73, "bank": 0, "channel": 6, "icon": "🪈", "category": "Pipe"},
            74: {"name": "Recorder", "program": 74, "bank": 0, "channel": 6, "icon": "🪈", "category": "Pipe"},
            75: {"name": "Pan Flute", "program": 75, "bank": 0, "channel": 6, "icon": "🪈", "category": "Pipe"},
            76: {"name": "Blown Bottle", "program": 76, "bank": 0, "channel": 6, "icon": "🍾", "category": "Pipe"},
            77: {"name": "Shakuhachi", "program": 77, "bank": 0, "channel": 6, "icon": "🪈", "category": "Pipe"},
            78: {"name": "Whistle", "program": 78, "bank": 0, "channel": 6, "icon": "🪈", "category": "Pipe"},
            79: {"name": "Ocarina", "program": 79, "bank": 0, "channel": 6, "icon": "🪈", "category": "Pipe"},
            # SYNTH LEAD (80-87)
            80: {"name": "Lead 1 (square)", "program": 80, "bank": 0, "channel": 7, "icon": "🎛️", "category": "Synth Lead"},
            81: {"name": "Lead 2 (sawtooth)", "program": 81, "bank": 0, "channel": 7, "icon": "🎛️", "category": "Synth Lead"},
            82: {"name": "Lead 3 (calliope)", "program": 82, "bank": 0, "channel": 7, "icon": "🎛️", "category": "Synth Lead"},
            83: {"name": "Lead 4 (chiff)", "program": 83, "bank": 0, "channel": 7, "icon": "🎛️", "category": "Synth Lead"},
            84: {"name": "Lead 5 (charang)", "program": 84, "bank": 0, "channel": 7, "icon": "🎛️", "category": "Synth Lead"},
            85: {"name": "Lead 6 (voice)", "program": 85, "bank": 0, "channel": 7, "icon": "🎛️", "category": "Synth Lead"},
            86: {"name": "Lead 7 (fifths)", "program": 86, "bank": 0, "channel": 7, "icon": "🎛️", "category": "Synth Lead"},
            87: {"name": "Lead 8 (bass + lead)", "program": 87, "bank": 0, "channel": 7, "icon": "🎛️", "category": "Synth Lead"},
            # SYNTH PAD (88-95)
            88: {"name": "Pad 1 (new age)", "program": 88, "bank": 0, "channel": 8, "icon": "🎛️", "category": "Synth Pad"},
            89: {"name": "Pad 2 (warm)", "program": 89, "bank": 0, "channel": 8, "icon": "🎛️", "category": "Synth Pad"},
            90: {"name": "Pad 3 (polysynth)", "program": 90, "bank": 0, "channel": 8, "icon": "🎛️", "category": "Synth Pad"},
            91: {"name": "Pad 4 (choir)", "program": 91, "bank": 0, "channel": 8, "icon": "🎛️", "category": "Synth Pad"},
            92: {"name": "Pad 5 (bowed)", "program": 92, "bank": 0, "channel": 8, "icon": "🎛️", "category": "Synth Pad"},
            93: {"name": "Pad 6 (metallic)", "program": 93, "bank": 0, "channel": 8, "icon": "🎛️", "category": "Synth Pad"},
            94: {"name": "Pad 7 (halo)", "program": 94, "bank": 0, "channel": 8, "icon": "🎛️", "category": "Synth Pad"},
            95: {"name": "Pad 8 (sweep)", "program": 95, "bank": 0, "channel": 8, "icon": "🎛️", "category": "Synth Pad"},
            # EFECTOS FX (96-103)
            96: {"name": "FX 1 (rain)", "program": 96, "bank": 0, "channel": 9, "icon": "🌧️", "category": "Synth Effects"},
            97: {"name": "FX 2 (soundtrack)", "program": 97, "bank": 0, "channel": 9, "icon": "🎬", "category": "Synth Effects"},
            98: {"name": "FX 3 (crystal)", "program": 98, "bank": 0, "channel": 9, "icon": "💎", "category": "Synth Effects"},
            99: {"name": "FX 4 (atmosphere)", "program": 99, "bank": 0, "channel": 9, "icon": "🌌", "category": "Synth Effects"},
            100: {"name": "FX 5 (brightness)", "program": 100, "bank": 0, "channel": 9, "icon": "✨", "category": "Synth Effects"},
            101: {"name": "FX 6 (goblins)", "program": 101, "bank": 0, "channel": 9, "icon": "👹", "category": "Synth Effects"},
            102: {"name": "FX 7 (echoes)", "program": 102, "bank": 0, "channel": 9, "icon": "🔊", "category": "Synth Effects"},
            103: {"name": "FX 8 (sci-fi)", "program": 103, "bank": 0, "channel": 9, "icon": "🚀", "category": "Synth Effects"},
            # ETNICOS (104-111)
            104: {"name": "Sitar", "program": 104, "bank": 0, "channel": 10, "icon": "🪕", "category": "Ethnic"},
            105: {"name": "Banjo", "program": 105, "bank": 0, "channel": 10, "icon": "🪕", "category": "Ethnic"},
            106: {"name": "Shamisen", "program": 106, "bank": 0, "channel": 10, "icon": "🎸", "category": "Ethnic"},
            107: {"name": "Koto", "program": 107, "bank": 0, "channel": 10, "icon": "🎼", "category": "Ethnic"},
            108: {"name": "Kalimba", "program": 108, "bank": 0, "channel": 10, "icon": "🎵", "category": "Ethnic"},
            109: {"name": "Bag pipe", "program": 109, "bank": 0, "channel": 10, "icon": "🪈", "category": "Ethnic"},
            110: {"name": "Fiddle", "program": 110, "bank": 0, "channel": 10, "icon": "🎻", "category": "Ethnic"},
            111: {"name": "Shanai", "program": 111, "bank": 0, "channel": 10, "icon": "🪈", "category": "Ethnic"},
            # PERCUSION (112-119)
            112: {"name": "Tinkle Bell", "program": 112, "bank": 0, "channel": 11, "icon": "🔔", "category": "Percussive"},
            113: {"name": "Agogo", "program": 113, "bank": 0, "channel": 11, "icon": "🥁", "category": "Percussive"},
            114: {"name": "Steel Drums", "program": 114, "bank": 0, "channel": 11, "icon": "🛢️", "category": "Percussive"},
            115: {"name": "Woodblock", "program": 115, "bank": 0, "channel": 11, "icon": "🪵", "category": "Percussive"},
            116: {"name": "Taiko Drum", "program": 116, "bank": 0, "channel": 11, "icon": "🥁", "category": "Percussive"},
            117: {"name": "Melodic Tom", "program": 117, "bank": 0, "channel": 11, "icon": "🥁", "category": "Percussive"},
            118: {"name": "Synth Drum", "program": 118, "bank": 0, "channel": 11, "icon": "🎛️", "category": "Percussive"},
            119: {"name": "Reverse Cymbal", "program": 119, "bank": 0, "channel": 11, "icon": "🥁", "category": "Percussive"},
            # EFECTOS SONOROS (120-127)
            120: {"name": "Guitar Fret Noise", "program": 120, "bank": 0, "channel": 12, "icon": "🎸", "category": "Sound Effects"},
            121: {"name": "Breath Noise", "program": 121, "bank": 0, "channel": 12, "icon": "💨", "category": "Sound Effects"},
            122: {"name": "Seashore", "program": 122, "bank": 0, "channel": 12, "icon": "🌊", "category": "Sound Effects"},
            123: {"name": "Bird Tweet", "program": 123, "bank": 0, "channel": 12, "icon": "🐦", "category": "Sound Effects"},
            124: {"name": "Telephone Ring", "program": 124, "bank": 0, "channel": 12, "icon": "📞", "category": "Sound Effects"},
            125: {"name": "Helicopter", "program": 125, "bank": 0, "channel": 12, "icon": "🚁", "category": "Sound Effects"},
            126: {"name": "Applause", "program": 126, "bank": 0, "channel": 12, "icon": "👏", "category": "Sound Effects"},
            127: {"name": "Gunshot", "program": 127, "bank": 0, "channel": 12, "icon": "💥", "category": "Sound Effects"},
            # BATERIA (canal 9 solo)
            128: {"name": "Standard Drum Kit", "program": 0, "bank": 128, "channel": 9, "icon": "🥁", "category": "Drums"}
        }
        
        # Presets configurables (8 slots)
        self.presets = {
            0: {"name": "Acoustic Grand Piano", "program": 0, "bank": 0, "channel": 0, "icon": "🎹"},
            1: {"name": "Standard Drum Kit", "program": 0, "bank": 128, "channel": 9, "icon": "🥁"},
            2: {"name": "Acoustic Bass", "program": 32, "bank": 0, "channel": 1, "icon": "🎸"},
            3: {"name": "Acoustic Guitar (nylon)", "program": 24, "bank": 0, "channel": 2, "icon": "🎸"},
            4: {"name": "Alto Sax", "program": 65, "bank": 0, "channel": 3, "icon": "🎷"},
            5: {"name": "String Ensemble 1", "program": 48, "bank": 0, "channel": 4, "icon": "🎻"},
            6: {"name": "Drawbar Organ", "program": 16, "bank": 0, "channel": 5, "icon": "🎹"},
            7: {"name": "Flute", "program": 73, "bank": 0, "channel": 6, "icon": "🪈"}
        }
        
        # Efectos globales expandidos
        self.effects = {
            'master_volume': 80,
            'global_reverb': 50,
            'global_chorus': 30,
            'global_cutoff': 64,
            'global_resonance': 0
        }
        
        # Monitoreo de dispositivos MIDI en tiempo real
        self.device_monitor_thread = None
        self.monitoring_active = False
        
        # Componentes del sistema
        self.fs = None  # FluidSynth
        self.sfid = None  # SoundFont ID
        self.app = None  # Flask App
        self.socketio = None  # SocketIO
        self.audio_device = None  # Dispositivo de audio detectado
        self.instrument_extractor = None  # FluidSynth instrument extractor
        self._instrument_library_cache = None  # Cache for instrument library
        
        # Sistema de controladores MIDI específicos
        self.connected_controllers = {}  # device_name -> controller_info
        self.controller_patterns = {
            'mvave_pocket': ['MVAVE.*Pocket', 'Pocket.*MVAVE', 'MVAVE.*'],
            'hexaphonic': ['HEX.*', 'Hexaphonic.*', 'Guitar.*Synth', '.*Hexaphonic.*'],
            'midi_captain': ['.*Captain.*', 'Captain.*', 'Pico.*Captain.*', 'MIDI.*Captain.*']
        }
        
        # Presets específicos por controlador
        self.controller_presets = {
            'mvave_pocket': {
                0: {"name": "Standard Kit", "program": 0, "bank": 128, "channel": 9, "icon": "🥁"},
                1: {"name": "Rock Kit", "program": 16, "bank": 128, "channel": 9, "icon": "🤘"},
                2: {"name": "Electronic Kit", "program": 25, "bank": 128, "channel": 9, "icon": "🔊"},
                3: {"name": "Jazz Kit", "program": 32, "bank": 128, "channel": 9, "icon": "🎷"}
            },
            'hexaphonic': {
                0: {"name": "Synth Bass", "program": 38, "bank": 0, "channel": 0, "icon": "🎸"},
                1: {"name": "String Ensemble", "program": 48, "bank": 0, "channel": 1, "icon": "🎻"},
                2: {"name": "Lead Synth", "program": 80, "bank": 0, "channel": 2, "icon": "🎹"},
                3: {"name": "Trumpet Section", "program": 56, "bank": 0, "channel": 3, "icon": "🎺"},
                4: {"name": "Tenor Sax", "program": 66, "bank": 0, "channel": 4, "icon": "🎷"},
                5: {"name": "Flute", "program": 73, "bank": 0, "channel": 5, "icon": "🪈"}
            },
            'midi_captain': {
                0: {"name": "Rock Setup", "program": 0, "bank": 0, "channel": 15, "icon": "🤘"},
                1: {"name": "Jazz Setup", "program": 0, "bank": 0, "channel": 15, "icon": "🎷"},
                2: {"name": "Electronic Setup", "program": 0, "bank": 0, "channel": 15, "icon": "🔊"},
                3: {"name": "Classical Setup", "program": 0, "bank": 0, "channel": 15, "icon": "🎻"},
                4: {"name": "Funk Setup", "program": 0, "bank": 0, "channel": 15, "icon": "🎸"},
                5: {"name": "Ambient Setup", "program": 0, "bank": 0, "channel": 15, "icon": "🌊"},
                6: {"name": "Latin Setup", "program": 0, "bank": 0, "channel": 15, "icon": "🪘"},
                7: {"name": "Experimental Setup", "program": 0, "bank": 0, "channel": 15, "icon": "🚀"}
            }
        }
        
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
    
    def _load_effects_from_db(self):
        """Cargar efectos guardados de la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT key, value FROM config WHERE key LIKE "%_volume" OR key LIKE "global_%"')
                rows = cursor.fetchall()
                
                for key, value in rows:
                    try:
                        self.effects[key] = int(value)
                        print(f"   📂 Cargado {key}: {value}%")
                    except ValueError:
                        print(f"   ⚠️  Valor inválido para {key}: {value}")
                        
                print(f"   ✅ {len(rows)} efectos cargados de la BD")
        except Exception as e:
            print(f"   ⚠️  Error cargando efectos: {e}")
    
    def _auto_detect_audio(self) -> bool:
        """Auto-detectar dispositivo de audio que funciona"""
        print("🔊 Auto-detectando audio...")
        
        # Detectar dispositivos disponibles primero
        available_devices = self._get_available_audio_devices()
        
        # Configuraciones a probar (orden de preferencia)
        audio_configs = [
            ("default", "Sistema por defecto", None),
            ("hw:0,0", "Jack 3.5mm", 1),
            ("hw:0,1", "HDMI", 2),
            ("hw:1,0", "USB Audio", None),
            ("hw:2,0", "USB Audio secundario", None)
        ]
        
        # Filtrar solo dispositivos disponibles
        configs_to_test = []
        for device, description, raspi_config in audio_configs:
            if device == "default" or any(device in avail for avail in available_devices):
                configs_to_test.append((device, description, raspi_config))
        
        if not configs_to_test:
            print("   ⚠️  No se encontraron dispositivos de audio")
            self.audio_device = "default"
            return False
        
        for device, description, raspi_config in configs_to_test:
            print(f"   Probando: {description} ({device})")
            
            # Configurar raspi-config si es necesario (solo en Raspberry Pi)
            if raspi_config and os.path.exists('/boot/config.txt'):
                try:
                    subprocess.run(['sudo', 'raspi-config', 'nonint', 'do_audio', str(raspi_config)], 
                                 check=True, capture_output=True, timeout=5)
                    time.sleep(0.5)
                except:
                    pass
            
            # Test rápido del dispositivo
            if self._test_audio_device(device):
                print(f"   ✅ Audio detectado: {description}")
                self.audio_device = device
                self._configure_alsa()
                return True
            else:
                print(f"   ❌ No funciona: {description}")
        
        print("   ⚠️  Usando dispositivo por defecto")
        self.audio_device = "default"
        return False
    
    def _get_available_audio_devices(self) -> List[str]:
        """Obtener lista de dispositivos de audio disponibles"""
        devices = []
        try:
            # Usar aplay para listar dispositivos
            result = subprocess.run(['aplay', '-l'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'card' in line and 'device' in line:
                        # Extraer hw:X,Y del formato "card X: ... device Y:"
                        parts = line.split()
                        card = None
                        device = None
                        for i, part in enumerate(parts):
                            if part.startswith('card') and i+1 < len(parts):
                                card = parts[i+1].rstrip(':')
                            elif part.startswith('device') and i+1 < len(parts):
                                device = parts[i+1].rstrip(':')
                        
                        if card is not None and device is not None:
                            devices.append(f"hw:{card},{device}")
        except:
            pass
        
        return devices
    
    def _test_audio_device(self, device: str) -> bool:
        """Test rápido de un dispositivo de audio"""
        try:
            # Test muy breve para no molestar
            cmd = ['aplay', '-D', device, '/dev/zero']
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
            time.sleep(0.1)  # Test muy corto
            proc.terminate()
            proc.wait(timeout=1)
            return True
        except:
            return False
    
    def _configure_alsa(self):
        """Configurar ALSA con volúmenes óptimos"""
        try:
            # Configurar volúmenes de manera más segura
            commands = [
                ['amixer', '-q', 'set', 'PCM', '90%'],
                ['amixer', '-q', 'set', 'Master', '90%'],
                ['amixer', '-q', 'sset', 'Headphone', '90%'],
                ['amixer', '-q', 'sset', 'Speaker', '90%']
            ]
            
            for cmd in commands:
                try:
                    subprocess.run(cmd, capture_output=True, timeout=2)
                except:
                    pass  # Ignorar errores individuales
            
            # Crear archivo de configuración ALSA si no existe
            alsa_conf = """
pcm.!default {
    type hw
    card 0
    device 0
}
ctl.!default {
    type hw
    card 0
}
"""
            
            try:
                asoundrc_path = os.path.expanduser("~/.asoundrc")
                if not os.path.exists(asoundrc_path):
                    with open(asoundrc_path, 'w') as f:
                        f.write(alsa_conf)
                    print("   ✅ Configuración ALSA creada")
            except:
                pass
            
            print("   ✅ ALSA configurado")
        except Exception as e:
            print(f"   ⚠️  Error configurando ALSA: {e}")
    
    def _init_fluidsynth(self) -> bool:
        """Inicializar FluidSynth con configuración optimizada para baja latencia"""
        try:
            print("🎹 Inicializando FluidSynth (MODO BAJA LATENCIA)...")
            self.fs = fluidsynth.Synth()
            
            # Detectar versión de FluidSynth para compatibilidad
            self._detect_fluidsynth_version()
            
            # 🚀 CONFIGURACIONES CRÍTICAS PARA BAJA LATENCIA (SOLO PARÁMETROS VÁLIDOS)
            print("   🚀 Aplicando configuraciones de baja latencia (compatibles)...")
            
            # ✅ PARÁMETROS VÁLIDOS Y COMPATIBLES
            # Buffer pequeño para latencia baja
            self._safe_setting('audio.periods', 2)           # Mínimos períodos (VÁLIDO)
            self._safe_setting('audio.period-size', 64)      # Buffer pequeño (VÁLIDO)
            
            # Reducir voces para menos CPU
            self._safe_setting('synth.polyphony', 32)        # Menos voces simultáneas (VÁLIDO)
            self._safe_setting('synth.gain', 1.2)            # Ganancia para compensar (VÁLIDO)
            
            # Configuraciones de reverb/chorus para menos CPU
            self._safe_setting('synth.reverb.active', 1)     # Reverb básico (VÁLIDO)
            self._safe_setting('synth.chorus.active', 1)     # Chorus básico (VÁLIDO)
            
            # Configuraciones de audio específicas
            self._safe_setting('audio.file.type', 'auto')    # Tipo de archivo auto (VÁLIDO)
            
            print("   ✅ Solo parámetros compatibles aplicados")
            
            # 🎯 ESTRATEGIA ALTERNATIVA PARA BAJA LATENCIA (sin parámetros incompatibles)
            self._apply_alternative_low_latency_settings()
            
            # Configuración de audio más compatible
            drivers_to_try = ['alsa', 'pulse', 'oss', 'jack']
            audio_started = False
            
            for driver in drivers_to_try:
                try:
                    print(f"   Probando driver de audio: {driver}")
                    self.fs.setting('audio.driver', driver)
                    
                    if driver == 'alsa':
                        # 🎯 CONFIGURACIÓN ALSA OPTIMIZADA PARA LATENCIA
                        device = self.audio_device or 'hw:0,0'
                        print(f"      Dispositivo ALSA: {device} (BAJA LATENCIA)")
                        
                        self._safe_setting('audio.alsa.device', device)
                        # ✅ Solo configuraciones ALSA compatibles
                        # Los parámetros periods y period-size específicos de ALSA no son compatibles
                        
                    elif driver == 'pulse':
                        # PulseAudio con configuración básica
                        self._safe_setting('audio.pulseaudio.server', 'default')
                        self._safe_setting('audio.pulseaudio.device', 'default')
                    
                    # Ganancia optimizada
                    self._safe_setting('synth.gain', 1.2)              # Ganancia ligeramente alta
                    
                    # Intentar iniciar
                    result = self.fs.start(driver=driver)
                    if result == 0:  # Success
                        print(f"   ✅ Audio iniciado con driver: {driver} (BAJA LATENCIA)")
                        audio_started = True
                        break
                    else:
                        print(f"   ❌ Driver {driver} falló")
                        
                except Exception as e:
                    print(f"   ❌ Error con driver {driver}: {e}")
                    continue
            
            if not audio_started:
                print("   ⚠️  Intentando configuración ultra-básica...")
                try:
                    # Reinicializar con configuración por defecto
                    self.fs = fluidsynth.Synth()
                    
                    # NO configurar nada, usar valores por defecto de FluidSynth
                    print("      Usando configuración por defecto de FluidSynth")
                    
                    # Intentar iniciar sin especificar driver (usa el por defecto)
                    result = self.fs.start()
                    if result == 0:
                        print("   ✅ FluidSynth iniciado con configuración por defecto")
                        audio_started = True
                    else:
                        # Último intento: especificar solo el driver ALSA
                        print("   ⚠️  Intentando solo con driver ALSA...")
                        self.fs = fluidsynth.Synth()
                        self.fs.setting('audio.driver', 'alsa')
                        result = self.fs.start(driver='alsa')
                        if result == 0:
                            print("   ✅ FluidSynth iniciado solo con ALSA")
                            audio_started = True
                        else:
                            raise Exception("No se pudo iniciar FluidSynth")
                            
                except Exception as e:
                    print(f"   ❌ Error en configuración ultra-básica: {e}")
                    return False
            
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
            
            # Ajustar volumen del sistema después de iniciar FluidSynth
            self._boost_system_audio()
            
            # Test de audio para verificar que funciona
            self._test_audio_output()
            
            # Validar mapeo de presets
            self._validate_preset_mapping()
            
            # Aplicar efectos iniciales
            self._apply_current_effects()
            
            # 🚀 Aplicar optimizaciones post-inicio para baja latencia
            self._apply_post_init_optimizations()
            
            # Inicializar extractor de instrumentos
            self.instrument_extractor = FluidSynthInstrumentExtractor()
            if self.instrument_extractor.initialize(sf_path):
                print("   ✅ Extractor de instrumentos inicializado")
            else:
                print("   ⚠️  Extractor de instrumentos falló, usando fallback")
            
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando FluidSynth: {e}")
            return False
    
    def _safe_setting(self, param: str, value) -> bool:
        """Configurar parámetro FluidSynth de manera segura (silencia errores de parámetros no válidos)"""
        try:
            result = self.fs.setting(param, value)
            if result == 0:  # 0 = éxito en FluidSynth
                print(f"      ✅ {param} = {value}")
                return True
            else:
                # No mostrar warning para parámetros conocidos como incompatibles
                if param not in ['synth.parallel-render', 'synth.sample-rate', 'synth.overflow.percussion', 
                               'synth.overflow.released', 'synth.overflow.sustained', 'audio.alsa.periods', 
                               'audio.alsa.period-size', 'audio.pulseaudio.media.role']:
                    print(f"      ⚠️  {param} no soportado en esta versión")
                return False
        except Exception as e:
            # No mostrar errores para parámetros conocidos como incompatibles
            if param not in ['synth.parallel-render', 'synth.sample-rate', 'synth.overflow.percussion', 
                           'synth.overflow.released', 'synth.overflow.sustained', 'audio.alsa.periods', 
                           'audio.alsa.period-size', 'audio.pulseaudio.media.role']:
                print(f"      ❌ Error configurando {param}: {e}")
            return False
    
    def _apply_alternative_low_latency_settings(self):
        """Aplicar configuraciones alternativas de baja latencia que funcionan en todas las versiones"""
        try:
            print("   🚀 Aplicando estrategia alternativa de baja latencia...")
            
            # Estrategia 1: Reducir latencia mediante configuración de drivers
            # Configurar argumentos de inicio de FluidSynth directamente
            # Estos se aplican cuando se inicia el driver de audio
            
            # Estrategia 2: Configuraciones posteriores al inicio
            # Estas se aplicarán después de que FluidSynth esté funcionando
            self.post_init_optimizations = {
                'low_latency_mode': True,
                'reduced_buffer_size': 64,
                'minimal_periods': 2,
                'optimized_polyphony': 32
            }
            
            print("   ✅ Estrategia alternativa configurada - se aplicará después del inicio")
            
        except Exception as e:
            print(f"   ⚠️  Error en estrategia alternativa: {e}")
    
    def _apply_post_init_optimizations(self):
        """Aplicar optimizaciones después de que FluidSynth esté iniciado"""
        try:
            if not hasattr(self, 'post_init_optimizations') or not self.fs:
                return
                
            print("   🚀 Aplicando optimizaciones post-inicio...")
            
            # Configurar prioridad alta del hilo de audio (a nivel de SO)
            try:
                import os
                # Intentar aumentar prioridad si es posible
                os.nice(-5)  # Prioridad ligeramente alta
                print("      ✅ Prioridad de proceso aumentada")
            except:
                pass
            
            # Optimizar FluidSynth mediante CC messages
            # Esto funciona independientemente de la configuración inicial
            try:
                # Configurar todos los canales para respuesta rápida
                for channel in range(16):
                    # CC 6: Data Entry MSB (para respuesta rápida)
                    self.fs.cc(channel, 6, 127)
                    # CC 100: RPN LSB = 0 (fine tuning)
                    self.fs.cc(channel, 100, 0)
                    # CC 101: RPN MSB = 0 (fine tuning)
                    self.fs.cc(channel, 101, 0)
                
                print("      ✅ Canales optimizados para respuesta rápida")
            except:
                pass
                
            print("   ✅ Optimizaciones post-inicio aplicadas")
            
        except Exception as e:
            print(f"   ⚠️  Error en optimizaciones post-inicio: {e}")
    
    def _detect_fluidsynth_version(self):
        """Detectar versión de FluidSynth para optimizar compatibilidad"""
        try:
            # Intentar obtener versión si está disponible
            try:
                import subprocess
                result = subprocess.run(['fluidsynth', '--version'], capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    version_info = result.stdout.strip()
                    print(f"   ℹ️  FluidSynth detectado: {version_info}")
                    
                    # Extraer número de versión para futura compatibilidad
                    if 'FluidSynth' in version_info:
                        version_parts = version_info.split()
                        for part in version_parts:
                            if '.' in part and any(c.isdigit() for c in part):
                                self.fluidsynth_version = part
                                print(f"      Versión: {self.fluidsynth_version}")
                                break
                else:
                    print("   ⚠️  No se pudo detectar versión de FluidSynth")
            except:
                print("   ⚠️  Detección de versión FluidSynth falló")
                
        except Exception as e:
            print(f"   ⚠️  Error detectando versión FluidSynth: {e}")
    
    def _boost_system_audio(self):
        """Aumentar volumen del sistema para asegurar que se escuche"""
        try:
            print("   🔊 Ajustando volumen del sistema...")
            
            # Comandos para aumentar volumen
            volume_commands = [
                ['amixer', '-q', 'sset', 'Master', '100%', 'unmute'],
                ['amixer', '-q', 'sset', 'PCM', '100%', 'unmute'],
                ['amixer', '-q', 'sset', 'Headphone', '95%', 'unmute'],
                ['amixer', '-q', 'sset', 'Speaker', '95%', 'unmute'],
                ['amixer', '-q', 'sset', 'Capture', '90%'],
            ]
            
            for cmd in volume_commands:
                try:
                    subprocess.run(cmd, capture_output=True, timeout=2)
                except:
                    pass  # Ignorar errores individuales
            
            # También aumentar ganancia de FluidSynth si es posible
            if self.fs:
                try:
                    # Usar método más directo para ganancia
                    if hasattr(self.fs, 'set_gain'):
                        self.fs.set_gain(1.2)
                        print("      ✅ Ganancia FluidSynth aumentada")
                except:
                    pass
            
            print("   ✅ Volumen del sistema ajustado")
            
        except Exception as e:
            print(f"   ⚠️  Error ajustando volumen: {e}")
    
    def _test_audio_output(self):
        """Test rápido de salida de audio"""
        try:
            if self.fs and self.sfid is not None:
                print("   🧪 Probando salida de audio...")
                
                # Configurar canal 0 con piano
                self.fs.program_select(0, self.sfid, 0, 0)  # Canal 0, Bank 0, Program 0 (Piano)
                
                # Tocar una nota corta (C4)
                self.fs.noteon(0, 60, 80)   # Canal 0, Nota C4, Velocidad 80
                time.sleep(0.2)              # Sonar por 200ms
                self.fs.noteoff(0, 60)       # Apagar nota
                
                print("   ✅ Test de audio completado")
                print("   🔊 Si no escuchaste nada, revisar conexión de audio")
            else:
                print("   ⚠️  No se pudo hacer test de audio (FluidSynth no iniciado)")
                
        except Exception as e:
            print(f"   ⚠️  Error en test de audio: {e}")
    
    def _validate_preset_mapping(self, _recursion_depth: int = 0) -> bool:
        """Validar que los presets configurados funcionan correctamente con FluidSynth"""
        try:
            if not self.fs or self.sfid is None:
                print("   ❌ FluidSynth no inicializado - no se puede validar")
                return False
                
            print("   🔍 Validando mapeo de presets...")
            validation_errors = []
            
            for preset_id, preset_info in self.presets.items():
                try:
                    channel = preset_info['channel']
                    bank = preset_info['bank']
                    program = preset_info['program']
                    name = preset_info['name']
                    
                    print(f"      Validando preset {preset_id}: {name}")
                    print(f"         Canal={channel}, Bank={bank}, Program={program}")
                    
                    # Intentar seleccionar el programa
                    result = self.fs.program_select(channel, self.sfid, bank, program)
                    
                    if result == 0:  # Success en FluidSynth
                        print(f"         ✅ Preset {preset_id} válido")
                        
                        # Test opcional con nota corta para verificar sonido
                        try:
                            self.fs.noteon(channel, 60, 60)  # Nota suave
                            time.sleep(0.05)  # Muy corto para no molestar
                            self.fs.noteoff(channel, 60)
                        except:
                            pass  # Ignorar errores del test de sonido
                            
                    else:
                        error_msg = f"Preset {preset_id} ({name}): program_select falló (resultado: {result})"
                        print(f"         ❌ {error_msg}")
                        validation_errors.append(error_msg)
                        
                except Exception as preset_error:
                    error_msg = f"Preset {preset_id}: Error de validación - {preset_error}"
                    print(f"         ❌ {error_msg}")
                    validation_errors.append(error_msg)
            
            if validation_errors:
                print(f"   ⚠️  Se encontraron {len(validation_errors)} errores de validación:")
                for error in validation_errors:
                    print(f"      • {error}")
                print("   🔧 Intentando corregir automáticamente...")
                
                # Intentar correcciones automáticas (solo una vez)
                if _recursion_depth == 0 and self._fix_preset_mapping_issues():
                    print("   🔄 Re-validando después de correcciones...")
                    # Re-validar después de las correcciones (con profundidad 1 para evitar recursión infinita)
                    return self._validate_preset_mapping(_recursion_depth + 1)
                else:
                    print("   💡 Los presets pueden sonar extraños debido a estos errores")
                    return False
            else:
                print(f"   ✅ Todos los {len(self.presets)} presets validados correctamente")
                return True
                
        except Exception as e:
            print(f"   ❌ Error en validación de presets: {e}")
            return False
    
    def _fix_preset_mapping_issues(self) -> bool:
        """Intentar corregir problemas comunes en el mapeo de presets"""
        try:
            if not self.fs or self.sfid is None:
                print("   ❌ FluidSynth no inicializado - no se pueden corregir presets")
                return False
                
            print("   🔧 Intentando corregir problemas de mapeo...")
            fixes_applied = 0
            
            for preset_id, preset_info in self.presets.items():
                try:
                    channel = preset_info['channel']
                    bank = preset_info['bank']
                    program = preset_info['program']
                    name = preset_info['name']
                    
                    # Test actual preset
                    result = self.fs.program_select(channel, self.sfid, bank, program)
                    
                    if result != 0:  # Si falló
                        print(f"      🔧 Corrigiendo preset {preset_id}: {name}")
                        
                        # Intentar correcciones comunes
                        corrections = [
                            # Corregir banco de percusión
                            (128 if channel == 9 else 0, program),
                            # Usar bank 0 por defecto
                            (0, program),
                            # Si el programa está fuera de rango, usar 0
                            (bank, 0 if program > 127 else program),
                            # Último recurso: canal 0, bank 0, program 0 (Piano)
                            (0, 0)
                        ]
                        
                        for new_bank, new_program in corrections:
                            test_result = self.fs.program_select(channel, self.sfid, new_bank, new_program)
                            if test_result == 0:
                                # Actualizar preset corregido
                                self.presets[preset_id]['bank'] = new_bank
                                self.presets[preset_id]['program'] = new_program
                                
                                print(f"         ✅ Corregido: Bank {bank}→{new_bank}, Program {program}→{new_program}")
                                fixes_applied += 1
                                break
                        else:
                            print(f"         ❌ No se pudo corregir preset {preset_id}")
                            
                except Exception as preset_error:
                    print(f"         ❌ Error corrigiendo preset {preset_id}: {preset_error}")
            
            if fixes_applied > 0:
                print(f"   ✅ Se aplicaron {fixes_applied} correcciones")
                return True
            else:
                print("   ℹ️  No se necesitaron correcciones")
                return True
                
        except Exception as e:
            print(f"   ❌ Error corrigiendo presets: {e}")
            return False
    
    def _init_midi_input(self) -> bool:
        """Inicializar entrada MIDI con auto-conexión"""
        try:
            print("🎛️ Inicializando MIDI input...")
            
            # NO usar rtmidi callback para evitar crashes al desconectar
            # En su lugar, usar solo aconnect para conexiones directas
            print("   📡 Usando conexiones MIDI directas (sin callbacks rtmidi)")
            
            # Auto-conectar TODOS los dispositivos MIDI a FluidSynth
            self._auto_connect_midi_devices()
            return True
                
        except Exception as e:
            print(f"❌ Error inicializando MIDI: {e}")
            return False
    
    def _auto_connect_midi_devices(self):
        """Auto-conectar todos los dispositivos MIDI a FluidSynth"""
        try:
            import subprocess
            
            # Esperar un momento para que FluidSynth esté listo
            time.sleep(2)
            
            # Obtener lista de clientes MIDI
            result = subprocess.run(['aconnect', '-l'], capture_output=True, text=True)
            if result.returncode != 0:
                print("   ⚠️  No se pudo obtener lista de dispositivos MIDI")
                return
            
            lines = result.stdout.split('\n')
            midi_inputs = []
            fluidsynth_port = None
            
            # Parsear salida de aconnect
            for line in lines:
                line = line.strip()
                if line.startswith('client ') and '[type=kernel' in line:
                    # Dispositivo MIDI de hardware
                    client_num = line.split(':')[0].replace('client ', '')
                    device_name = line.split("'")[1] if "'" in line else "Unknown"
                    if 'System' not in device_name and 'Midi Through' not in device_name:
                        midi_inputs.append((client_num, device_name))
                elif line.startswith('client ') and 'FLUID Synth' in line:
                    # FluidSynth port
                    fluidsynth_port = line.split(':')[0].replace('client ', '')
            
            if not fluidsynth_port:
                print("   ⚠️  FluidSynth no encontrado para auto-conexión")
                return
            
            # Conectar cada dispositivo MIDI a FluidSynth y detectar controladores específicos
            connected_devices = []
            for client_num, device_name in midi_inputs:
                try:
                    cmd = ['aconnect', f'{client_num}:0', f'{fluidsynth_port}:0']
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        connected_devices.append(device_name)
                        print(f"   ✅ Conectado: {device_name} -> FluidSynth")
                        
                        # Detectar tipo de controlador específico
                        controller_type = self._detect_controller_type(device_name)
                        if controller_type:
                            self._register_controller(device_name, controller_type, client_num)
                    else:
                        print(f"   ⚠️  No se pudo conectar: {device_name}")
                except Exception as e:
                    print(f"   ❌ Error conectando {device_name}: {e}")
            
            if connected_devices:
                print(f"   🎹 Auto-conectados {len(connected_devices)} dispositivos MIDI")
                if self.connected_controllers:
                    print(f"   🎛️ Controladores específicos detectados: {len(self.connected_controllers)}")
                    for device, info in self.connected_controllers.items():
                        print(f"      • {info['type'].replace('_', ' ').title()}: {device}")
            else:
                print("   ⚠️  No se conectaron dispositivos MIDI automáticamente")
                
        except Exception as e:
            print(f"❌ Error en auto-conexión MIDI: {e}")
    
    def _detect_controller_type(self, device_name: str) -> Optional[str]:
        """Detectar tipo de controlador basado en el nombre del dispositivo"""
        import re
        
        for controller_type, patterns in self.controller_patterns.items():
            for pattern in patterns:
                if re.search(pattern, device_name, re.IGNORECASE):
                    return controller_type
        return None
    
    def _register_controller(self, device_name: str, controller_type: str, client_num: str):
        """Registrar controlador específico detectado"""
        try:
            # Información del controlador
            controller_info = {
                'type': controller_type,
                'client_num': client_num,
                'current_preset': 0,
                'presets': self.controller_presets.get(controller_type, {}),
                'connected': True,
                'last_seen': time.time(),  # Timestamp para detección de desconexión
                'detection_time': time.time()  # Cuando fue detectado
            }
            
            self.connected_controllers[device_name] = controller_info
            
            # Configurar presets iniciales del controlador en FluidSynth
            self._setup_controller_presets(controller_type)
            
            print(f"   🎛️ Registrado: {controller_type.replace('_', ' ').title()} ({device_name})")
            
        except Exception as e:
            print(f"❌ Error registrando controlador {device_name}: {e}")
    
    def _setup_controller_presets(self, controller_type: str):
        """Configurar presets del controlador en FluidSynth"""
        try:
            if controller_type not in self.controller_presets:
                return
                
            presets = self.controller_presets[controller_type]
            for preset_id, preset_info in presets.items():
                channel = preset_info['channel']
                bank = preset_info['bank']  
                program = preset_info['program']
                
                if self.fs and self.sfid is not None:
                    # Configurar banco e instrumento
                    self.fs.program_select(channel, self.sfid, bank, program)
                    print(f"      Canal {channel}: {preset_info['name']} (Bank {bank}, Program {program})")
            
        except Exception as e:
            print(f"❌ Error configurando presets de {controller_type}: {e}")
    
    def get_connected_controllers(self) -> Dict[str, Any]:
        """Obtener información de controladores conectados EN TIEMPO REAL"""
        try:
            # 🔄 DETECCIÓN EN TIEMPO REAL DE DISPOSITIVOS MIDI
            current_devices = self._scan_current_midi_devices()
            
            # Actualizar estado de controladores existentes
            controllers_to_remove = []
            for device_name, controller_info in self.connected_controllers.items():
                # Verificar si el dispositivo sigue conectado
                is_still_connected = any(device_name in device for device in current_devices)
                
                if is_still_connected:
                    controller_info['connected'] = True
                    controller_info['last_seen'] = time.time()
                else:
                    controller_info['connected'] = False
                    # Si lleva desconectado más de 10 segundos, remover
                    if time.time() - controller_info.get('last_seen', 0) > 10:
                        controllers_to_remove.append(device_name)
            
            # Remover controladores desconectados
            for device_name in controllers_to_remove:
                print(f"   🔌 Removiendo controlador desconectado: {device_name}")
                del self.connected_controllers[device_name]
                
                # Notificar desconexión a clientes web
                if self.socketio:
                    self.socketio.emit('controller_disconnected', {
                        'device_name': device_name,
                        'timestamp': time.time()
                    })
            
            # Detectar nuevos dispositivos
            for device_name in current_devices:
                if device_name not in self.connected_controllers:
                    controller_type = self._detect_controller_type(device_name)
                    if controller_type:
                        print(f"   ✅ Nuevo controlador detectado: {device_name} ({controller_type})")
                        self._register_controller(device_name, controller_type, 0)
                        
                        # Notificar nueva conexión a clientes web
                        if self.socketio:
                            self.socketio.emit('controller_connected', {
                                'device_name': device_name,
                                'controller_type': controller_type,
                                'timestamp': time.time()
                            })
            
            return {
                'controllers': self.connected_controllers,
                'count': len(self.connected_controllers),
                'types': list(set(info['type'] for info in self.connected_controllers.values()))
            }
            
        except Exception as e:
            print(f"❌ Error detectando controladores: {e}")
            return {
                'controllers': self.connected_controllers,
                'count': len(self.connected_controllers),
                'types': []
            }
    
    def _scan_current_midi_devices(self) -> List[str]:
        """Escanear dispositivos MIDI conectados actualmente"""
        try:
            import subprocess
            
            # Obtener lista actual de clientes MIDI usando aconnect
            result = subprocess.run(['aconnect', '-l'], capture_output=True, text=True, timeout=3)
            if result.returncode != 0:
                return []
            
            # Parsear salida para encontrar dispositivos de entrada
            current_devices = []
            lines = result.stdout.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('client ') and ':' in line:
                    try:
                        # Buscar patrones conocidos de controladores MIDI
                        keywords = ['MIDI', 'MPK', 'Pico', 'Captain', 'Fishman', 'TriplePlay', 'UMC', 'Behringer']
                        if any(keyword.lower() in line.lower() for keyword in keywords):
                            
                            # Extraer nombre del dispositivo de diferentes formatos
                            if '[' in line:
                                # Formato: client 24: 'MPK mini 3' [type=kernel,card=2]
                                device_name = line.split("'")[1] if "'" in line else line.split('[')[0].split(':')[1].strip()
                            else:
                                # Formato simple: client 24: MPK mini 3
                                device_name = line.split(':')[1].strip()
                            
                            # Limpiar nombre y validar
                            device_name = device_name.replace("'", "").strip()
                            
                            if device_name and device_name not in ['System', 'Midi Through', 'Timer', 'Announce']:
                                current_devices.append(device_name)
                                
                    except Exception as e:
                        # Ignorar errores de parsing individual
                        continue
            
            return current_devices
            
        except Exception as e:
            print(f"⚠️  Error escaneando dispositivos MIDI: {e}")
            return []
    
    def _apply_channel_effect(self, channel: int, effect_name: str, value: int) -> bool:
        """Aplicar efecto específico a un canal MIDI"""
        try:
            if not self.fs:
                return False
                
            # Mapeo de efectos a Control Change messages
            effect_cc_map = {
                'volume': 7,
                'reverb': 91,
                'chorus': 93,
                'cutoff': 74,
                'resonance': 71,
                'expression': 11,
                'sustain': 64
            }
            
            if effect_name in effect_cc_map:
                cc_number = effect_cc_map[effect_name]
                self.fs.cc(channel, cc_number, value)
                print(f"   🎛️ Canal {channel}: {effect_name} = {value}")
                return True
                
            return False
            
        except Exception as e:
            print(f"❌ Error aplicando efecto {effect_name} en canal {channel}: {e}")
            return False
    
    def _monitor_midi_connections(self):
        """Monitorear y reconectar dispositivos MIDI dinámicamente"""
        last_device_count = 0
        print("🔍 Iniciando monitoreo MIDI...")
        
        try:
            while self.is_running:
                try:
                    time.sleep(3)  # Verificar cada 3 segundos
                    
                    # Obtener dispositivos actuales
                    current_device_count = self._get_midi_device_count()
                    
                    # Debug: mostrar conteo cada 30 segundos
                    if hasattr(self, '_debug_counter'):
                        self._debug_counter += 1
                    else:
                        self._debug_counter = 1
                    
                    if self._debug_counter % 10 == 0:  # Cada 30 segundos
                        print(f"🔍 Dispositivos MIDI actuales: {current_device_count}")
                    
                    # Si cambió el número de dispositivos, reconectar todo
                    if current_device_count != last_device_count:
                        print(f"🔄 CAMBIO DETECTADO: {last_device_count} -> {current_device_count} dispositivos MIDI")
                        print(f"⏰ Timestamp: {time.strftime('%H:%M:%S')}")
                        
                        # Limpiar conexiones existentes
                        print("   🧹 Limpiando conexiones antiguas...")
                        self._disconnect_all_midi()
                        
                        # Esperar un momento para estabilizar
                        time.sleep(2)
                        
                        # Reconectar todos los dispositivos
                        print("   🔗 Reconectando dispositivos...")
                        self._auto_connect_midi_devices()
                        
                        last_device_count = current_device_count
                        print(f"   ✅ Reconexión completada")
                        
                except Exception as inner_e:
                    print(f"⚠️  Error en ciclo de monitoreo: {inner_e}")
                    time.sleep(5)  # Esperar más tiempo si hay error
                    
        except Exception as e:
            print(f"❌ Error crítico monitoreando MIDI: {e}")
            # Reintentar después de error crítico
            time.sleep(10)
            if self.is_running:
                print("🔄 Reintentando monitoreo MIDI...")
                self._monitor_midi_connections()
    
    def _get_midi_device_count(self):
        """Obtener número actual de dispositivos MIDI"""
        try:
            import subprocess
            result = subprocess.run(['aconnect', '-l'], capture_output=True, text=True)
            if result.returncode != 0:
                return 0
            
            # Contar dispositivos MIDI de hardware (excluyendo System y Midi Through)
            count = 0
            for line in result.stdout.split('\n'):
                if (line.strip().startswith('client ') and 
                    '[type=kernel' in line and 
                    'System' not in line and 
                    'Midi Through' not in line):
                    count += 1
            return count
        except:
            return 0
    
    def _disconnect_all_midi(self):
        """Desconectar todas las conexiones MIDI existentes"""
        try:
            import subprocess
            
            # Obtener todas las conexiones activas
            result = subprocess.run(['aconnect', '-l'], capture_output=True, text=True)
            if result.returncode != 0:
                return
            
            # Parsear y desconectar
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Connecting To:' in line:
                    # Extraer información de conexión
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        target = parts[2]  # Ej: "128:0"
                        try:
                            subprocess.run(['aconnect', '-d', ':0', target], 
                                         capture_output=True, timeout=2)
                        except:
                            pass
                            
        except Exception as e:
            print(f"⚠️  Error desconectando MIDI: {e}")
    
    def _midi_callback(self, message, data):
        """Callback para mensajes MIDI entrantes - OPTIMIZADO PARA BAJA LATENCIA"""
        msg, delta_time = message
        
        # 🚀 Procesamiento ultra-rápido - solo lo esencial
        if len(msg) >= 2 and 0xC0 <= msg[0] <= 0xCF and 0 <= msg[1] <= 7:
            # Program Change directo - sin logs para velocidad máxima
            if self._set_instrument(msg[1]):
                # Notificación web solo si es necesario
                if self.socketio:
                    try:
                        self.socketio.emit('instrument_changed', {
                            'pc': msg[1],
                            'name': self.presets[msg[1]]['name']
                        })
                    except:
                        pass
    
    def _set_instrument(self, pc: int) -> bool:
        """Cambiar instrumento activo usando presets - CORREGIDO Y OPTIMIZADO"""
        try:
            # 🚀 Validación rápida
            pc_int = int(pc)
            if pc_int not in self.presets:
                print(f"   ❌ Preset {pc_int} no existe en sistema principal")
                return False
            
            # 🚀 Verificación rápida de FluidSynth
            if not self.fs or self.sfid is None:
                print("   ❌ FluidSynth no inicializado")
                return False
            
            # 🚀 Obtener preset y aplicar inmediatamente
            preset = self.presets[pc_int]
            channel = preset['channel']
            bank = preset['bank']
            program = preset['program']
            
            print(f"   🎹 Sistema principal: Canal={channel}, Bank={bank}, Program={program}")
            
            # 🚀 MÉTODO MÚLTIPLE para asegurar que funcione
            # 1. Program Select
            result = self.fs.program_select(channel, self.sfid, bank, program)
            print(f"   🎹 program_select resultado: {result}")
            
            if result == 0:  # Success
                # 2. Program Change adicional para asegurar
                try:
                    self.fs.program_change(channel, program)
                    print(f"   📨 Program Change enviado: Canal {channel}, Programa {program}")
                except:
                    pass
                
                # 3. Nota de prueba para activar el sonido
                try:
                    self.fs.noteon(channel, 60, 80)  # Nota C4
                    time.sleep(0.05)  # Muy breve para no molestar
                    self.fs.noteoff(channel, 60)
                    print(f"   🎵 Nota de prueba: Canal {channel}")
                except:
                    pass
                
                self.current_instrument = pc_int
                
                # 🚀 Aplicar efectos para asegurar volumen
                self._apply_current_effects_fast()
                
                print(f"   ✅ Sistema principal: Preset {pc_int} ({preset['name']}) activado")
                return True
            else:
                print(f"   ❌ program_select falló: {result}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error en _set_instrument: {e}")
            return False
    
    def _set_effect(self, effect_name: str, value: int) -> bool:
        """Aplicar efecto global"""
        print(f"🎛️ _set_effect llamado: {effect_name} = {value}")
        try:
            if not self.fs:
                print("   ❌ FluidSynth no inicializado")
                return False
                
            print(f"   🔧 Aplicando {effect_name}...")
            if self.fs:  # Verificar que FluidSynth esté inicializado
                if effect_name == 'master_volume':
                    # Volumen master - estrategia simplificada y más efectiva
                    print(f"      Configurando volumen master: {value}%")
                    
                    # Método principal: CC 7 (Main Volume) en todos los canales usados
                    volume_cc = int((value / 100.0) * 127)
                    print(f"      Aplicando CC 7 (Main Volume): {volume_cc}")
                    
                    # Aplicar a todos los canales (incluyen percusión en canal 9)
                    cc_success = 0
                    for channel in range(16):
                        try:
                            self.fs.cc(channel, 7, volume_cc)  # CC 7 = Main Volume
                            cc_success += 1
                        except Exception as e:
                            print(f"         ❌ Error CC volume canal {channel}: {e}")
                    
                    # Método alternativo: synth.gain
                    try:
                        gain = max(0.1, min(2.0, (value / 100.0) * 1.5))  # Entre 0.1 y 2.0
                        self.fs.setting('synth.gain', gain)
                        print(f"      ✅ synth.gain: {gain}")
                    except:
                        print(f"      ⚠️  synth.gain no disponible")
                    
                    print(f"      ✅ Volume aplicado en {cc_success}/16 canales")
                    
                elif effect_name == 'global_reverb':
                    # Reverb global - CC 91 en todos los canales
                    reverb_value = int((value / 100.0) * 127)
                    print(f"      Aplicando Reverb CC 91: {reverb_value}")
                    cc_success = 0
                    for channel in range(16):
                        try:
                            self.fs.cc(channel, 91, reverb_value)  # CC 91 = Reverb Send
                            cc_success += 1
                        except Exception as e:
                            print(f"         ❌ Error CC reverb canal {channel}: {e}")
                    print(f"      ✅ Reverb aplicado en {cc_success}/16 canales")
                    
                elif effect_name == 'global_chorus':
                    # Chorus global - CC 93 en todos los canales
                    chorus_value = int((value / 100.0) * 127)
                    print(f"      Aplicando Chorus CC 93: {chorus_value}")
                    cc_success = 0
                    for channel in range(16):
                        try:
                            self.fs.cc(channel, 93, chorus_value)  # CC 93 = Chorus Send
                            cc_success += 1
                        except Exception as e:
                            print(f"         ❌ Error CC chorus canal {channel}: {e}")
                    print(f"      ✅ Chorus aplicado en {cc_success}/16 canales")
                        
                elif effect_name == 'global_cutoff':
                    # Filtro de corte - CC 74 (Brightness/Cutoff)
                    cutoff_value = int((value / 100.0) * 127)
                    print(f"      Aplicando Cutoff CC 74: {cutoff_value}")
                    cc_success = 0
                    for channel in range(16):
                        try:
                            self.fs.cc(channel, 74, cutoff_value)  # CC 74 = Brightness
                            cc_success += 1
                        except Exception as e:
                            print(f"         ❌ Error CC cutoff canal {channel}: {e}")
                    print(f"      ✅ Cutoff aplicado en {cc_success}/16 canales")
                        
                elif effect_name == 'global_resonance':
                    # Resonancia - CC 71 (Sound Timbre/Resonance)
                    resonance_value = int((value / 100.0) * 127)
                    print(f"      Aplicando Resonance CC 71: {resonance_value}")
                    cc_success = 0
                    for channel in range(16):
                        try:
                            self.fs.cc(channel, 71, resonance_value)  # CC 71 = Resonance
                            cc_success += 1
                        except Exception as e:
                            print(f"         ❌ Error CC resonance canal {channel}: {e}")
                    print(f"      ✅ Resonance aplicado en {cc_success}/16 canales")
                
                else:
                    print(f"      ⚠️  Efecto {effect_name} no reconocido")
                    return False
            
            self.effects[effect_name] = value
            
            # Guardar en base de datos
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', 
                             (effect_name, str(value)))
                conn.commit()
            
            print(f"🎹 {effect_name}: {value}% - ✅ COMPLETADO")
            return True
            
        except Exception as e:
            print(f"❌ Error aplicando efecto {effect_name}: {e}")
            return False
    
    def _apply_current_effects(self):
        """Aplicar todos los efectos actuales (útil después de cambio de instrumento)"""
        try:
            print("🎛️ Aplicando efectos actuales...")
            if not self.fs:
                print("   ❌ FluidSynth no inicializado")
                return
            
            # Aplicar efectos directamente usando Control Changes para evitar recursión
            for effect_name, value in self.effects.items():
                if effect_name == 'master_volume':
                    volume_cc = int((value / 100.0) * 127)
                    for channel in range(16):
                        try:
                            self.fs.cc(channel, 7, volume_cc)  # CC 7 = Main Volume
                        except:
                            pass
                            
                elif effect_name == 'global_reverb':
                    reverb_value = int((value / 100.0) * 127)
                    for channel in range(16):
                        try:
                            self.fs.cc(channel, 91, reverb_value)  # CC 91 = Reverb Send
                        except:
                            pass
                            
                elif effect_name == 'global_chorus':
                    chorus_value = int((value / 100.0) * 127)
                    for channel in range(16):
                        try:
                            self.fs.cc(channel, 93, chorus_value)  # CC 93 = Chorus Send
                        except:
                            pass
                            
                elif effect_name == 'global_cutoff':
                    cutoff_value = int((value / 100.0) * 127)
                    for channel in range(16):
                        try:
                            self.fs.cc(channel, 74, cutoff_value)  # CC 74 = Brightness
                        except:
                            pass
                            
                elif effect_name == 'global_resonance':
                    resonance_value = int((value / 100.0) * 127)
                    for channel in range(16):
                        try:
                            self.fs.cc(channel, 71, resonance_value)  # CC 71 = Resonance
                        except:
                            pass
            
            print("✅ Efectos actuales aplicados")
        except Exception as e:
            print(f"❌ Error aplicando efectos actuales: {e}")
    
    def _apply_current_effects_fast(self):
        """Aplicar efectos actuales de forma ultra-rápida (sin logs, solo lo esencial)"""
        try:
            if not self.fs:
                return
            
            # 🚀 Solo aplicar efectos críticos de forma directa
            for effect_name, value in self.effects.items():
                cc_value = int((value / 100.0) * 127)
                
                if effect_name == 'master_volume':
                    # Solo canales activos para velocidad
                    for channel in [0, 1, 2, 9]:  # Solo canales principales
                        try:
                            self.fs.cc(channel, 7, cc_value)
                        except:
                            pass
                elif effect_name == 'global_reverb':
                    for channel in [0, 1, 2, 9]:
                        try:
                            self.fs.cc(channel, 91, cc_value)
                        except:
                            pass
        except:
            pass  # Sin error handling para velocidad máxima
    
    def _simulate_midi_program_change(self, pc_number: int) -> bool:
        """Simular mensaje MIDI Program Change internamente - CORREGIDO"""
        try:
            print(f"🎛️ Simulando MIDI Program Change {pc_number}")
            
            # ESTRATEGIA 1: Verificar primero en presets del sistema principal (0-7)
            if 0 <= pc_number <= 7 and pc_number in self.presets:
                print(f"   📋 Usando preset del sistema principal: {pc_number}")
                return self._set_instrument(pc_number)
            
            # ESTRATEGIA 2: Buscar en controladores activos para presets fuera del rango 0-7
            for controller_name, controller in self.active_controllers.items():
                controller_presets = controller.get('presets', {})
                if pc_number in controller_presets:
                    preset_info = controller_presets[pc_number]
                    print(f"   🎛️ Usando preset de controlador {controller_name}: {pc_number} ({preset_info['name']})")
                    
                    # Aplicar preset directamente usando FluidSynth
                    return self._apply_controller_preset_direct(controller, pc_number, preset_info)
            
            # ESTRATEGIA 3: Mapear preset alto a rango del sistema (fallback)
            if pc_number > 7:
                mapped_preset = pc_number % 8  # Mapear 8->0, 9->1, 10->2, etc.
                if mapped_preset in self.presets:
                    print(f"   🔄 Mapeando preset {pc_number} -> {mapped_preset}")
                    return self._set_instrument(mapped_preset)
            
            print(f"❌ Preset {pc_number} no encontrado en ningún sistema")
            return False
            
        except Exception as e:
            print(f"❌ Error simulando MIDI Program Change: {e}")
            return False
    
    def _apply_controller_preset_direct(self, controller, pc_number: int, preset_info) -> bool:
        """Aplicar preset de controlador directamente con FluidSynth - MÉTODO CORREGIDO"""
        try:
            if not self.fs or self.sfid is None:
                print("   ❌ FluidSynth no inicializado")
                return False
            
            # Obtener información del controlador
            device_info = controller.get('device_info', {})
            channel = device_info.get('midi_channel', 0)
            
            # Obtener información del preset
            program = preset_info.get('program', 0)
            bank = preset_info.get('bank', 0)
            
            print(f"   🎹 Aplicando: Canal={channel}, Bank={bank}, Program={program}")
            
            # MÉTODO 1: Program Select directo
            result = self.fs.program_select(channel, self.sfid, bank, program)
            print(f"   🎹 program_select resultado: {result}")
            
            if result == 0:  # Éxito
                # MÉTODO 2: Enviar Program Change MIDI para asegurar
                try:
                    # Enviar PC message directo al canal
                    self.fs.program_change(channel, program)
                    print(f"   📨 Program Change enviado: Canal {channel}, Programa {program}")
                except:
                    pass
                
                # MÉTODO 3: Activar nota de prueba para forzar sonido
                try:
                    self.fs.noteon(channel, 60, 80)  # Nota C4 para activar el sonido
                    time.sleep(0.1)  # Muy breve
                    self.fs.noteoff(channel, 60)     # Apagar nota
                    print(f"   🎵 Nota de prueba enviada en canal {channel}")
                except:
                    pass
                
                # Actualizar estado del controlador
                controller['current_preset'] = pc_number
                
                # Aplicar efectos para asegurar que se escuche
                self._apply_current_effects_fast()
                
                print(f"   ✅ Preset {pc_number} aplicado en controlador")
                return True
            else:
                print(f"   ❌ program_select falló: {result}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error aplicando preset de controlador: {e}")
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
    
    def _get_fluidsynth_instruments(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get available instruments from FluidSynth"""
        if self._instrument_library_cache:
            return self._instrument_library_cache
        
        if self.instrument_extractor:
            try:
                instruments = self.instrument_extractor.get_gm_instruments()
                self._instrument_library_cache = instruments
                print(f"✅ Cargados {sum(len(cat) for cat in instruments.values())} instrumentos de FluidSynth")
                return instruments
            except Exception as e:
                print(f"⚠️  Error extrayendo instrumentos: {e}")
        
        # Fallback instruments
        fallback = {
            "Piano": [
                {"id": 0, "name": "Acoustic Grand Piano", "program": 0, "bank": 0, "channel": 0, "icon": "🎹"}
            ],
            "Guitar": [
                {"id": 24, "name": "Acoustic Guitar (nylon)", "program": 24, "bank": 0, "channel": 0, "icon": "🎸"}
            ],
            "Bass": [
                {"id": 32, "name": "Acoustic Bass", "program": 32, "bank": 0, "channel": 1, "icon": "🎸"}
            ],
            "Brass": [
                {"id": 56, "name": "Trumpet", "program": 56, "bank": 0, "channel": 4, "icon": "🎺"}
            ],
            "Reed": [
                {"id": 65, "name": "Alto Sax", "program": 65, "bank": 0, "channel": 5, "icon": "🎷"}
            ],
            "Strings": [
                {"id": 48, "name": "String Ensemble 1", "program": 48, "bank": 0, "channel": 3, "icon": "🎻"}
            ],
            "Organ": [
                {"id": 16, "name": "Drawbar Organ", "program": 16, "bank": 0, "channel": 0, "icon": "🎹"}
            ],
            "Pipe": [
                {"id": 73, "name": "Flute", "program": 73, "bank": 0, "channel": 6, "icon": "🪈"}
            ],
            "Drums": [
                {"id": 128, "name": "Standard Drum Kit", "program": 0, "bank": 128, "channel": 9, "icon": "🥁"}
            ]
        }
        
        self._instrument_library_cache = fallback
        return fallback
    
    def _save_preset_to_db(self, preset_id: int, preset_data: Dict[str, Any]) -> bool:
        """Save preset configuration to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create presets table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS presets (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        program INTEGER NOT NULL,
                        bank INTEGER NOT NULL,
                        channel INTEGER NOT NULL,
                        icon TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Insert or update preset
                cursor.execute('''
                    INSERT OR REPLACE INTO presets (id, name, program, bank, channel, icon)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    preset_id,
                    preset_data['name'],
                    preset_data['program'],
                    preset_data['bank'],
                    preset_data['channel'],
                    preset_data['icon']
                ))
                
                conn.commit()
                print(f"✅ Preset {preset_id} guardado en DB: {preset_data['name']}")
                return True
                
        except Exception as e:
            print(f"❌ Error guardando preset en DB: {e}")
            return False
    
    def _load_presets_from_db(self) -> bool:
        """Load presets from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM presets ORDER BY id')
                rows = cursor.fetchall()
                
                for row in rows:
                    preset_id, name, program, bank, channel, icon, _ = row
                    if 0 <= preset_id <= 7:
                        self.presets[preset_id] = {
                            'name': name,
                            'program': program,
                            'bank': bank,
                            'channel': channel,
                            'icon': icon
                        }
                
                if rows:
                    print(f"✅ Cargados {len(rows)} presets desde DB")
                    return True
                
        except Exception as e:
            print(f"⚠️  Error cargando presets desde DB: {e}")
        
        return False
    
    def _save_config(self) -> bool:
        """Save current configuration to database"""
        try:
            # Save effects
            for effect, value in self.effects.items():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', 
                                 (effect, str(value)))
                    conn.commit()
            
            # Save current instrument
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', 
                             ('current_instrument', str(self.current_instrument)))
                conn.commit()
            
            return True
            
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")
            return False
    
    def _load_config(self) -> bool:
        """Load configuration from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT key, value FROM config')
                rows = cursor.fetchall()
                
                for key, value in rows:
                    if key in self.effects:
                        try:
                            self.effects[key] = int(value)
                        except ValueError:
                            pass
                    elif key == 'current_instrument':
                        try:
                            self.current_instrument = int(value)
                        except ValueError:
                            pass
            
            return True
            
        except Exception as e:
            print(f"⚠️  Error cargando configuración: {e}")
            return False
    
    def _init_web_server(self):
        """Inicializar servidor web integrado con estructura modular"""
        print("🌐 Inicializando servidor web...")
        
        # Configure Flask app
        template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web', 'templates')
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web', 'static')
        
        self.app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
        self.app.config['SECRET_KEY'] = 'guitar-midi-complete-2024'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Register API routes
        api_bp = init_api(self)
        self.app.register_blueprint(api_bp)
        
        # Main route
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        # Debug route for testing API
        @self.app.route('/debug')
        def debug():
            return render_template('debug.html')
        
        # WebSocket Events
        @self.socketio.on('connect')
        def handle_connect():
            print("📱 Cliente conectado")
            emit('status_update', {
                'current_instrument': self.current_instrument,
                'presets': self.presets,
                'effects': self.effects
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            print("📱 Cliente desconectado")
        
        print("✅ Servidor web listo")
    
    def run(self):
        """Ejecutar sistema completo"""
        try:
            print("🚀 Iniciando Guitar-MIDI Complete System...")
            
            # 1. Cargar configuración y presets desde DB
            self._load_config()
            self._load_presets_from_db()
            
            # 2. Auto-detectar audio
            self._auto_detect_audio()
            
            # 3. Inicializar FluidSynth
            if not self._init_fluidsynth():
                print("❌ Error crítico: FluidSynth no pudo inicializarse")
                return False
            
            # 4. Inicializar MIDI (opcional)
            self._init_midi_input()
            
            # 5. Inicializar servidor web
            self._init_web_server()
            
            # 6. Inicializar sistema modular (NUEVO)
            self._init_modular_system()
            
            # 7. Iniciar monitoreo MIDI en hilo separado
            midi_monitor_thread = threading.Thread(target=self._monitor_midi_connections, daemon=True)
            midi_monitor_thread.start()
            
            # 7.5. Iniciar monitoreo automático de dispositivos MIDI (NUEVO)
            self.start_device_monitoring()
            
            # 8. Mostrar información del sistema
            self._show_system_info()
            
            # 9. Ejecutar servidor (bloqueante)
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
        
        # Detener monitoreo de dispositivos
        self.stop_device_monitoring()
        
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
        
        current_name = self.presets[self.current_instrument]['name']
        print(f"🎹 Instrumento actual: {current_name} (PC {self.current_instrument})")
        
        print("\n📱 Para conectar desde celular:")
        print("1. Conectar a WiFi 'Guitar-MIDI' (contraseña: guitarmidi2024)")
        print("2. Abrir: http://192.168.4.1:5000")
        print("\n⌨️  Atajos: P=PANIC, 0-7=Instrumentos")
        print("🔴 Ctrl+C para detener")
        print("="*60 + "\n")
    
    # ============================================================================
    # SISTEMA MODULAR - NUEVOS MÉTODOS
    # ============================================================================
    
    def _init_modular_system(self):
        """Inicializar detección de dispositivos MIDI específicos (INTEGRADO)"""
        try:
            print("🔌 Inicializando detección de dispositivos MIDI específicos...")
            
            # Detectar dispositivos MIDI conectados actualmente
            self._detect_specific_midi_devices()
            
            print("   ✅ Detección de dispositivos iniciada")
            
        except Exception as e:
            print(f"   ❌ Error inicializando detección: {e}")
    
    def _detect_specific_midi_devices(self):
        """Detectar dispositivos MIDI específicos conectados"""
        try:
            import rtmidi
            
            # Obtener dispositivos MIDI disponibles
            midiin = rtmidi.MidiIn()
            available_ports = midiin.get_ports()
            
            print(f"   📡 Escaneando {len(available_ports)} puertos MIDI...")
            
            # Patrones de detección (CORREGIDOS para tus dispositivos)
            device_patterns = {
                'akai_mpk_mini': [r'.*MPK.*mini.*', r'.*MPK.*Mini.*', r'.*Akai.*MPK.*', r'MPK.*mini.*3.*', r'.*AKAI.*MPK.*'],
                'midi_captain': [r'.*Pico.*', r'.*Captain.*', r'.*MIDI.*Captain.*', r'Pico.*Captain.*', r'.*Pico.*MIDI.*'],
                'fishman_tripleplay': [r'.*Fishman.*Triple.*', r'.*TriplePlay.*', r'.*Fishman.*'],
                'mvave_pocket': [r'.*MVAVE.*Pocket.*', r'.*Pocket.*MVAVE.*', r'MVAVE.*'],
                'hexaphonic': [r'.*HEX.*', r'.*Hexaphonic.*', r'.*Guitar.*Synth.*'],
                'generic_midi': [r'.*']  # Catch-all para otros dispositivos
            }
            
            detected_devices = []
            
            for i, port_name in enumerate(available_ports):
                print(f"   🎛️ Puerto {i}: {port_name}")
                
                # Detectar tipo de dispositivo
                device_type = None
                for dev_type, patterns in device_patterns.items():
                    for pattern in patterns:
                        import re
                        if re.search(pattern, port_name, re.IGNORECASE):
                            device_type = dev_type
                            break
                    if device_type and device_type != 'generic_midi':
                        break
                
                if device_type and device_type != 'generic_midi':
                    print(f"      ✅ Detectado: {device_type}")
                    detected_devices.append({
                        'name': port_name,
                        'type': device_type,
                        'port_index': i,
                        'connected': True
                    })
                    
                    # Registrar en el sistema
                    self._register_detected_device(port_name, device_type, i)
            
            if detected_devices:
                print(f"   🎯 Dispositivos específicos detectados: {len(detected_devices)}")
            else:
                print("   💡 No se detectaron dispositivos específicos (usando sistema original)")
            
            midiin.close_port()
            
        except Exception as e:
            print(f"   ❌ Error detectando dispositivos: {e}")
    
    def _register_detected_device(self, device_name: str, device_type: str, port_index: int):
        """Registrar dispositivo detectado en el sistema"""
        try:
            # Información básica del dispositivo
            device_info = {
                'name': device_name,
                'type': device_type,
                'port_index': port_index,
                'connected': True,
                'preset_start': len(self.active_controllers) * 8,  # 8 presets por dispositivo
                'preset_end': (len(self.active_controllers) * 8) + 7,
                'midi_channel': len(self.active_controllers) % 16,  # Rotar canales
                'last_connected': time.time()
            }
            
            # Crear controlador simple
            controller = self._create_simple_controller(device_info)
            
            if controller:
                self.active_controllers[device_name] = controller
                print(f"      🎮 Controlador creado: Presets {device_info['preset_start']}-{device_info['preset_end']}, Canal {device_info['midi_channel']}")
                
                # INICIALIZAR con el primer preset para que suene inmediatamente
                self._initialize_controller_preset(controller)
                
        except Exception as e:
            print(f"   ❌ Error registrando dispositivo {device_name}: {e}")
    
    def _create_simple_controller(self, device_info: dict):
        """Crear controlador simple integrado"""
        try:
            device_type = device_info['type']
            
            # Presets por defecto según el tipo
            if device_type == 'akai_mpk_mini':
                presets = {
                    device_info['preset_start'] + 0: {'name': 'MPK Piano', 'program': 0, 'bank': 0, 'icon': '🎹'},
                    device_info['preset_start'] + 1: {'name': 'MPK E.Piano', 'program': 4, 'bank': 0, 'icon': '🎹'},
                    device_info['preset_start'] + 2: {'name': 'MPK Organ', 'program': 16, 'bank': 0, 'icon': '🎹'},
                    device_info['preset_start'] + 3: {'name': 'MPK Synth', 'program': 80, 'bank': 0, 'icon': '🎛️'},
                    device_info['preset_start'] + 4: {'name': 'MPK Bass', 'program': 38, 'bank': 0, 'icon': '🎸'},
                    device_info['preset_start'] + 5: {'name': 'MPK Strings', 'program': 48, 'bank': 0, 'icon': '🎻'},
                    device_info['preset_start'] + 6: {'name': 'MPK Brass', 'program': 56, 'bank': 0, 'icon': '🎺'},
                    device_info['preset_start'] + 7: {'name': 'MPK Lead', 'program': 81, 'bank': 0, 'icon': '🎛️'}
                }
            elif device_type == 'fishman_tripleplay':
                presets = {
                    device_info['preset_start'] + 0: {'name': 'TP Acoustic', 'program': 24, 'bank': 0, 'icon': '🎸'},
                    device_info['preset_start'] + 1: {'name': 'TP Electric', 'program': 27, 'bank': 0, 'icon': '🎸'},
                    device_info['preset_start'] + 2: {'name': 'TP Distortion', 'program': 30, 'bank': 0, 'icon': '🎸'},
                    device_info['preset_start'] + 3: {'name': 'TP Violin', 'program': 40, 'bank': 0, 'icon': '🎻'},
                    device_info['preset_start'] + 4: {'name': 'TP Cello', 'program': 42, 'bank': 0, 'icon': '🎻'},
                    device_info['preset_start'] + 5: {'name': 'TP Trumpet', 'program': 56, 'bank': 0, 'icon': '🎺'},
                    device_info['preset_start'] + 6: {'name': 'TP Flute', 'program': 73, 'bank': 0, 'icon': '🪈'},
                    device_info['preset_start'] + 7: {'name': 'TP Synth', 'program': 80, 'bank': 0, 'icon': '🎛️'}
                }
            else:
                # Presets genéricos
                presets = {
                    device_info['preset_start'] + i: {
                        'name': f'{device_type.title()} {i+1}', 
                        'program': i, 
                        'bank': 0, 
                        'icon': '🎵'
                    } for i in range(8)
                }
            
            # Controlador simple
            controller = {
                'device_info': device_info,
                'presets': presets,
                'current_preset': device_info['preset_start'],
                'active': True
            }
            
            return controller
            
        except Exception as e:
            print(f"   ❌ Error creando controlador simple: {e}")
            return None
    
    def _initialize_controller_preset(self, controller):
        """Inicializar controlador con su primer preset activo"""
        try:
            device_info = controller['device_info']
            presets = controller['presets']
            
            if not presets:
                return
            
            # Tomar el primer preset disponible
            first_preset_id = min(presets.keys())
            first_preset = presets[first_preset_id]
            
            # Aplicar preset inmediatamente al FluidSynth
            if self.fs and self.sfid is not None:
                channel = device_info['midi_channel']
                bank = first_preset.get('bank', 0)
                program = first_preset.get('program', 0)
                
                self.fs.program_select(channel, self.sfid, bank, program)
                controller['current_preset'] = first_preset_id
                
                print(f"      🎵 Preset inicial: {first_preset['name']} (Programa {program}, Canal {channel})")
                
        except Exception as e:
            print(f"   ❌ Error inicializando preset: {e}")
    
    def _modular_callback(self, event_type: str, data: dict):
        """Callback para eventos del sistema modular"""
        try:
            if event_type == 'midi_device_connected':
                device_name = data.get('name', 'Unknown')
                device_type = data.get('type', 'unknown')
                print(f"🎛️ Dispositivo MIDI conectado: {device_name} ({device_type})")
                
                # Crear controlador específico
                controller = self._create_modular_controller(device_name, device_type, data)
                if controller:
                    controller.activate()
                    self.active_controllers[device_name] = controller
                    print(f"   ✅ Controlador {device_name} activado")
                    
            elif event_type == 'midi_device_disconnected':
                if data and 'name' in data:
                    device_name = data['name']
                    if device_name in self.active_controllers:
                        self.active_controllers[device_name].deactivate()
                        del self.active_controllers[device_name]
                        print(f"🔌 Controlador {device_name} desactivado")
                        
            elif event_type == 'audio_device_connected':
                device_name = data.get('name', 'Unknown')
                device_type = data.get('type', 'unknown')
                print(f"🎤 Dispositivo de audio conectado: {device_name} ({device_type})")
                
        except Exception as e:
            print(f"❌ Error en callback modular: {e}")
    
    def _create_modular_controller(self, device_name: str, device_type: str, device_info: dict):
        """Crear controlador específico según el tipo"""
        try:
            if device_type == 'akai_mpk_mini':
                from modules.controllers.akai_mpk_mini import AkaiMPKMiniController
                return AkaiMPKMiniController(device_name, device_info, self._controller_callback)
            elif device_type == 'fishman_tripleplay':
                from modules.controllers.fishman_tripleplay import FishmanTriplePlayController
                return FishmanTriplePlayController(device_name, device_info, self._controller_callback)
            else:
                # Dispositivos ya manejados por el sistema original
                return None
                
        except ImportError as e:
            print(f"   ⚠️ Controlador {device_type} no disponible: {e}")
            return None
        except Exception as e:
            print(f"   ❌ Error creando controlador {device_type}: {e}")
            return None
    
    def _controller_callback(self, event_type: str, data: dict):
        """Callback para eventos de controladores específicos"""
        try:
            if event_type == 'midi_note':
                self._handle_modular_note(data)
            elif event_type == 'midi_cc':
                self._handle_modular_cc(data)
            elif event_type == 'apply_preset':
                return self._handle_modular_preset(data)
            elif event_type == 'preset_changed':
                controller = data.get('controller', 'Unknown')
                preset_id = data.get('new_preset', 0)
                preset_info = data.get('preset_info', {})
                print(f"🔄 {controller}: Preset → {preset_id} ({preset_info.get('name', 'Sin nombre')})")
                
        except Exception as e:
            print(f"❌ Error en callback de controlador: {e}")
    
    def _handle_modular_note(self, data: dict):
        """Manejar nota MIDI de controlador modular"""
        try:
            note_type = data.get('type')
            note = data.get('note')
            velocity = data.get('velocity')
            channel = data.get('channel', 0)
            controller = data.get('controller', 'Unknown')
            
            if self.fs:
                if note_type == 'note_on' and velocity > 0:
                    self.fs.noteon(channel, note, velocity)
                else:
                    self.fs.noteoff(channel, note)
                    
                print(f"🎵 {controller}: Nota {note} {'ON' if note_type == 'note_on' else 'OFF'} (canal {channel})")
                
        except Exception as e:
            print(f"❌ Error manejando nota modular: {e}")
    
    def _handle_modular_cc(self, data: dict):
        """Manejar Control Change de controlador modular"""
        try:
            cc_number = data.get('cc_number')
            value = data.get('value')
            channel = data.get('channel', 0)
            controller = data.get('controller', 'Unknown')
            
            if self.fs:
                self.fs.cc(channel, cc_number, value)
                print(f"🎛️ {controller}: CC{cc_number} = {value} (canal {channel})")
                
        except Exception as e:
            print(f"❌ Error manejando CC modular: {e}")
    
    def _handle_modular_preset(self, data: dict):
        """Manejar aplicación de preset modular"""
        try:
            channel = data.get('channel', 0)
            program = data.get('program', 0)
            bank = data.get('bank', 0)
            controller = data.get('controller', 'Unknown')
            
            if self.fs and self.sfid is not None:
                self.fs.program_select(channel, self.sfid, bank, program)
                print(f"🎛️ {controller}: Preset aplicado - Canal {channel}, Programa {program}")
                return True
                
            return False
            
        except Exception as e:
            print(f"❌ Error aplicando preset modular: {e}")
            return False
    
    def get_modular_status(self):
        """Obtener estado del sistema modular para la API"""
        try:
            status = {
                'modular_active': True,  # Sistema integrado siempre activo
                'controllers': {},
                'devices': {}
            }
            
            # Estado de controladores activos (sistema integrado)
            for name, controller in self.active_controllers.items():
                try:
                    device_info = controller.get('device_info', {})
                    status['controllers'][name] = {
                        'device_name': name,
                        'device_type': device_info.get('type', 'unknown'),
                        'is_active': controller.get('active', False),
                        'current_preset': controller.get('current_preset', 0),
                        'preset_range': f"{device_info.get('preset_start', 0)}-{device_info.get('preset_end', 7)}",
                        'midi_channel': device_info.get('midi_channel', 0),
                        'total_presets': len(controller.get('presets', {})),
                        'connected': device_info.get('connected', False)
                    }
                except Exception as e:
                    status['controllers'][name] = {'error': f'Error: {e}'}
            
            return status
            
        except Exception as e:
            print(f"❌ Error obteniendo estado modular: {e}")
            return {'error': str(e)}
    
    def start_device_monitoring(self):
        """Iniciar monitoreo automático de dispositivos MIDI"""
        try:
            if self.monitoring_active:
                return
            
            print("🔄 Iniciando monitoreo automático de dispositivos MIDI...")
            self.monitoring_active = True
            
            import threading
            self.device_monitor_thread = threading.Thread(
                target=self._device_monitor_loop,
                daemon=True
            )
            self.device_monitor_thread.start()
            
        except Exception as e:
            print(f"❌ Error iniciando monitoreo: {e}")
    
    def stop_device_monitoring(self):
        """Detener monitoreo automático de dispositivos MIDI"""
        try:
            if not self.monitoring_active:
                return
                
            print("⏹️ Deteniendo monitoreo de dispositivos MIDI...")
            self.monitoring_active = False
            
            if self.device_monitor_thread:
                self.device_monitor_thread.join(timeout=2)
                
        except Exception as e:
            print(f"❌ Error deteniendo monitoreo: {e}")
    
    def _device_monitor_loop(self):
        """Bucle de monitoreo de dispositivos MIDI en segundo plano"""
        try:
            while self.monitoring_active:
                try:
                    # Actualizar estado de controladores cada 5 segundos
                    self.get_connected_controllers()
                    
                    # Dormir un poco para no sobrecargar el sistema
                    import time
                    time.sleep(5)
                    
                except Exception as e:
                    print(f"⚠️  Error en monitoreo: {e}")
                    time.sleep(10)  # Esperar más tiempo si hay error
                    
        except Exception as e:
            print(f"❌ Error crítico en monitoreo: {e}")
        finally:
            print("🔄 Monitoreo de dispositivos MIDI terminado")

def optimize_system_for_low_latency():
    """Optimizar sistema operativo para baja latencia en actuaciones en vivo"""
    try:
        print("🚀 OPTIMIZANDO SISTEMA PARA BAJA LATENCIA...")
        
        # 1. Configurar prioridades de proceso
        try:
            import os
            # Configurar nice level para prioridad alta
            os.nice(-10)  # Prioridad alta (solo si se ejecuta como root)
            print("   ✅ Prioridad de proceso aumentada")
        except:
            print("   ⚠️  No se pudo aumentar prioridad (ejecutar como root para mejor rendimiento)")
        
        # 2. Configurar límites del sistema
        system_optimizations = [
            # Aumentar límite de memoria bloqueada
            ['ulimit', '-l', 'unlimited'],
            # Configurar scheduler para tiempo real
            ['echo', 'performance', '>', '/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor'],
            # Deshabilitar swap para evitar latencia
            ['swapoff', '-a'],
        ]
        
        for cmd in system_optimizations:
            try:
                import subprocess
                subprocess.run(cmd, shell=True, capture_output=True, timeout=2)
            except:
                pass
        
        # 3. Configurar JACK si está disponible (mejor que ALSA para latencia)
        try:
            jack_config = [
                'jackd', '-d', 'alsa', '-r', '22050', '-p', '64', '-n', '2'
            ]
            # Solo verificar si JACK está disponible, no iniciarlo
            result = subprocess.run(['which', 'jackd'], capture_output=True)
            if result.returncode == 0:
                print("   ✅ JACK disponible - considerar usar para latencia ultra-baja")
            else:
                print("   ⚠️  JACK no disponible - usando ALSA optimizado")
        except:
            pass
        
        print("🚀 OPTIMIZACIONES DE SISTEMA APLICADAS")
        
    except Exception as e:
        print(f"⚠️  Error en optimizaciones: {e}")

def main():
    """Función principal"""
    print("🎸 Guitar-MIDI Complete System v2.0 - ULTRA LOW LATENCY")
    print("Sistema 100% optimizado para actuaciones en vivo")
    print("-" * 50)
    
    # Aplicar optimizaciones del sistema
    optimize_system_for_low_latency()
    
    system = GuitarMIDIComplete()
    system.run()

if __name__ == "__main__":
    main()