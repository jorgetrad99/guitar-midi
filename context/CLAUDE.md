# CLAUDE.md - Context for Guitar-MIDI Project

## Project Overview
This is a monorepo for a Guitar-MIDI looper/sampler system designed to run on a Raspberry Pi with DietPi. The project aims to transform an electric guitar into a multivoice MIDI controller for playing various digital instruments using FluidSynth, soundfonts, and sample playback.

## Architecture
- **Hardware**: Raspberry Pi (DietPi OS) + MIDI controller (e.g., Akai MPK Mini Mk3, MIDI Foot Controller Captain)
- **Software**: Python-based system using rtmidi, FluidSynth, and pygame
- **Audio**: FluidSynth (.sf2 soundfonts) + sample playback (.wav files)

## Current Status
- Basic MIDI listener implemented (`scripts/midi_listener.py`)
- FluidSynth integration working
- Dependencies: numpy, pyfluidsynth, pygame, python-rtmidi

## Planned Structure
```
guitar-midi/
├── scripts/
│   ├── midi_listener.py      # Main MIDI listener (implemented)
│   ├── sampler.py            # Sample player (.wav files) - TO DO
│   ├── fluidsynth_player.py  # FluidSynth player (.sf2) - TO DO
│   └── loop_engine.py        # Looper functionality - TO DO
├── assets/
│   ├── samples/              # .wav sample files - TO DO
│   └── soundfonts/           # .sf2 soundfont files - TO DO
├── config/
│   └── mappings.json         # MIDI note mappings - TO DO
├── README.md
├── requirements.txt
└── CLAUDE.md
```

## Goals
1. **Real-time MIDI processing**: Listen to MIDI controllers and map notes to actions
2. **Multi-instrument synthesis**: Use soundfonts to simulate piano, drums, bass, saxophone, etc.
3. **Sample playback**: Trigger .wav samples from MIDI notes
4. **Looping engine**: Record, playback, and manage audio loops
5. **Portable system**: Self-contained Raspberry Pi setup
6. **Future expansions**: Web interface, multi-track recording, effects

## Technical Details
- **MIDI**: Using python-rtmidi for MIDI I/O
- **Audio synthesis**: FluidSynth with GM soundfonts
- **Sample playback**: pygame for .wav file playback
- **Target latency**: Real-time performance for live use
- **Configuration**: JSON-based mapping system

## Development Notes
- Main script connects to port 1 by default (may need adjustment)
- Uses ALSA audio driver for FluidSynth
- Default soundfont path: `/usr/share/sounds/sf2/FluidR3_GM.sf2`
- System designed for live performance use

## MIDI Captain Integration
- **Connection**: USB direct connection (MIDI Captain USB → Raspberry Pi USB)
- **Port Detection**: Automatic detection of MIDI Captain device
- **Instrument Mapping**: 8 instruments mapped to Program Change 0-7
- **Controls**: Program Change for instrument switching, Control Change for effects/looper

### Instrument Map (Program Change):
- PC 0: Piano
- PC 1: Drums (Bank 128)
- PC 2: Bass
- PC 3: Guitar
- PC 4: Saxophone
- PC 5: Strings
- PC 6: Organ
- PC 7: Flute

## Commands to Run
- Test MIDI listener: `python scripts/midi_listener.py`
- Install dependencies: `pip install -r requirements.txt`
- System deps: `sudo apt install python3 python3-pip fluidsynth`

## System Status: ✅ FUNCIONANDO
- **Audio**: Configurado automáticamente al arranque
- **MIDI**: Detección automática de múltiples dispositivos
- **Auto-inicio**: Servicio systemd configurado y funcionando
- **Problema USB resuelto**: Parámetros de arranque configurados para múltiples dispositivos

## Configuración Final
- **Boot delay**: 4 segundos configurado en `/boot/firmware/config.txt`
- **USB timing**: Parámetros de cmdline.txt configurados
- **Audio**: FluidSynth con ganancia 2x para volumen óptimo
- **Desktop**: Configurado para arranque sin interfaz gráfica

## Sistema Plug & Play
El sistema está completamente configurado para uso en vivo:
1. Conectar dispositivos USB MIDI
2. Encender Raspberry Pi
3. Esperar 3 minutos
4. Sistema listo automáticamente

Ver `SETUP_COMPLETO.md` para documentación completa.