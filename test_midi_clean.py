#!/usr/bin/env python3
"""
🎸 Test MIDI Clean - SOLO CONTROLADORES FÍSICOS
"""

import rtmidi
import fluidsynth
import time

def main():
    print("🎸 Test MIDI Clean - FUNCIONANDO")
    
    # Presets
    presets = {
        0: {'name': 'Piano', 'program': 0},
        1: {'name': 'Guitar', 'program': 27}, 
        2: {'name': 'Bass', 'program': 33},
        3: {'name': 'Strings', 'program': 48}
    }
    
    current_preset = 0
    
    # 1. FluidSynth
    print("🎹 Inicializando FluidSynth...")
    fs = fluidsynth.Synth()
    fs.start(driver="alsa")
    sfid = fs.sfload("/usr/share/sounds/sf2/FluidR3_GM.sf2")
    print("✅ FluidSynth OK")
    
    # 2. MIDI Output - SOLO CONTROLADORES FÍSICOS
    print("📤 Configurando MIDI Output...")
    midi_out = rtmidi.MidiOut()
    out_ports = midi_out.get_ports()
    
    midi_outputs = []
    target_controllers = ['pico', 'captain', 'mpk', 'akai']
    
    for i, port in enumerate(out_ports):
        # SOLO conectar a controladores conocidos
        if any(controller in port.lower() for controller in target_controllers):
            try:
                output = rtmidi.MidiOut()
                output.open_port(i)
                midi_outputs.append({'name': port, 'out': output})
                print(f"✅ Controlador conectado: {port}")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    midi_out.close_port()
    print(f"🎛️ {len(midi_outputs)} controladores configurados")
    
    # 3. Función para cambiar preset
    def change_preset(preset_num, source="manual"):
        nonlocal current_preset
        
        if preset_num not in presets:
            return False
            
        preset_info = presets[preset_num]
        print(f"\n🎵 Preset {preset_num}: {preset_info['name']} (desde {source})")
        
        # Cambiar sonido FluidSynth
        result = fs.program_select(0, sfid, 0, preset_info['program'])
        if result == 0:
            print(f"✅ Sonido cambiado a: {preset_info['name']}")
            
            # Tocar nota de prueba
            fs.noteon(0, 60, 100)  # C4
            time.sleep(0.2)
            fs.noteoff(0, 60)
            
        else:
            print(f"❌ Error FluidSynth: {result}")
            return False
        
        # Enviar SOLO a controladores físicos
        for output in midi_outputs:
            try:
                pc_message = [0xC0, preset_num]
                output['out'].send_message(pc_message)
                print(f"📤 PC {preset_num} → {output['name']}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        current_preset = preset_num
        return True
    
    # 4. MIDI Input
    print("\n🎛️ Configurando MIDI Input...")
    midi_in = rtmidi.MidiIn()
    in_ports = midi_in.get_ports()
    
    def on_midi(message, data):
        msg, _ = message
        if len(msg) >= 2 and 0xC0 <= msg[0] <= 0xCF:
            preset = msg[1]
            if 0 <= preset <= 3:
                print(f"🎛️ MIDI IN: Program Change {preset}")
                change_preset(preset, "MIDI_Controller")
    
    # Conectar a controlador
    for i, port in enumerate(in_ports):
        if any(controller in port.lower() for controller in target_controllers):
            midi_in.open_port(i)
            midi_in.set_callback(on_midi)
            print(f"🔌 Input: {port}")
            break
    
    # 5. Interface
    print("\n" + "="*50)
    print("🚀 SISTEMA FUNCIONANDO")
    print("📋 Pruebas:")
    print("  0: Piano    1: Guitar")
    print("  2: Bass     3: Strings")
    print("  t: Tocar nota prueba")
    print("  s: Estado   q: Salir")
    print("="*50)
    
    # Preset inicial con sonido
    change_preset(0, "inicio")
    
    # Loop
    try:
        while True:
            cmd = input(f"\nPreset actual: {current_preset} ({presets[current_preset]['name']}) > ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 't':
                # Tocar nota de prueba
                fs.noteon(0, 60, 100)
                time.sleep(0.5)
                fs.noteoff(0, 60)
                print("🎵 Nota de prueba tocada")
            elif cmd == 's':
                print(f"📊 Estado:")
                print(f"   Preset: {current_preset} ({presets[current_preset]['name']})")
                print(f"   Controladores: {len(midi_outputs)}")
            elif cmd.isdigit():
                preset_num = int(cmd)
                if 0 <= preset_num <= 3:
                    change_preset(preset_num, "manual")
                else:
                    print("❌ Preset debe ser 0-3")
            else:
                print("❌ Comando no válido")
                
    except KeyboardInterrupt:
        pass
    
    print("\n🛑 Cerrando...")
    
    # Cleanup
    try:
        midi_in.close_port()
        for output in midi_outputs:
            output['out'].close_port()
        fs.delete()
    except:
        pass
    
    print("👋 Terminado")

if __name__ == "__main__":
    main()