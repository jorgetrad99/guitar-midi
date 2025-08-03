#!/bin/bash
# Auto-inicio del sistema Guitar-MIDI
# Para uso en vivo - Plug and Play

echo "🎸 Iniciando sistema Guitar-MIDI..."

# Esperar a que el sistema termine de cargar
echo "⏳ Esperando estabilización del sistema..."
sleep 5

# Configurar audio automáticamente
echo "🔊 Configurando audio..."
amixer cset numid=2 on > /dev/null 2>&1  # Unmute
amixer cset numid=1 100% > /dev/null 2>&1 # Volumen 100%

# Esperar dispositivos USB (reducido)
echo "🔌 Esperando dispositivos USB MIDI..."
sleep 3

# Ir al directorio del proyecto
cd /root/guitar-midi

# Activar entorno virtual
source venv/bin/activate

# Ejecutar el sistema MIDI
echo "🎹 Iniciando sistema MIDI..."
echo "✅ Sistema listo para tocar en vivo!"
echo ""

# Ejecutar el script principal
python scripts/midi_listener.py