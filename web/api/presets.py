"""
Presets API
Gestión de presets y configuraciones guardadas
"""

import json
import os
import time
from typing import Dict, List, Any

class PresetsAPI:
    def __init__(self):
        self.presets_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'presets')
        self.current_config_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'current_config.json')
        
        # Asegurar que el directorio existe
        os.makedirs(self.presets_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.current_config_file), exist_ok=True)
        
        # Crear preset por defecto si no existe
        self._create_default_preset()
    
    def get_all_presets(self) -> Dict[str, Any]:
        """Obtener lista de todos los presets disponibles"""
        presets = {}
        
        try:
            for filename in os.listdir(self.presets_dir):
                if filename.endswith('.json'):
                    preset_name = filename[:-5]  # Remover .json
                    preset_path = os.path.join(self.presets_dir, filename)
                    
                    try:
                        with open(preset_path, 'r') as f:
                            preset_data = json.load(f)
                            presets[preset_name] = {
                                'name': preset_name,
                                'description': preset_data.get('description', ''),
                                'created': preset_data.get('created', ''),
                                'modified': preset_data.get('modified', ''),
                                'instruments_count': len(preset_data.get('instruments', {}))
                            }
                    except Exception as e:
                        print(f"Error loading preset {preset_name}: {e}")
                        
        except Exception as e:
            print(f"Error reading presets directory: {e}")
        
        return presets
    
    def load_preset(self, preset_name: str) -> Dict[str, Any]:
        """Cargar un preset específico"""
        preset_path = os.path.join(self.presets_dir, f"{preset_name}.json")
        
        try:
            if os.path.exists(preset_path):
                with open(preset_path, 'r') as f:
                    preset_data = json.load(f)
                
                # Guardar como configuración actual
                self._save_current_config(preset_data)
                
                return {
                    'success': True,
                    'message': f'Preset "{preset_name}" loaded successfully',
                    'data': preset_data
                }
            else:
                return {
                    'success': False,
                    'error': f'Preset "{preset_name}" not found'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error loading preset: {str(e)}'
            }
    
    def save_preset(self, preset_name: str, config: Dict) -> Dict[str, Any]:
        """Guardar configuración actual como preset"""
        preset_path = os.path.join(self.presets_dir, f"{preset_name}.json")
        
        try:
            # Preparar datos del preset
            preset_data = {
                'name': preset_name,
                'description': config.get('description', f'Preset creado el {time.strftime("%Y-%m-%d %H:%M:%S")}'),
                'created': time.strftime('%Y-%m-%d %H:%M:%S'),
                'modified': time.strftime('%Y-%m-%d %H:%M:%S'),
                'instruments': config.get('instruments', {}),
                'effects': config.get('effects', {}),
                'current_instrument': config.get('current_instrument', 0)
            }
            
            # Si el preset ya existe, mantener fecha de creación
            if os.path.exists(preset_path):
                try:
                    with open(preset_path, 'r') as f:
                        existing_data = json.load(f)
                        preset_data['created'] = existing_data.get('created', preset_data['created'])
                except:
                    pass
            
            # Guardar preset
            with open(preset_path, 'w') as f:
                json.dump(preset_data, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'message': f'Preset "{preset_name}" saved successfully',
                'data': preset_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error saving preset: {str(e)}'
            }
    
    def delete_preset(self, preset_name: str) -> Dict[str, Any]:
        """Eliminar un preset"""
        if preset_name == 'default':
            return {
                'success': False,
                'error': 'Cannot delete default preset'
            }
        
        preset_path = os.path.join(self.presets_dir, f"{preset_name}.json")
        
        try:
            if os.path.exists(preset_path):
                os.remove(preset_path)
                return {
                    'success': True,
                    'message': f'Preset "{preset_name}" deleted successfully'
                }
            else:
                return {
                    'success': False,
                    'error': f'Preset "{preset_name}" not found'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error deleting preset: {str(e)}'
            }
    
    def export_preset(self, preset_name: str) -> Dict[str, Any]:
        """Exportar preset como JSON para backup"""
        preset_path = os.path.join(self.presets_dir, f"{preset_name}.json")
        
        try:
            if os.path.exists(preset_path):
                with open(preset_path, 'r') as f:
                    preset_data = json.load(f)
                
                return {
                    'success': True,
                    'data': preset_data
                }
            else:
                return {
                    'success': False,
                    'error': f'Preset "{preset_name}" not found'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error exporting preset: {str(e)}'
            }
    
    def import_preset(self, preset_name: str, preset_data: Dict) -> Dict[str, Any]:
        """Importar preset desde JSON"""
        try:
            # Validar datos del preset
            if not isinstance(preset_data, dict):
                return {
                    'success': False,
                    'error': 'Invalid preset data format'
                }
            
            # Actualizar metadatos
            preset_data['name'] = preset_name
            preset_data['modified'] = time.strftime('%Y-%m-%d %H:%M:%S')
            if 'created' not in preset_data:
                preset_data['created'] = preset_data['modified']
            
            # Guardar preset
            return self.save_preset(preset_name, preset_data)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error importing preset: {str(e)}'
            }
    
    def get_current_config(self) -> Dict[str, Any]:
        """Obtener configuración actual"""
        try:
            if os.path.exists(self.current_config_file):
                with open(self.current_config_file, 'r') as f:
                    return json.load(f)
            else:
                return self._get_default_config()
                
        except Exception as e:
            print(f"Error loading current config: {e}")
            return self._get_default_config()
    
    def _save_current_config(self, config: Dict):
        """Guardar configuración actual"""
        try:
            with open(self.current_config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving current config: {e}")
    
    def _create_default_preset(self):
        """Crear preset por defecto si no existe"""
        default_path = os.path.join(self.presets_dir, 'default.json')
        
        if not os.path.exists(default_path):
            default_config = self._get_default_config()
            self.save_preset('default', default_config)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Configuración por defecto del sistema"""
        return {
            'name': 'default',
            'description': 'Configuración por defecto del sistema',
            'current_instrument': 0,
            'current_preset': 'default',
            'instruments': {
                0: {"name": "Piano", "program": 0, "bank": 0, "volume": 80, "reverb": 50, "chorus": 30},
                1: {"name": "Drums", "program": 0, "bank": 128, "volume": 80, "reverb": 20, "chorus": 10},
                2: {"name": "Bass", "program": 32, "bank": 0, "volume": 85, "reverb": 30, "chorus": 20},
                3: {"name": "Guitar", "program": 24, "bank": 0, "volume": 75, "reverb": 60, "chorus": 40},
                4: {"name": "Saxophone", "program": 64, "bank": 0, "volume": 70, "reverb": 70, "chorus": 30},
                5: {"name": "Strings", "program": 48, "bank": 0, "volume": 65, "reverb": 80, "chorus": 50},
                6: {"name": "Organ", "program": 16, "bank": 0, "volume": 75, "reverb": 40, "chorus": 60},
                7: {"name": "Flute", "program": 73, "bank": 0, "volume": 70, "reverb": 70, "chorus": 20}
            },
            'effects': {
                'master_volume': 80,
                'global_reverb': 50,
                'global_chorus': 30
            }
        }