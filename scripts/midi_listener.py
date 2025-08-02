import time
import rtmidi
import fluidsynth

class MidiCaptainController:
    def __init__(self):
        # Inicializa FluidSynth
        self.fs = fluidsynth.Synth()
        self.fs.start(driver="alsa")
        
        # Carga SoundFont
        self.sfid = self.fs.sfload("/usr/share/sounds/sf2/FluidR3_GM.sf2")
        
        # Mapeo de instrumentos (Program Change números del MIDI Captain)
        self.instrument_map = {
            0: {"name": "Piano", "program": 0, "bank": 0},
            1: {"name": "Drums", "program": 0, "bank": 128}, # Drum kit
            2: {"name": "Bass", "program": 32, "bank": 0},   # Acoustic Bass
            3: {"name": "Guitar", "program": 24, "bank": 0}, # Acoustic Guitar
            4: {"name": "Saxophone", "program": 64, "bank": 0}, # Soprano Sax
            5: {"name": "Strings", "program": 48, "bank": 0}, # String Ensemble
            6: {"name": "Organ", "program": 16, "bank": 0},  # Hammond Organ
            7: {"name": "Flute", "program": 73, "bank": 0},  # Flute
        }
        
        self.current_instrument = 0
        self.set_instrument(0)  # Comenzar con piano
        
    def set_instrument(self, pc_number):
        """Cambia el instrumento basado en Program Change"""
        if pc_number in self.instrument_map:
            instrument = self.instrument_map[pc_number]
            self.fs.program_select(0, self.sfid, instrument["bank"], instrument["program"])
            self.current_instrument = pc_number
            print(f"🎹 Instrumento cambiado a: {instrument['name']} (PC: {pc_number})")
        else:
            print(f"⚠️  Instrumento no mapeado: PC {pc_number}")
    
    def handle_midi_message(self, message):
        """Procesa mensajes MIDI del MIDI Captain"""
        status = message[0] & 0xF0
        channel = message[0] & 0x0F
        
        if len(message) >= 2:
            data1 = message[1]
            data2 = message[2] if len(message) > 2 else 0
            
            # Program Change - Cambio de instrumento
            if status == 0xC0:  # Program Change
                print(f"📡 Program Change recibido: {data1}")
                self.set_instrument(data1)
                
            # Control Change - Para funciones especiales
            elif status == 0xB0:  # Control Change
                print(f"🎛️  Control Change: CC{data1} = {data2}")
                # Aquí puedes mapear CCs específicos para looper, efectos, etc.
                
            # Note On/Off - Tocar notas con el instrumento actual
            elif status == 0x90 and data2 > 0:  # Note On
                print(f"🎵 Note On: {data1} Vel: {data2} ({self.instrument_map[self.current_instrument]['name']})")
                self.fs.noteon(channel, data1, data2)
                
            elif status == 0x80 or (status == 0x90 and data2 == 0):  # Note Off
                print(f"🎵 Note Off: {data1}")
                self.fs.noteoff(channel, data1)
    
    def cleanup(self):
        """Limpia recursos"""
        self.fs.delete()

def get_all_midi_ports(available_ports):
    """Obtiene todos los puertos MIDI disponibles sin discriminar modelo"""
    devices = []
    for i, port in enumerate(available_ports):
        devices.append({"port": i, "name": port})
    return devices

def main():
    controller = MidiCaptainController()
    
    # Obtener puertos MIDI disponibles
    midi_inputs = []
    available_ports = rtmidi.MidiIn().get_ports()

    if not available_ports:
        print("❌ No se encontraron puertos MIDI.")
        return

    print("🔌 Puertos MIDI disponibles:")
    devices = get_all_midi_ports(available_ports)
    
    # Crear conexiones MIDI para todos los dispositivos
    for device in devices:
        print(f"  {device['port']}: {device['name']}")
        try:
            midi_in = rtmidi.MidiIn()
            midi_in.open_port(device['port'])
            midi_inputs.append({
                "input": midi_in,
                "device": device
            })
            print(f"✅ Conectado a: {device['name']}")
        except Exception as e:
            print(f"❌ Error conectando a {device['name']}: {e}")

    if not midi_inputs:
        print("❌ No se pudo conectar a ningún dispositivo MIDI")
        return

    print("\n🎸 Sistema Guitar-MIDI listo!")
    print("🎹 Instrumentos disponibles:")
    for pc, instrument in controller.instrument_map.items():
        print(f"   PC {pc}: {instrument['name']}")
    print("\n⚡ Presiona pedales del MIDI Captain para cambiar instrumentos...")
    print("🎵 Toca notas MIDI en cualquier dispositivo para escuchar")
    print("🛑 Ctrl+C para salir\n")

    try:
        while True:
            # Revisar mensajes de TODOS los dispositivos MIDI conectados
            for i, midi_input in enumerate(midi_inputs):
                msg = midi_input["input"].get_message()
                if msg:
                    message, delta_time = msg
                    device_name = midi_input["device"]["name"]
                    
                    # Mostrar de qué puerto viene el mensaje (genérico)
                    print(f"🎵 [Puerto {i}] ", end="")
                    
                    controller.handle_midi_message(message)
            
            time.sleep(0.001)  # Pequeña espera para evitar uso alto de CPU

    except KeyboardInterrupt:
        print("\n🛑 Saliendo del sistema Guitar-MIDI...")

    finally:
        # Cerrar todas las conexiones MIDI
        for midi_input in midi_inputs:
            midi_input["input"].close_port()
        controller.cleanup()
        print("✅ Recursos liberados correctamente")


if __name__ == "__main__":
    main()
