#!/usr/bin/env python3
"""
🎛️ InstrumentController - Clase base para controladores de instrumentos
Define la interfaz común para todos los controladores específicos
"""

import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstrumentController(ABC):
    """Clase base abstracta para todos los controladores de instrumentos"""
    
    def __init__(self, device_name: str, device_info: Dict[str, Any], main_system_callback: Callable = None):
        """
        Inicializar controlador de instrumento
        
        Args:
            device_name: Nombre del dispositivo
            device_info: Información del dispositivo del DeviceManager
            main_system_callback: Callback para comunicarse con el sistema principal
        """
        self.device_name = device_name
        self.device_info = device_info
        self.main_system = main_system_callback
        
        # Configuración básica
        self.device_type = device_info.get('type', 'unknown')
        self.midi_channel = device_info.get('midi_channel', 0)
        self.preset_start = device_info.get('preset_start', 0)
        self.preset_end = device_info.get('preset_end', 7)
        
        # Estado del controlador
        self.is_active = False
        self.current_preset = 0
        self.presets: Dict[int, Dict] = {}
        self.config: Dict[str, Any] = {}
        
        # Control de threads
        self.monitoring_thread = None
        self.is_monitoring = False
        
        # Base de datos
        self.db_path = "guitar_midi_devices.db"
        
        print(f"🎛️ Inicializando controlador: {self.device_name} ({self.device_type})")
        
        # Cargar configuración
        self.load_config()
        self.setup_presets()
    
    @abstractmethod
    def setup_presets(self):
        """Configurar presets específicos del controlador (debe ser implementado por subclases)"""
        pass
    
    @abstractmethod
    def handle_midi_message(self, message: List[int], delta_time: float):
        """Procesar mensaje MIDI recibido (debe ser implementado por subclases)"""
        pass
    
    def activate(self):
        """Activar el controlador"""
        try:
            print(f"▶️ Activando controlador: {self.device_name}")
            self.is_active = True
            
            # Iniciar monitoreo si es necesario
            if self.requires_monitoring():
                self.start_monitoring()
            
            # Configurar estado inicial
            self._setup_initial_state()
            
            # Notificar activación
            if self.main_system and callable(self.main_system):
                self.main_system('controller_activated', {
                    'name': self.device_name,
                    'type': self.device_type,
                    'presets': self.presets
                })
            
            print(f"✅ Controlador {self.device_name} activado")
            
        except Exception as e:
            logger.error(f"Error activando controlador {self.device_name}: {e}")
            self.is_active = False
    
    def deactivate(self):
        """Desactivar el controlador"""
        try:
            print(f"⏹️ Desactivando controlador: {self.device_name}")
            self.is_active = False
            
            # Detener monitoreo
            self.stop_monitoring()
            
            # Cleanup específico del controlador
            self._cleanup()
            
            # Notificar desactivación
            if self.main_system and callable(self.main_system):
                self.main_system('controller_deactivated', {
                    'name': self.device_name,
                    'type': self.device_type
                })
            
            print(f"✅ Controlador {self.device_name} desactivado")
            
        except Exception as e:
            logger.error(f"Error desactivando controlador {self.device_name}: {e}")
    
    def change_preset(self, preset_id: int) -> bool:
        """Cambiar a un preset específico"""
        try:
            if preset_id not in self.presets:
                logger.warning(f"Preset {preset_id} no existe en {self.device_name}")
                return False
            
            old_preset = self.current_preset
            self.current_preset = preset_id
            
            # Aplicar el preset
            success = self._apply_preset(preset_id)
            
            if success:
                print(f"🎛️ {self.device_name}: Preset {old_preset} → {preset_id} ({self.presets[preset_id].get('name', 'Sin nombre')})")
                
                # Notificar cambio
                if self.main_system and callable(self.main_system):
                    self.main_system('preset_changed', {
                        'controller': self.device_name,
                        'old_preset': old_preset,
                        'new_preset': preset_id,
                        'preset_info': self.presets[preset_id]
                    })
                
                return True
            else:
                # Revertir si falló
                self.current_preset = old_preset
                return False
                
        except Exception as e:
            logger.error(f"Error cambiando preset en {self.device_name}: {e}")
            return False
    
    def _apply_preset(self, preset_id: int) -> bool:
        """Aplicar preset al sintetizador (implementación por defecto)"""
        try:
            if not self.main_system:
                return False
            
            preset_info = self.presets[preset_id]
            
            # Enviar información del preset al sistema principal para aplicarlo
            return self.main_system('apply_preset', {
                'controller': self.device_name,
                'preset_id': preset_id,
                'channel': preset_info.get('channel', self.midi_channel),
                'program': preset_info.get('program', 0),
                'bank': preset_info.get('bank', 0)
            })
            
        except Exception as e:
            logger.error(f"Error aplicando preset {preset_id}: {e}")
            return False
    
    def save_config(self):
        """Guardar configuración del controlador en base de datos"""
        try:
            config_json = self._serialize_config()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Determinar si es MIDI o audio
                if hasattr(self, 'port_index'):  # Dispositivo MIDI
                    cursor.execute('''
                        UPDATE midi_devices 
                        SET config_json = ?, velocity_curve = ?, volume = ?, effects_enabled = ?
                        WHERE device_name = ?
                    ''', (
                        config_json,
                        self.config.get('velocity_curve', 'linear'),
                        self.config.get('volume', 100),
                        self.config.get('effects_enabled', True),
                        self.device_name
                    ))
                else:  # Dispositivo de audio
                    cursor.execute('''
                        UPDATE audio_devices 
                        SET config_json = ?, audio_to_midi_enabled = ?, sensitivity = ?
                        WHERE device_name = ?
                    ''', (
                        config_json,
                        self.config.get('audio_to_midi_enabled', False),
                        self.config.get('sensitivity', 0.5),
                        self.device_name
                    ))
                
                conn.commit()
                print(f"💾 Configuración guardada para {self.device_name}")
                
        except Exception as e:
            logger.error(f"Error guardando configuración de {self.device_name}: {e}")
    
    def load_config(self):
        """Cargar configuración del controlador desde base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Intentar cargar como dispositivo MIDI primero
                cursor.execute('''
                    SELECT config_json, velocity_curve, volume, effects_enabled
                    FROM midi_devices 
                    WHERE device_name = ?
                ''', (self.device_name,))
                
                row = cursor.fetchone()
                
                if not row:
                    # Intentar cargar como dispositivo de audio
                    cursor.execute('''
                        SELECT config_json, audio_to_midi_enabled, sensitivity
                        FROM audio_devices 
                        WHERE device_name = ?
                    ''', (self.device_name,))
                    
                    row = cursor.fetchone()
                    
                    if row:
                        config_json, audio_to_midi, sensitivity = row
                        self.config.update({
                            'audio_to_midi_enabled': bool(audio_to_midi),
                            'sensitivity': float(sensitivity) if sensitivity else 0.5
                        })
                else:
                    config_json, velocity_curve, volume, effects_enabled = row
                    self.config.update({
                        'velocity_curve': velocity_curve or 'linear',
                        'volume': int(volume) if volume else 100,
                        'effects_enabled': bool(effects_enabled)
                    })
                
                # Deserializar configuración adicional si existe
                if row and row[0]:  # config_json
                    additional_config = self._deserialize_config(row[0])
                    self.config.update(additional_config)
                
                print(f"📂 Configuración cargada para {self.device_name}")
                
        except Exception as e:
            logger.error(f"Error cargando configuración de {self.device_name}: {e}")
            # Configuración por defecto
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Obtener configuración por defecto"""
        return {
            'velocity_curve': 'linear',
            'volume': 100,
            'effects_enabled': True,
            'audio_to_midi_enabled': False,
            'sensitivity': 0.5,
            'custom_settings': {}
        }
    
    def _serialize_config(self) -> str:
        """Serializar configuración personalizada a JSON"""
        import json
        try:
            # Solo serializar configuraciones personalizadas
            custom_config = {
                k: v for k, v in self.config.items() 
                if k not in ['velocity_curve', 'volume', 'effects_enabled', 'audio_to_midi_enabled', 'sensitivity']
            }
            return json.dumps(custom_config)
        except Exception as e:
            logger.error(f"Error serializando configuración: {e}")
            return "{}"
    
    def _deserialize_config(self, config_json: str) -> Dict[str, Any]:
        """Deserializar configuración desde JSON"""
        import json
        try:
            return json.loads(config_json) if config_json else {}
        except Exception as e:
            logger.error(f"Error deserializando configuración: {e}")
            return {}
    
    def requires_monitoring(self) -> bool:
        """Determinar si el controlador requiere monitoreo activo (por defecto no)"""
        return False
    
    def start_monitoring(self):
        """Iniciar monitoreo del controlador (implementación por defecto)"""
        if self.is_monitoring or not self.requires_monitoring():
            return
        
        print(f"👁️ Iniciando monitoreo para {self.device_name}")
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Detener monitoreo del controlador"""
        if not self.is_monitoring:
            return
        
        print(f"🛑 Deteniendo monitoreo para {self.device_name}")
        self.is_monitoring = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2)
    
    def _monitoring_loop(self):
        """Loop de monitoreo del controlador (implementación por defecto)"""
        while self.is_monitoring and self.is_active:
            try:
                self._monitor_step()
                time.sleep(0.1)  # 100ms entre checks
                
            except Exception as e:
                logger.error(f"Error en loop de monitoreo de {self.device_name}: {e}")
                time.sleep(1)  # Esperar más tiempo si hay error
    
    def _monitor_step(self):
        """Un paso del monitoreo (implementación por defecto - no hace nada)"""
        pass
    
    def _setup_initial_state(self):
        """Configurar estado inicial del controlador (implementación por defecto)"""
        # Aplicar preset inicial
        if self.presets and self.current_preset in self.presets:
            self._apply_preset(self.current_preset)
    
    def _cleanup(self):
        """Limpieza específica del controlador (implementación por defecto - no hace nada)"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado actual del controlador"""
        return {
            'device_name': self.device_name,
            'device_type': self.device_type,
            'is_active': self.is_active,
            'is_monitoring': self.is_monitoring,
            'current_preset': self.current_preset,
            'preset_range': f"{self.preset_start}-{self.preset_end}",
            'midi_channel': self.midi_channel,
            'total_presets': len(self.presets),
            'config': self.config.copy()
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """Actualizar configuración del controlador"""
        try:
            self.config.update(new_config)
            self.save_config()
            
            # Notificar cambio de configuración
            if self.main_system and callable(self.main_system):
                self.main_system('controller_config_updated', {
                    'controller': self.device_name,
                    'config': self.config.copy()
                })
            
            print(f"⚙️ Configuración actualizada para {self.device_name}")
            
        except Exception as e:
            logger.error(f"Error actualizando configuración de {self.device_name}: {e}")
    
    def add_custom_preset(self, preset_id: int, preset_info: Dict[str, Any]) -> bool:
        """Añadir preset personalizado"""
        try:
            if preset_id < self.preset_start or preset_id > self.preset_end:
                logger.warning(f"Preset ID {preset_id} fuera del rango permitido ({self.preset_start}-{self.preset_end})")
                return False
            
            self.presets[preset_id] = preset_info
            
            # Guardar en base de datos
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO device_presets 
                    (device_name, preset_id, preset_name, program, bank, midi_channel, icon)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.device_name,
                    preset_id,
                    preset_info.get('name', f'Preset {preset_id}'),
                    preset_info.get('program', 0),
                    preset_info.get('bank', 0),
                    preset_info.get('channel', self.midi_channel),
                    preset_info.get('icon', '🎵')
                ))
                
                conn.commit()
            
            print(f"➕ Preset personalizado añadido: {self.device_name} - Preset {preset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error añadiendo preset personalizado: {e}")
            return False