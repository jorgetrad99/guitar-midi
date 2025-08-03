#!/bin/bash

echo "🎸 Guitar-MIDI Sistema Integrado"
echo "================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "scripts/midi_engine.py" ]; then
    echo "❌ Error: Ejecutar desde el directorio guitar-midi"
    echo "💡 Uso: cd ~/guitar-midi && ./start_integrated_system.sh"
    exit 1
fi

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "🐍 Activando entorno virtual..."
    source venv/bin/activate
fi

# Función para limpiar al salir
cleanup() {
    echo ""
    echo "🛑 Deteniendo sistema..."
    
    # Terminar procesos
    if [ ! -z "$MIDI_PID" ]; then
        echo "   Deteniendo MIDI Engine..."
        kill $MIDI_PID 2>/dev/null
    fi
    
    if [ ! -z "$FLASK_PID" ]; then
        echo "   Deteniendo Flask..."
        kill $FLASK_PID 2>/dev/null
    fi
    
    # Limpiar archivos temporales
    rm -f /tmp/guitar_midi_*.json 2>/dev/null
    
    echo "✅ Sistema detenido"
    exit 0
}

# Configurar trap para cleanup
trap cleanup INT TERM

# 1. Verificar hotspot (opcional)
echo "📡 1. Verificando hotspot..."
if command -v systemctl &> /dev/null; then
    if ! systemctl is-active --quiet hostapd; then
        echo "   Activando hotspot WiFi..."
        sudo systemctl start hostapd 2>/dev/null
        sudo systemctl start dnsmasq 2>/dev/null
        sleep 2
    else
        echo "   ✅ Hotspot ya activo"
    fi
fi

# 2. Obtener IP
IP=$(ip addr show wlan0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
if [ -z "$IP" ]; then
    IP=$(hostname -I | awk '{print $1}')
    if [ -z "$IP" ]; then
        IP="192.168.4.1"  # Fallback
    fi
fi

# 3. Iniciar MIDI Engine
echo "🎹 2. Iniciando MIDI Engine..."
cd scripts
python3 midi_engine.py &
MIDI_PID=$!
cd ..

# Esperar que el engine se inicialice
sleep 3

# Verificar que el engine esté corriendo
if ! kill -0 $MIDI_PID 2>/dev/null; then
    echo "❌ Error: MIDI Engine no se pudo iniciar"
    exit 1
fi

echo "   ✅ MIDI Engine iniciado (PID: $MIDI_PID)"

# 4. Iniciar Flask Web Server
echo "🌐 3. Iniciando servidor web..."
cd web
python3 app.py &
FLASK_PID=$!
cd ..

# Esperar que Flask se inicialice
sleep 2

# Verificar que Flask esté corriendo
if ! kill -0 $FLASK_PID 2>/dev/null; then
    echo "❌ Error: Flask no se pudo iniciar"
    cleanup
    exit 1
fi

echo "   ✅ Servidor web iniciado (PID: $FLASK_PID)"

# 5. Mostrar información del sistema
echo ""
echo "🎯 GUITAR-MIDI SISTEMA LISTO!"
echo "============================="
echo ""
echo "📡 Red WiFi: Guitar-MIDI"
echo "🔑 Contraseña: guitarmidi2024"
echo "🌐 IP del servidor: $IP"
echo ""
echo "📱 URLs para tu celular:"
echo "   Interfaz simple:   http://$IP:5000/simple"
echo "   Interfaz completa: http://$IP:5000"
echo ""
echo "🎹 Sistema MIDI:"
echo "   - FluidSynth configurado"
echo "   - Instrumentos PC 0-7 listos"
echo "   - Efectos globales disponibles"
echo ""
echo "🎛️ Controles disponibles:"
echo "   - Cambio de instrumentos en tiempo real"
echo "   - Control de efectos (volumen, reverb, chorus)"
echo "   - Botón PANIC para detener todas las notas"
echo ""
echo "⌨️  Atajos desde interfaz web:"
echo "   - P = PANIC"
echo "   - 0-7 = Cambiar a instrumento PC"
echo ""
echo "🔴 Presiona Ctrl+C para detener todo el sistema"
echo ""

# 6. Monitorear procesos
echo "📊 Monitoreando sistema..."
while true; do
    # Verificar que ambos procesos estén corriendo
    if ! kill -0 $MIDI_PID 2>/dev/null; then
        echo "❌ MIDI Engine se detuvo inesperadamente"
        cleanup
        exit 1
    fi
    
    if ! kill -0 $FLASK_PID 2>/dev/null; then
        echo "❌ Flask se detuvo inesperadamente"
        cleanup
        exit 1
    fi
    
    # Mostrar estado cada 30 segundos
    sleep 30
    echo "✅ $(date '+%H:%M:%S') - Sistema funcionando correctamente"
done