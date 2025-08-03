#!/bin/bash

echo "🎸 Guitar-MIDI Sistema Completo"
echo "==============================="

# 1. Activar hotspot si no está activo
echo "📡 1. Verificando hotspot..."
if ! systemctl is-active --quiet hostapd; then
    echo "   Activando hotspot WiFi..."
    sudo systemctl start hostapd
    sudo systemctl start dnsmasq
    sleep 3
fi

# 2. Verificar entorno virtual
if [ -d ~/guitar-midi/venv ]; then
    echo "🐍 2. Activando entorno virtual..."
    source ~/guitar-midi/venv/bin/activate
fi

# 3. Obtener IP
IP=$(ip addr show wlan0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
if [ -z "$IP" ]; then
    IP="192.168.4.1"  # IP por defecto del hotspot
fi

echo ""
echo "🎯 GUITAR-MIDI LISTO!"
echo "==================="
echo ""
echo "📡 Red WiFi: Guitar-MIDI"
echo "🔑 Contraseña: guitarmidi2024"
echo ""
echo "📱 URLs para tu celular:"
echo "   Página simple: http://$IP:5000/simple"
echo "   Página completa: http://$IP:5000"
echo ""
echo "🎹 Controles rápidos:"
echo "   - Toca los botones de instrumentos para cambiar"
echo "   - Usa los sliders para ajustar volumen/efectos"
echo "   - Botón PANIC para detener todas las notas"
echo ""
echo "⌨️  Atajos de teclado:"
echo "   - P = PANIC"
echo "   - 0-7 = Cambiar a instrumento"
echo ""
echo "🔴 Presiona Ctrl+C para detener el servidor"
echo ""

# 4. Iniciar servidor Flask
cd ~/guitar-midi/web
python3 app.py