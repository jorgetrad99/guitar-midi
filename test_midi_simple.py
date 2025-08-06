#!/usr/bin/env python3
"""
🎸 Test MIDI Simple - SIN FLASK - Solo prueba básica
"""

import rtmidi
import fluidsynth
import time

def test_midi_sync():
    print("🎸 Test MIDI Simple - SIN WEB")
    
    # Presets básicos
    presets = {
        0: {'name': 'Piano', 'program': 0},
        1: {'name': 'Guitar', 'program': 27}, 
        2: {'name': 'Bass', 'program': 33},
        3: {'name': 'Strings', 'program': 48}
    }
    
    # 1. FluidSynth
    print("🎹 Inicializando FluidSynth...")
    fs = fluidsynth.Synth()
    fs.start(driver="alsa")
    sfid = fs.sfload("/usr/share/sounds/sf2/FluidR3_GM.sf2")
    print("✅ FluidSynth OK")
    
    # 2. MIDI Output
    print("📤 Inicializando MIDI Output...")
    midi_out = rtmidi.MidiOut()
    out_ports = midi_out.get_ports()
    print(f"Puertos disponibles: {out_ports}")
    
    midi_outputs = []
    for i, port in enumerate(out_ports):
        if not any(skip in port for skip in ['Microsoft', 'Mapper', 'Timer']):
            try:
                output = rtmidi.MidiOut()
                output.open_port(i)
                midi_outputs.append({'name': port, 'out': output})
                print(f"✅ Output: {port}")
            except Exception as e:
                print(f"❌ Error: {e}")
    
    midi_out.close_port()
    
    # 3. Función para cambiar preset
    def change_preset(preset_num):
        if preset_num not in presets:
            return False
            
        preset_info = presets[preset_num]
        print(f"\n🎵 Cambiando a preset {preset_num}: {preset_info['name']}")
        
        # Cambiar sonido FluidSynth
        result = fs.program_select(0, sfid, 0, preset_info['program'])
        if result == 0:
            print(f"✅ FluidSynth: {preset_info['name']}")
        else:
            print(f"❌ Error FluidSynth: {result}")
            return False
        
        # Enviar a controladores físicos
        for output in midi_outputs:
            try:
                pc_message = [0xC0, preset_num]  # Program Change
                output['out'].send_message(pc_message)
                print(f"📤 PC {preset_num} → {output['name']}")
            except Exception as e:
                print(f"❌ Error enviando: {e}")
        
        return True
    
    # 4. MIDI Input para recibir
    print("\n🎛️ Inicializando MIDI Input...")
    midi_in = rtmidi.MidiIn()
    in_ports = midi_in.get_ports()
    print(f"Puertos Input: {in_ports}")
    
    def on_midi(message, data):
        msg, _ = message
        if len(msg) >= 2 and 0xC0 <= msg[0] <= 0xCF:
            preset = msg[1]
            if 0 <= preset <= 7:
                print(f"🎛️ MIDI recibido: Preset {preset}")
                change_preset(preset)
    
    # Conectar MIDI Input
    for i, port in enumerate(in_ports):
        if any(word in port.lower() for word in ['pico', 'captain', 'mpk', 'akai']):
            midi_in.open_port(i)
            midi_in.set_callback(on_midi)
            print(f"🔌 Input conectado: {port}")
            break
    
    # 5. Test manual
    print("\n" + "="*50)
    print("🚀 SISTEMA LISTO")
    print("📋 Comandos:")
    print("  0-3: Cambiar preset")
    print("  q: Salir")
    print("="*50)
    
    # Preset inicial
    change_preset(0)
    
    # Loop principal
    try:
        while True:
            cmd = input("\n> ").strip()
            
            if cmd == 'q':
                break
            elif cmd.isdigit():
                preset_num = int(cmd)
                if 0 <= preset_num <= 3:
                    change_preset(preset_num)
                else:
                    print("❌ Preset debe ser 0-3")
            else:
                print("❌ Comando no reconocido")
                
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
    test_midi_sync()