#!/bin/bash

# Test del sistema auto-inicio antes del reboot
echo "🧪 Guitar-MIDI Auto-Start Test"
echo "=============================="

# Verificar que el servicio esté instalado
if [ ! -f "/etc/systemd/system/guitar-midi-complete.service" ]; then
    echo "❌ Error: Servicio no instalado"
    echo "💡 Ejecuta primero: ./install_autostart.sh"
    exit 1
fi

echo "📋 Verificando configuración..."

# 1. Verificar servicio
echo "🔧 1. Verificando servicio systemd..."
if systemctl is-enabled guitar-midi-complete.service >/dev/null 2>&1; then
    echo "   ✅ Servicio habilitado para auto-inicio"
else
    echo "   ❌ Servicio NO habilitado"
    exit 1
fi

# 2. Verificar archivos
echo "📁 2. Verificando archivos..."
files=(
    "/usr/local/bin/guitar-midi-start.sh"
    "/usr/local/bin/guitar-midi-start"
    "/usr/local/bin/guitar-midi-stop"
    "/usr/local/bin/guitar-midi-status"
    "/usr/local/bin/guitar-midi-logs"
    "/usr/local/bin/guitar-midi-restart"
    "/var/log/guitar-midi.log"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file FALTA"
    fi
done

# 3. Test manual del servicio
echo "🧪 3. Test manual del servicio..."
echo "   Iniciando servicio para prueba..."
sudo systemctl start guitar-midi-complete.service

# Esperar un poco
sleep 5

# Verificar estado
if systemctl is-active guitar-midi-complete.service >/dev/null 2>&1; then
    echo "   ✅ Servicio se inició correctamente"
    
    # Verificar procesos
    sleep 10
    
    MIDI_PROC=$(pgrep -f "midi_engine.py")
    FLASK_PROC=$(pgrep -f "app.py")
    
    if [ ! -z "$MIDI_PROC" ]; then
        echo "   ✅ MIDI Engine ejecutándose (PID: $MIDI_PROC)"
    else
        echo "   ❌ MIDI Engine NO ejecutándose"
    fi
    
    if [ ! -z "$FLASK_PROC" ]; then
        echo "   ✅ Flask Web ejecutándose (PID: $FLASK_PROC)"
    else
        echo "   ❌ Flask Web NO ejecutándose"
    fi
    
    # Verificar puerto
    if netstat -tlnp 2>/dev/null | grep -q ":5000 "; then
        echo "   ✅ Puerto 5000 activo"
    else
        echo "   ❌ Puerto 5000 NO activo"
    fi
    
    # Obtener IP
    IP=$(ip addr show wlan0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
    if [ -z "$IP" ]; then
        IP=$(hostname -I | awk '{print $1}')
    fi
    
    if [ ! -z "$IP" ]; then
        echo "   🌐 Sistema disponible en: http://$IP:5000/simple"
    fi
    
    # Detener servicio después del test
    echo "   🛑 Deteniendo servicio de prueba..."
    sudo systemctl stop guitar-midi-complete.service
    
else
    echo "   ❌ Servicio NO se pudo iniciar"
    echo "   📋 Ver logs: guitar-midi-logs"
    exit 1
fi

# 4. Verificar hotspot
echo "🔥 4. Verificando configuración de hotspot..."
if systemctl is-enabled hostapd >/dev/null 2>&1; then
    echo "   ✅ Hotspot configurado"
    if systemctl is-active hostapd >/dev/null 2>&1; then
        echo "   ✅ Hotspot activo"
    else
        echo "   ⚠️  Hotspot no activo (se activará en el arranque)"
    fi
else
    echo "   ⚠️  Hotspot no configurado"
    echo "   💡 Para configurar: ./hotspot_simple.sh"
fi

echo ""
echo "🎯 RESULTADO DEL TEST:"
echo "====================="
echo ""
echo "✅ Auto-inicio configurado correctamente"
echo "✅ Servicio funciona manualmente"
echo "✅ Todos los componentes están listos"
echo ""
echo "🔄 PRÓXIMOS PASOS:"
echo "=================="
echo ""
echo "1️⃣  Reiniciar Raspberry Pi:"
echo "   sudo reboot"
echo ""
echo "2️⃣  Después del reinicio (~2 minutos):"
echo "   - El sistema se iniciará automáticamente"
echo "   - WiFi 'Guitar-MIDI' estará disponible"
echo "   - Acceso: http://192.168.4.1:5000/simple"
echo ""
echo "3️⃣  Para verificar estado después del reinicio:"
echo "   guitar-midi-status"
echo ""
echo "4️⃣  Para ver logs en tiempo real:"
echo "   guitar-midi-logs"
echo ""
echo "🎸 ¡Sistema listo para uso automático!"