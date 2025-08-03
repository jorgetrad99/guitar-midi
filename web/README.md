# Guitar-MIDI Web Interface

## Descripción
Interfaz web responsive para control en tiempo real del sistema Guitar-MIDI desde dispositivos móviles.

## Funcionalidades
- Control de instrumentos MIDI (PC 0-7)
- Sistema de presets personalizables
- Control de efectos (reverb, chorus, volumen)
- Interfaz optimizada para uso en vivo
- Comunicación en tiempo real via WebSocket

## Tecnologías
- Backend: Flask + Socket.IO
- Frontend: HTML5 + CSS3 + JavaScript
- PWA: Progressive Web App
- Comunicación: REST API + WebSocket

## Estructura
```
web/
├── app.py                    # Servidor Flask principal
├── api/                      # APIs REST
│   ├── __init__.py
│   ├── midi_controller.py    # Control MIDI
│   ├── presets.py           # Gestión presets
│   └── system_info.py       # Info del sistema
├── static/                   # Archivos estáticos
│   ├── css/
│   ├── js/
│   └── icons/
├── templates/                # Templates HTML
│   ├── index.html
│   ├── instruments.html
│   └── presets.html
└── data/                     # Datos persistentes
    ├── presets/
    ├── instruments.json
    └── current_config.json
```

## Instalación
Ver SETUP_COMPLETO.md para instrucciones de instalación completa.