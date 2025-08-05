"""
API Routes for Guitar-MIDI Complete System
Handles all web API endpoints
"""

from flask import Blueprint, jsonify, request
import time

api = Blueprint('api', __name__, url_prefix='/api')

def init_api(guitar_midi_system):
    """Initialize API with reference to main system"""
    api.guitar_midi = guitar_midi_system
    return api

@api.route('/system/status', methods=['GET'])
def system_status():
    """Get current system status"""
    return jsonify({
        'success': True,
        'current_instrument': api.guitar_midi.current_instrument,
        'presets': api.guitar_midi.presets,
        'effects': api.guitar_midi.effects,
        'audio_device': api.guitar_midi.audio_device,
        'timestamp': time.time()
    })

@api.route('/system/panic', methods=['POST'])
def panic():
    """Emergency stop - silence all audio"""
    success = api.guitar_midi._panic()
    return jsonify({'success': success})

@api.route('/presets', methods=['GET'])
def get_presets():
    """Get all configured presets"""
    return jsonify({
        'success': True, 
        'presets': api.guitar_midi.presets
    })

@api.route('/presets/<int:preset_id>', methods=['PUT'])
def update_preset(preset_id):
    """Update a specific preset configuration"""
    if not (0 <= preset_id <= 7):
        return jsonify({'success': False, 'error': 'Invalid preset ID'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    # Validate required fields
    required_fields = ['name', 'program', 'bank', 'channel', 'icon']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    # Update preset
    api.guitar_midi.presets[preset_id] = {
        'name': data['name'],
        'program': int(data['program']),
        'bank': int(data['bank']),
        'channel': int(data['channel']),
        'icon': data['icon']
    }
    
    # Save to database
    api.guitar_midi._save_preset_to_db(preset_id, api.guitar_midi.presets[preset_id])
    
    return jsonify({
        'success': True, 
        'preset': api.guitar_midi.presets[preset_id]
    })

@api.route('/instruments/<int:pc>/activate', methods=['POST'])
def activate_instrument(pc):
    """Activate a specific preset/instrument using MIDI Program Change simulation"""
    print(f"🎹 API: Activando instrumento {pc} usando simulación MIDI")
    print(f"   Presets disponibles: {list(api.guitar_midi.presets.keys())}")
    if pc in api.guitar_midi.presets:
        preset_info = api.guitar_midi.presets[pc]
        print(f"   Preset {pc} info: {preset_info}")
    else:
        print(f"   ❌ Preset {pc} NO EXISTE en presets")
        return jsonify({
            'success': False, 
            'error': f'Preset {pc} no existe'
        }), 404
    
    # 🎯 USAR EXACTAMENTE LA MISMA FUNCIÓN QUE EL MIDI CAPTAIN
    print(f"   🎯 Usando función universal (mismo código que MIDI Captain)")
    success = api.guitar_midi._change_preset_universal(pc, "Web_Interface")
    print(f"   Resultado función universal: {'✅ Éxito' if success else '❌ Error'}")
    
    return jsonify({
        'success': success, 
        'current_instrument': pc if success else None
    })

@api.route('/effects', methods=['POST'])
def update_effects():
    """Update effect parameters"""
    data = request.get_json()
    print(f"🎛️ API: Efectos recibidos: {data}")  # Debug log
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    results = []
    for effect, value in data.items():
        try:
            value = int(value)
            if not (0 <= value <= 100):
                results.append({
                    'effect': effect, 
                    'success': False, 
                    'error': 'Value must be 0-100'
                })
                continue
                
            success = api.guitar_midi._set_effect(effect, value)
            print(f"   {effect}: {value}% -> {'✅' if success else '❌'}")  # Debug log
            results.append({
                'effect': effect, 
                'value': value, 
                'success': success
            })
        except (ValueError, TypeError):
            results.append({
                'effect': effect, 
                'success': False, 
                'error': 'Invalid value type'
            })
    
    return jsonify({'success': True, 'results': results})

@api.route('/instruments/library', methods=['GET'])
def get_instrument_library():
    """Get available instruments from FluidSynth"""
    try:
        # Extract real instruments from FluidSynth
        instruments = api.guitar_midi._get_fluidsynth_instruments()
        return jsonify({
            'success': True, 
            'instruments': instruments
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Failed to load instruments: {str(e)}'
        }), 500

@api.route('/config/save', methods=['POST'])
def save_config():
    """Save current configuration to persistent storage"""
    try:
        api.guitar_midi._save_config()
        return jsonify({'success': True, 'message': 'Configuration saved'})
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Failed to save config: {str(e)}'
        }), 500

@api.route('/config/load', methods=['POST'])
def load_config():
    """Load configuration from persistent storage"""
    try:
        api.guitar_midi._load_config()
        return jsonify({'success': True, 'message': 'Configuration loaded'})
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Failed to load config: {str(e)}'
        }), 500

@api.route('/system/validate', methods=['POST'])
def validate_system():
    """Validate FluidSynth preset mapping"""
    try:
        # Validar presets
        is_valid = api.guitar_midi._validate_preset_mapping()
        
        return jsonify({
            'success': True,
            'valid': is_valid,
            'message': 'Validación completada - revisar logs para detalles'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error en validación: {str(e)}'
        }), 500

# ============================================================================
# NUEVAS APIs PARA CONTROLADORES ESPECÍFICOS
# ============================================================================

@api.route('/controllers', methods=['GET'])
def get_controllers():
    """Get all connected controllers (original + modular)"""
    try:
        # Controladores originales
        controllers_info = api.guitar_midi.get_connected_controllers()
        
        # Controladores modulares
        modular_status = api.guitar_midi.get_modular_status()
        
        # Combinar ambos sistemas
        all_controllers = controllers_info['controllers'].copy()
        
        # Agregar controladores modulares
        for name, controller_status in modular_status.get('controllers', {}).items():
            all_controllers[name] = {
                'type': controller_status.get('device_type', 'modular'),
                'connected': controller_status.get('is_active', False),
                'current_preset': controller_status.get('current_preset', 0),
                'modular': True  # Marcar como modular
            }
        
        return jsonify({
            'success': True,
            'controllers': all_controllers,
            'count': len(all_controllers),
            'types': list(set([c.get('type', 'unknown') for c in all_controllers.values()])),
            'modular_active': modular_status.get('modular_active', False)
        })
        
    except Exception as e:
        print(f"❌ Error obteniendo controladores: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'controllers': {},
            'count': 0,
            'types': []
        })

@api.route('/controllers/<controller_name>/preset/<int:preset_id>', methods=['POST'])
def set_controller_preset(controller_name, preset_id):
    """Set preset for specific controller (original + modular)"""
    try:
        # Verificar en controladores originales
        if controller_name in api.guitar_midi.connected_controllers:
            return _set_original_controller_preset(controller_name, preset_id)
        
        # Verificar en controladores modulares (NUEVO)
        if controller_name in api.guitar_midi.active_controllers:
            return _set_modular_controller_preset(controller_name, preset_id)
        
        return jsonify({
            'success': False, 
            'error': f'Controller {controller_name} not found'
        }), 404
        
    except Exception as e:
        print(f"❌ Error estableciendo preset {preset_id} en {controller_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _set_original_controller_preset(controller_name, preset_id):
    """Establecer preset en controlador original usando simulación MIDI"""
    controller_info = api.guitar_midi.connected_controllers[controller_name]
    controller_type = controller_info['type']
    
    # Verificar que el preset existe para este controlador
    if controller_type not in api.guitar_midi.controller_presets:
        return jsonify({
            'success': False, 
            'error': f'No presets defined for controller type {controller_type}'
        }), 400
    
    available_presets = api.guitar_midi.controller_presets[controller_type]
    if preset_id not in available_presets:
        return jsonify({
            'success': False, 
            'error': f'Preset {preset_id} not available for {controller_type}'
        }), 400
    
    preset_info = available_presets[preset_id]
    
    # Calcular PC número basado en el rango del controlador
    # Cada controlador tiene un rango de 8 presets
    base_range = controller_info.get('preset_range_start', 0)
    pc_number = base_range + preset_id
    
    print(f"🎛️ {controller_type}: Simulando MIDI PC {pc_number} para preset {preset_id} ({preset_info['name']})")
    
    # Usar simulación de MIDI Program Change (como MIDI Captain)
    success = api.guitar_midi._simulate_midi_program_change(pc_number)
    
    if success:
        # Actualizar preset actual del controlador
        api.guitar_midi.connected_controllers[controller_name]['current_preset'] = preset_id
        print(f"✅ {controller_type}: Preset {preset_id} activado mediante simulación MIDI")
    else:
        print(f"❌ Error en simulación MIDI para {controller_type} preset {preset_id}")
    
    return jsonify({
        'success': success,
        'controller': controller_name,
        'preset_id': preset_id,
        'preset_name': preset_info['name'] if success else None
    })

def _set_modular_controller_preset(controller_name, preset_id):
    """Establecer preset en controlador modular usando simulación MIDI"""
    controller = api.guitar_midi.active_controllers[controller_name]
    device_info = controller.get('device_info', {})
    presets = controller.get('presets', {})
    
    # Verificar que el preset existe
    if preset_id not in presets:
        return jsonify({
            'success': False,
            'error': f'Preset {preset_id} not available for {controller_name}'
        }), 400
    
    preset_info = presets[preset_id]
    
    # Calcular PC número basado en el rango del controlador
    base_range = device_info.get('preset_range_start', 0)
    pc_number = base_range + preset_id
    
    print(f"🎛️ {controller_name}: Simulando MIDI PC {pc_number} para preset {preset_id} ({preset_info.get('name', 'Unknown')})")
    
    # Usar simulación de MIDI Program Change (como MIDI Captain)
    success = api.guitar_midi._simulate_midi_program_change(pc_number)
    
    if success:
        # Actualizar preset actual del controlador
        controller['current_preset'] = preset_id
        print(f"✅ {controller_name}: Preset {preset_id} activado mediante simulación MIDI")
    else:
        print(f"❌ Error en simulación MIDI para {controller_name} preset {preset_id}")
    
    return jsonify({
        'success': success,
        'controller': controller_name,
        'preset_id': preset_id,
        'preset_name': preset_info.get('name', 'Unknown') if success else None
    })

@api.route('/controllers/<controller_name>/presets', methods=['GET'])
def get_controller_presets(controller_name):
    """Get presets for specific controller (original + modular)"""
    try:
        # Verificar en controladores originales
        if controller_name in api.guitar_midi.connected_controllers:
            controller_info = api.guitar_midi.connected_controllers[controller_name]
            controller_type = controller_info['type']
            presets = api.guitar_midi.controller_presets.get(controller_type, {})
            
            return jsonify({
                'success': True,
                'controller': controller_name,
                'controller_type': controller_type,
                'current_preset': controller_info['current_preset'],
                'presets': presets
            })
        
        # Verificar en controladores modulares (NUEVO)
        if controller_name in api.guitar_midi.active_controllers:
            controller = api.guitar_midi.active_controllers[controller_name]
            device_info = controller.get('device_info', {})
            presets = controller.get('presets', {})
            
            return jsonify({
                'success': True,
                'controller': controller_name,
                'controller_type': device_info.get('type', 'unknown'),
                'current_preset': controller.get('current_preset', 0),
                'presets': presets
            })
        
        return jsonify({
            'success': False, 
            'error': f'Controller {controller_name} not found'
        }), 404
        
    except Exception as e:
        print(f"❌ Error obteniendo presets de {controller_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/controllers/types', methods=['GET'])
def get_controller_types():
    """Get information about supported controller types"""
    controller_types_info = {}
    
    for controller_type, presets in api.guitar_midi.controller_presets.items():
        controller_types_info[controller_type] = {
            'name': controller_type.replace('_', ' ').title(),
            'preset_count': len(presets),
            'channels': list(set(p['channel'] for p in presets.values())),
            'patterns': api.guitar_midi.controller_patterns.get(controller_type, [])
        }
    
    return jsonify({
        'success': True,
        'controller_types': controller_types_info
    })

@api.route('/controllers/<controller_name>/effects', methods=['POST'])
def set_controller_effects(controller_name):
    """Set effects for specific controller channels"""
    if controller_name not in api.guitar_midi.connected_controllers:
        return jsonify({
            'success': False, 
            'error': f'Controller {controller_name} not found'
        }), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    controller_info = api.guitar_midi.connected_controllers[controller_name]
    controller_type = controller_info['type']
    presets = api.guitar_midi.controller_presets.get(controller_type, {})
    
    results = []
    
    # Aplicar efectos a todos los canales del controlador
    channels = list(set(p['channel'] for p in presets.values()))
    
    for effect_name, value in data.items():
        try:
            value = int(value)
            if not (0 <= value <= 127):
                results.append({
                    'effect': effect_name,
                    'success': False,
                    'error': 'Value must be 0-127'
                })
                continue
            
            # Aplicar efecto a todos los canales del controlador
            success_count = 0
            for channel in channels:
                if api.guitar_midi._apply_channel_effect(channel, effect_name, value):
                    success_count += 1
            
            results.append({
                'effect': effect_name,
                'value': value,
                'success': success_count > 0,
                'channels_affected': success_count
            })
            
        except (ValueError, TypeError):
            results.append({
                'effect': effect_name,
                'success': False,
                'error': 'Invalid value type'
            })
    
    return jsonify({
        'success': True,
        'controller': controller_name,
        'results': results
    })