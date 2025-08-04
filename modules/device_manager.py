#!/usr/bin/env python3
"""
🔌 DeviceManager - Detección automática de dispositivos MIDI y Audio
Maneja la detección, inicialización y asignación dinámica de dispositivos
"""

import time
import threading
import re
import sqlite3
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import logging

try:
    import rtmidi
    import sounddevice as sd
    import numpy as np
except ImportError as e:
    print(f"❌ Error importando dependencias: {e}")
    print("💡 Instalar con: pip install python-rtmidi sounddevice numpy")

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeviceManager:
    """Administrador central de dispositivos MIDI y audio"""
    
    def __init__(self, main_system_callback: Callable = None):
        """
        Inicializar el administrador de dispositivos
        
        Args:
            main_system_callback: Callback para notificar al sistema principal
        """
        print("🔌 Inicializando DeviceManager...")
        
        self.main_system = main_system_callback
        self.is_running = False
        self.scan_thread = None
        
        # Dispositivos detectados
        self.midi_devices: Dict[str, Dict] = {}
        self.audio_devices: Dict[str, Dict] = {}
        self.registered_controllers: Dict[str, Any] = {}
        
        # Asignación dinámica de presets
        self.preset_ranges: Dict[str, Dict[str, int]] = {}
        self.next_preset_start = 0
        self.preset_block_size = 8  # 8 presets por dispositivo
        
        # Patrones de detección de dispositivos
        self.device_patterns = {
            'midi': {
                'akai_mpk_mini': [
                    r'.*MPK.*Mini.*', r'.*Akai.*MPK.*', r'MPK.*Mini.*',
                    r'.*AKAI.*MPK.*', r'Akai Professional MPK mini 3'
                ],
                'fishman_tripleplay': [
                    r'.*Fishman.*Triple.*', r'.*TriplePlay.*', r'.*Fishman.*',
                    r'TriplePlay.*', r'Fishman TriplePlay'
                ],
                'midi_captain': [
                    r'.*Captain.*', r'.*MIDI.*Captain.*', r'Pico.*Captain.*',
                    r'Captain.*MIDI.*', r'MIDI Captain'
                ],
                'mvave_pocket': [
                    r'.*MVAVE.*Pocket.*', r'.*Pocket.*MVAVE.*', r'MVAVE.*'
                ],
                'hexaphonic': [
                    r'.*HEX.*', r'.*Hexaphonic.*', r'.*Guitar.*Synth.*', 
                    r'.*Hexaphonic.*'
                ],
                'generic_midi': [
                    r'.*MIDI.*', r'.*USB.*MIDI.*', r'.*Digital.*Piano.*'
                ]
            },
            'audio': {
                'behringer_umc22': [
                    r'.*Behringer.*UMC22.*', r'.*UMC22.*', r'.*Behringer.*UMC.*',
                    r'UMC22.*', r'Behringer UMC22'
                ],
                'behringer_generic': [
                    r'.*Behringer.*', r'.*UMC.*', r'.*U-PHORIA.*'
                ],
                'scarlett': [
                    r'.*Scarlett.*', r'.*Focusrite.*'
                ],
                'generic_audio': [
                    r'.*USB.*Audio.*', r'.*Audio.*Interface.*', r'.*Line.*'
                ]
            }
        }
        
        # Base de datos
        self.db_path = "guitar_midi_devices.db"
        self._init_device_database()
        
        print("✅ DeviceManager inicializado")
    
    def _init_device_database(self):
        """Inicializar base de datos de dispositivos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabla de dispositivos MIDI
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS midi_devices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_name TEXT UNIQUE NOT NULL,
                        device_type TEXT NOT NULL,
                        client_id TEXT,
                        preset_start INTEGER,
                        preset_end INTEGER,
                        midi_channel INTEGER,
                        velocity_curve TEXT DEFAULT 'linear',
                        volume INTEGER DEFAULT 100,
                        effects_enabled BOOLEAN DEFAULT 1,
                        last_connected TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        config_json TEXT
                    )
                ''')
                
                # Tabla de dispositivos de audio
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audio_devices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_name TEXT UNIQUE NOT NULL,
                        device_type TEXT NOT NULL,
                        device_index INTEGER,
                        sample_rate INTEGER DEFAULT 44100,
                        channels INTEGER DEFAULT 2,
                        audio_to_midi_enabled BOOLEAN DEFAULT 0,
                        midi_channel INTEGER,
                        sensitivity REAL DEFAULT 0.5,
                        last_connected TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        config_json TEXT
                    )
                ''')
                
                # Tabla de presets por dispositivo
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS device_presets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_name TEXT NOT NULL,
                        preset_id INTEGER NOT NULL,
                        preset_name TEXT NOT NULL,
                        program INTEGER NOT NULL,
                        bank INTEGER DEFAULT 0,
                        midi_channel INTEGER NOT NULL,
                        icon TEXT DEFAULT '🎵',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(device_name, preset_id)
                    )
                ''')
                
                conn.commit()
                print("✅ Base de datos de dispositivos inicializada")
                
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")
    
    def start_monitoring(self):
        """Iniciar monitoreo automático de dispositivos"""
        if self.is_running:
            return
            
        print("🔍 Iniciando monitoreo de dispositivos...")
        self.is_running = True
        
        # Escaneo inicial
        self._scan_devices()
        
        # Hilo de monitoreo continuo
        self.scan_thread = threading.Thread(target=self._monitor_devices_loop, daemon=True)
        self.scan_thread.start()
        
        print("✅ Monitoreo de dispositivos iniciado")
    
    def stop_monitoring(self):
        """Detener monitoreo de dispositivos"""
        print("🛑 Deteniendo monitoreo de dispositivos...")
        self.is_running = False
        
        if self.scan_thread and self.scan_thread.is_alive():
            self.scan_thread.join(timeout=2)
        
        print("✅ Monitoreo detenido")
    
    def _monitor_devices_loop(self):
        """Loop principal de monitoreo"""
        while self.is_running:
            try:
                time.sleep(5)  # Escanear cada 5 segundos
                self._scan_devices()
                
            except Exception as e:
                logger.error(f"Error en loop de monitoreo: {e}")
                time.sleep(10)  # Esperar más tiempo si hay error
    
    def _scan_devices(self):
        """Escanear dispositivos MIDI y audio disponibles"""
        try:
            # Escanear dispositivos MIDI
            self._scan_midi_devices()
            
            # Escanear dispositivos de audio
            self._scan_audio_devices()
            
        except Exception as e:
            logger.error(f"Error escaneando dispositivos: {e}")
    
    def _scan_midi_devices(self):
        """Escanear dispositivos MIDI"""
        try:
            # Crear instancia temporal para escanear
            midiin = rtmidi.MidiIn()
            available_ports = midiin.get_ports()
            
            current_devices = set()
            
            for i, port_name in enumerate(available_ports):
                current_devices.add(port_name)
                
                # Si ya está registrado, continuar
                if port_name in self.midi_devices:
                    continue
                
                # Detectar tipo de dispositivo
                device_type = self._detect_midi_device_type(port_name)
                
                if device_type:
                    print(f"🎛️ Nuevo dispositivo MIDI detectado: {port_name} ({device_type})")
                    
                    # Registrar dispositivo
                    device_info = self._register_midi_device(port_name, device_type, i)
                    
                    # Notificar al sistema principal
                    if self.main_system and callable(self.main_system):
                        self.main_system('midi_device_connected', device_info)
            
            # Detectar dispositivos desconectados
            disconnected = set(self.midi_devices.keys()) - current_devices
            for device_name in disconnected:
                print(f"🔌 Dispositivo MIDI desconectado: {device_name}")
                device_info = self.midi_devices.pop(device_name, None)
                
                if self.main_system and callable(self.main_system):
                    self.main_system('midi_device_disconnected', device_info)
            
            midiin.close_port()
            
        except Exception as e:
            logger.error(f"Error escaneando dispositivos MIDI: {e}")
    
    def _scan_audio_devices(self):
        """Escanear dispositivos de audio"""
        try:
            devices = sd.query_devices()
            
            current_devices = set()
            
            for i, device in enumerate(devices):
                device_name = device['name']
                current_devices.add(device_name)
                
                # Solo procesar dispositivos de entrada con más de 0 canales
                if device['max_input_channels'] == 0:
                    continue
                
                # Si ya está registrado, continuar
                if device_name in self.audio_devices:
                    continue
                
                # Detectar tipo de dispositivo de audio
                device_type = self._detect_audio_device_type(device_name)
                
                if device_type and device_type != 'generic_audio':  # Solo registrar dispositivos específicos
                    print(f"🎤 Nuevo dispositivo de audio detectado: {device_name} ({device_type})")
                    
                    # Registrar dispositivo
                    device_info = self._register_audio_device(device_name, device_type, i, device)
                    
                    # Notificar al sistema principal
                    if self.main_system and callable(self.main_system):
                        self.main_system('audio_device_connected', device_info)
            
            # Detectar dispositivos de audio desconectados
            disconnected = set(self.audio_devices.keys()) - current_devices
            for device_name in disconnected:
                print(f"🔌 Dispositivo de audio desconectado: {device_name}")
                device_info = self.audio_devices.pop(device_name, None)
                
                if self.main_system and callable(self.main_system):
                    self.main_system('audio_device_disconnected', device_info)
            
        except Exception as e:
            logger.error(f"Error escaneando dispositivos de audio: {e}")
    
    def _detect_midi_device_type(self, device_name: str) -> Optional[str]:
        """Detectar tipo de dispositivo MIDI por nombre"""
        patterns = self.device_patterns['midi']
        
        for device_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, device_name, re.IGNORECASE):
                    return device_type
        
        return None
    
    def _detect_audio_device_type(self, device_name: str) -> Optional[str]:
        """Detectar tipo de dispositivo de audio por nombre"""
        patterns = self.device_patterns['audio']
        
        for device_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, device_name, re.IGNORECASE):
                    return device_type
        
        return None
    
    def _register_midi_device(self, device_name: str, device_type: str, port_index: int) -> Dict:
        """Registrar nuevo dispositivo MIDI"""
        try:
            # Asignar rango de presets
            preset_start = self.next_preset_start
            preset_end = preset_start + self.preset_block_size - 1
            self.next_preset_start += self.preset_block_size
            
            # Asignar canal MIDI (rotar entre 0-15, evitando canal 9 que es percusión)
            midi_channel = len(self.midi_devices) % 16
            if midi_channel == 9:  # Canal 9 es percusión estándar
                midi_channel = (midi_channel + 1) % 16
            
            device_info = {
                'name': device_name,
                'type': device_type,
                'port_index': port_index,
                'preset_start': preset_start,
                'preset_end': preset_end,
                'midi_channel': midi_channel,
                'connected': True,
                'last_connected': datetime.now().isoformat(),
                'controller': None  # Se asignará cuando se cree el controlador
            }
            
            self.midi_devices[device_name] = device_info
            
            # Guardar en base de datos
            self._save_midi_device_to_db(device_info)
            
            # Crear presets por defecto
            self._create_default_presets(device_name, device_type, preset_start, preset_end, midi_channel)
            
            return device_info
            
        except Exception as e:
            logger.error(f"Error registrando dispositivo MIDI {device_name}: {e}")
            return {}
    
    def _register_audio_device(self, device_name: str, device_type: str, device_index: int, device_info_sd: Dict) -> Dict:
        """Registrar nuevo dispositivo de audio"""
        try:
            # Asignar canal MIDI para audio-to-MIDI
            midi_channel = (len(self.audio_devices) + 10) % 16  # Empezar desde canal 10
            if midi_channel == 9:  # Evitar canal 9 (percusión)
                midi_channel = (midi_channel + 1) % 16
            
            device_info = {
                'name': device_name,
                'type': device_type,
                'device_index': device_index,
                'sample_rate': int(device_info_sd.get('default_samplerate', 44100)),
                'max_input_channels': device_info_sd.get('max_input_channels', 2),
                'midi_channel': midi_channel,
                'audio_to_midi_enabled': False,  # Deshabilitado por defecto
                'connected': True,
                'last_connected': datetime.now().isoformat(),
                'controller': None  # Se asignará cuando se cree el controlador
            }
            
            self.audio_devices[device_name] = device_info
            
            # Guardar en base de datos
            self._save_audio_device_to_db(device_info)
            
            return device_info
            
        except Exception as e:
            logger.error(f"Error registrando dispositivo de audio {device_name}: {e}")
            return {}
    
    def _save_midi_device_to_db(self, device_info: Dict):
        """Guardar dispositivo MIDI en base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO midi_devices 
                    (device_name, device_type, preset_start, preset_end, midi_channel, last_connected)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    device_info['name'],
                    device_info['type'],
                    device_info['preset_start'],
                    device_info['preset_end'],
                    device_info['midi_channel'],
                    device_info['last_connected']
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error guardando dispositivo MIDI en DB: {e}")
    
    def _save_audio_device_to_db(self, device_info: Dict):
        """Guardar dispositivo de audio en base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO audio_devices 
                    (device_name, device_type, device_index, sample_rate, channels, midi_channel, last_connected)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    device_info['name'],
                    device_info['type'],
                    device_info['device_index'],
                    device_info['sample_rate'],
                    device_info['max_input_channels'],
                    device_info['midi_channel'],
                    device_info['last_connected']
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error guardando dispositivo de audio en DB: {e}")
    
    def _create_default_presets(self, device_name: str, device_type: str, preset_start: int, preset_end: int, midi_channel: int):
        """Crear presets por defecto para el dispositivo"""
        try:
            # Presets por defecto según tipo de dispositivo
            default_presets = self._get_default_presets_for_device_type(device_type)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for i, (preset_name, program, icon) in enumerate(default_presets):
                    if i >= self.preset_block_size:  # No exceder el límite
                        break
                        
                    preset_id = preset_start + i
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO device_presets 
                        (device_name, preset_id, preset_name, program, midi_channel, icon)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (device_name, preset_id, preset_name, program, midi_channel, icon))
                
                conn.commit()
                print(f"   ✅ Presets por defecto creados para {device_name}")
                
        except Exception as e:
            logger.error(f"Error creando presets por defecto: {e}")
    
    def _get_default_presets_for_device_type(self, device_type: str) -> List[tuple]:
        """Obtener presets por defecto según el tipo de dispositivo"""
        presets_map = {
            'akai_mpk_mini': [
                ("Grand Piano", 0, "🎹"),
                ("Electric Piano", 4, "🎹"),
                ("Organ", 16, "🎹"),
                ("Synth Lead", 80, "🎛️"),
                ("Synth Strings", 50, "🎻"),
                ("Choir", 52, "👥"),
                ("Bass", 32, "🎸"),
                ("Drums", 128, "🥁")  # Programa especial para percusión
            ],
            'fishman_tripleplay': [
                ("Acoustic Guitar", 24, "🎸"),
                ("Electric Guitar", 27, "🎸"),
                ("Distortion Guitar", 30, "🎸"),
                ("Guitar Harmonics", 31, "🎸"),
                ("Synth Guitar", 29, "🎸"),
                ("Bass Guitar", 33, "🎸"),
                ("Violin", 40, "🎻"),
                ("Cello", 42, "🎻")
            ],
            'midi_captain': [
                ("Master Control 1", 0, "🎚️"),
                ("Master Control 2", 1, "🎚️"),
                ("Master Control 3", 2, "🎚️"),
                ("Master Control 4", 3, "🎚️"),
                ("Master Control 5", 4, "🎚️"),
                ("Master Control 6", 5, "🎚️"),
                ("Master Control 7", 6, "🎚️"),
                ("Master Control 8", 7, "🎚️")
            ],
            'mvave_pocket': [
                ("Standard Kit", 0, "🥁"),
                ("Rock Kit", 8, "🥁"),
                ("Electronic Kit", 25, "🥁"),
                ("Jazz Kit", 32, "🥁"),
                ("Brush Kit", 40, "🥁"),
                ("Power Kit", 16, "🥁"),
                ("TR-808 Kit", 26, "🥁"),
                ("Dance Kit", 27, "🥁")
            ],
            'hexaphonic': [
                ("String 1 - Bass", 32, "🎸"),
                ("String 2 - Piano", 0, "🎹"),
                ("String 3 - Synth", 80, "🎛️"),
                ("String 4 - Strings", 48, "🎻"),
                ("String 5 - Brass", 56, "🎺"),
                ("String 6 - Lead", 81, "🎛️"),
                ("Poly Mode", 40, "🎻"),
                ("Chord Mode", 0, "🎹")
            ]
        }
        
        return presets_map.get(device_type, [
            ("Preset 1", 0, "🎵"),
            ("Preset 2", 1, "🎵"),
            ("Preset 3", 2, "🎵"),
            ("Preset 4", 3, "🎵"),
            ("Preset 5", 4, "🎵"),
            ("Preset 6", 5, "🎵"),
            ("Preset 7", 6, "🎵"),
            ("Preset 8", 7, "🎵")
        ])
    
    def get_device_presets(self, device_name: str) -> List[Dict]:
        """Obtener presets de un dispositivo específico"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT preset_id, preset_name, program, bank, midi_channel, icon
                    FROM device_presets 
                    WHERE device_name = ?
                    ORDER BY preset_id
                ''', (device_name,))
                
                presets = []
                for row in cursor.fetchall():
                    presets.append({
                        'preset_id': row[0],
                        'name': row[1],
                        'program': row[2],
                        'bank': row[3],
                        'channel': row[4],
                        'icon': row[5]
                    })
                
                return presets
                
        except Exception as e:
            logger.error(f"Error obteniendo presets de {device_name}: {e}")
            return []
    
    def get_all_registered_devices(self) -> Dict[str, Any]:
        """Obtener todos los dispositivos registrados"""
        return {
            'midi_devices': self.midi_devices,
            'audio_devices': self.audio_devices,
            'total_devices': len(self.midi_devices) + len(self.audio_devices)
        }
    
    def enable_audio_to_midi(self, device_name: str, enabled: bool = True) -> bool:
        """Habilitar/deshabilitar conversión audio-to-MIDI para un dispositivo"""
        try:
            if device_name in self.audio_devices:
                self.audio_devices[device_name]['audio_to_midi_enabled'] = enabled
                
                # Actualizar en base de datos
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE audio_devices 
                        SET audio_to_midi_enabled = ?
                        WHERE device_name = ?
                    ''', (enabled, device_name))
                    conn.commit()
                
                print(f"🎤 Audio-to-MIDI {'habilitado' if enabled else 'deshabilitado'} para {device_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error configurando audio-to-MIDI: {e}")
            return False