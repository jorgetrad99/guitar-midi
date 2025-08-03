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
        
        # Base de datos SQLite integrada
        self.db_path = "guitar_midi.db"
        self._init_database()
        
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
        
        # Componentes del sistema
        self.fs = None  # FluidSynth
        self.sfid = None  # SoundFont ID
        self.app = None  # Flask App
        self.socketio = None  # SocketIO
        self.audio_device = None  # Dispositivo de audio detectado
        self.instrument_extractor = None  # FluidSynth instrument extractor
        self._instrument_library_cache = None  # Cache for instrument library
        
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
    
    def _auto_detect_audio(self) -> bool:
        """Auto-detectar dispositivo de audio que funciona"""
        print("🔊 Auto-detectando audio...")
        
        # Configuraciones a probar (Raspberry Pi)
        audio_configs = [
            ("hw:0,0", "Jack 3.5mm", 1),
            ("hw:0,1", "HDMI", 2),
            ("hw:1,0", "USB", None)
        ]
        
        for device, description, raspi_config in audio_configs:
            print(f"   Probando: {description} ({device})")
            
            # Configurar raspi-config si es necesario
            if raspi_config:
                try:
                    subprocess.run(['sudo', 'raspi-config', 'nonint', 'do_audio', str(raspi_config)], 
                                 check=True, capture_output=True, timeout=10)
                    time.sleep(1)
                except:
                    pass
            
            # Test del dispositivo
            try:
                result = subprocess.run(['speaker-test', '-D', device, '-t', 'sine', '-f', '440', '-c', '2'], 
                                      timeout=2, capture_output=True)
                if result.returncode == 0:
                    print(f"   ✅ Audio detectado: {description}")
                    self.audio_device = device
                    self._configure_alsa()
                    return True
                else:
                    print(f"   ❌ No funciona: {description}")
            except:
                print(f"   ❌ Error probando: {description}")
        
        print("   ⚠️  No se detectó audio funcionando")
        self.audio_device = "hw:0,0"  # Fallback
        return False
    
    def _configure_alsa(self):
        """Configurar ALSA con volúmenes óptimos"""
        try:
            subprocess.run(['amixer', 'set', 'PCM', '100%'], capture_output=True)
            subprocess.run(['amixer', 'set', 'Master', '100%'], capture_output=True)
            subprocess.run(['amixer', 'cset', 'numid=1', '100%'], capture_output=True)
            print("   ✅ ALSA configurado")
        except Exception as e:
            print(f"   ⚠️  Error configurando ALSA: {e}")
    
    def _init_fluidsynth(self) -> bool:
        """Inicializar FluidSynth con configuración automática"""
        try:
            print("🎹 Inicializando FluidSynth...")
            self.fs = fluidsynth.Synth()
            
            # Configuración optimizada para Raspberry Pi
            self.fs.setting('audio.driver', 'alsa')
            self.fs.setting('audio.alsa.device', self.audio_device or 'hw:0,0')
            self.fs.setting('synth.gain', 1.0)
            self.fs.setting('audio.periods', 2)
            """ self.fs.setting('audio.sample_rate', 44100)
            self.fs.setting('synth.cpu_cores', 4) """
            
            self.fs.start()
            
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
            
            # Conectar cada dispositivo MIDI a FluidSynth
            connected_devices = []
            for client_num, device_name in midi_inputs:
                try:
                    cmd = ['aconnect', f'{client_num}:0', f'{fluidsynth_port}:0']
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        connected_devices.append(device_name)
                        print(f"   ✅ Conectado: {device_name} -> FluidSynth")
                    else:
                        print(f"   ⚠️  No se pudo conectar: {device_name}")
                except Exception as e:
                    print(f"   ❌ Error conectando {device_name}: {e}")
            
            if connected_devices:
                print(f"   🎹 Auto-conectados {len(connected_devices)} dispositivos MIDI")
            else:
                print("   ⚠️  No se conectaron dispositivos MIDI automáticamente")
                
        except Exception as e:
            print(f"❌ Error en auto-conexión MIDI: {e}")
    
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
        """Callback para mensajes MIDI entrantes"""
        msg, delta_time = message
        
        if len(msg) >= 2:
            status = msg[0]
            
            # Program Change (0xC0-0xCF)
            if 0xC0 <= status <= 0xCF:
                pc_number = msg[1]
                if 0 <= pc_number <= 7:
                    self._set_instrument(pc_number)
                    # Notificar a clientes web
                    if self.socketio:
                        self.socketio.emit('instrument_changed', {
                            'pc': pc_number,
                            'name': self.presets[pc_number]['name']
                        })
    
    def _set_instrument(self, pc: int) -> bool:
        """Cambiar instrumento activo usando presets"""
        try:
            if pc not in self.presets:
                return False
            
            instrument = self.presets[pc]
            
            if self.fs and self.sfid is not None:
                channel = instrument['channel']
                bank = instrument['bank']
                program = instrument['program']
                
                self.fs.program_select(channel, self.sfid, bank, program)
                self.current_instrument = pc
                
                # Guardar en base de datos
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', 
                                 ('current_instrument', str(pc)))
                    conn.commit()
                
                print(f"🎹 Instrumento: {instrument['name']} (PC: {pc})")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error cambiando instrumento: {e}")
            return False
    
    def _set_effect(self, effect_name: str, value: int) -> bool:
        """Aplicar efecto global"""
        try:
            if self.fs:
                if effect_name == 'master_volume':
                    # Volumen master
                    gain = (value / 100.0) * 2.0
                    self.fs.setting('synth.gain', gain)
                    
                elif effect_name == 'global_reverb':
                    # Reverb global en todos los canales
                    reverb_value = int((value / 100.0) * 127)
                    for channel in range(16):
                        self.fs.cc(channel, 91, reverb_value)  # CC 91 = Reverb
                    
                elif effect_name == 'global_chorus':
                    # Chorus global en todos los canales
                    chorus_value = int((value / 100.0) * 127)
                    for channel in range(16):
                        self.fs.cc(channel, 93, chorus_value)  # CC 93 = Chorus
                        
                elif effect_name == 'global_cutoff':
                    # Filtro de corte global
                    cutoff_value = int((value / 100.0) * 127)
                    for channel in range(16):
                        self.fs.cc(channel, 74, cutoff_value)  # CC 74 = Cutoff
                        
                elif effect_name == 'global_resonance':
                    # Resonancia global
                    resonance_value = int((value / 100.0) * 127)
                    for channel in range(16):
                        self.fs.cc(channel, 71, resonance_value)  # CC 71 = Resonance
            
            self.effects[effect_name] = value
            
            # Guardar en base de datos
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)', 
                             (effect_name, str(value)))
                conn.commit()
            
            print(f"🎹 {effect_name}: {value}%")
            return True
            
        except Exception as e:
            print(f"❌ Error aplicando efecto: {e}")
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
            
            # 6. Iniciar monitoreo MIDI en hilo separado
            midi_monitor_thread = threading.Thread(target=self._monitor_midi_connections, daemon=True)
            midi_monitor_thread.start()
            
            # 7. Mostrar información del sistema
            self._show_system_info()
            
            # 8. Ejecutar servidor (bloqueante)
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

def main():
    """Función principal"""
    print("🎸 Guitar-MIDI Complete System v2.0")
    print("Sistema 100% unificado - UN SOLO ARCHIVO")
    print("-" * 50)
    
    system = GuitarMIDIComplete()
    system.run()

if __name__ == "__main__":
    main()