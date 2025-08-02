# Guitar MIDI Controller & Multi-Instrument Synthesizer (Monorepo)

## Descripción general

Este proyecto tiene como objetivo transformar una guitarra eléctrica en un controlador MIDI multifonónico para tocar diversos instrumentos digitales como batería, piano, bajo, saxofón y sintetizadores, utilizando principalmente una Raspberry Pi (con DietPi) como núcleo del sistema.

El sistema integra:

- Recepción de señal MIDI desde el controlador (ej. MIDI Foot Controller Captain).
- Conversión de señal de guitarra analógica a MIDI (en desarrollo, actualmente sin pickup hexafónico).
- Reproducción de sonidos de instrumentos reales usando FluidSynth y SoundFonts.
- Posible control y configuración remota vía interfaz web o aplicación móvil.
- Compatibilidad para alternar entre señal de audio directa (guitarra + interfaz) y señal MIDI para sintetizadores.
- Soporte para técnicas de guitarra (vibrato, bending) mapeadas a sonidos MIDI.

---

## Estado actual

- Raspberry Pi corriendo DietPi.
- Entorno Python virtual (`venv`) con librerías:
  - `python-rtmidi` para manejo MIDI.
  - `pyfluidsynth` para síntesis de sonidos con SoundFonts.
  - `pygame` para audio básico (pruebas iniciales).
  - `numpy` y utilidades para procesamiento de señales futuras.
- Scripts base para capturar eventos MIDI y reproducir sonidos FluidSynth.
- Planes para agregar interfaz remota vía WiFi para control y configuración.

---
