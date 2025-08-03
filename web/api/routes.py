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
    """Activate a specific preset/instrument"""
    success = api.guitar_midi._set_instrument(pc)
    if success:
        # Emit WebSocket update
        if hasattr(api.guitar_midi, 'socketio') and api.guitar_midi.socketio:
            api.guitar_midi.socketio.emit('instrument_changed', {
                'pc': pc,
                'name': api.guitar_midi.presets[pc]['name']
            })
    
    return jsonify({
        'success': success, 
        'current_instrument': pc if success else None
    })

@api.route('/effects', methods=['POST'])
def update_effects():
    """Update effect parameters"""
    data = request.get_json()
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