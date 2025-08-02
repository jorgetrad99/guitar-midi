import time
import rtmidi
import fluidsynth

def main():
    # Inicializa FluidSynth
    fs = fluidsynth.Synth()
    fs.start(driver="alsa")

    # Carga un SoundFont (asegúrate de tener este archivo en esa ruta o cámbiala)
    sfid = fs.sfload("/usr/share/sounds/sf2/FluidR3_GM.sf2")
    fs.program_select(0, sfid, 0, 0)  # canal 0, banco 0, programa 0 (piano)

    # Inicializa MIDI In con python-rtmidi
    midi_in = rtmidi.MidiIn()
    available_ports = midi_in.get_ports()

    if available_ports:
        print("Puertos MIDI disponibles:")
        for i, port in enumerate(available_ports):
            print(f"{i}: {port}")
        midi_in.open_port(1)
        print(f"Conectado al puerto {available_ports[0]}")
    else:
        print("No se encontraron puertos MIDI.")
        return

    print("Escuchando mensajes MIDI... (Ctrl+C para salir)")

    try:
        while True:
            msg = midi_in.get_message()
            if msg:
                message, delta_time = msg
                status = message[0] & 0xF0
                channel = message[0] & 0x0F
                note = message[1] if len(message) > 1 else None
                velocity = message[2] if len(message) > 2 else None

                if status == 0x90 and velocity > 0:  # Note On
                    print(f"Note On: {note} Velocity: {velocity}")
                    fs.noteon(channel, note, velocity)
                elif status == 0x80 or (status == 0x90 and velocity == 0):  # Note Off
                    print(f"Note Off: {note}")
                    fs.noteoff(channel, note)

            time.sleep(0.001)  # Pequeña espera para evitar uso alto de CPU

    except KeyboardInterrupt:
        print("Saliendo...")

    finally:
        midi_in.close_port()
        fs.delete()


if __name__ == "__main__":
    main()
