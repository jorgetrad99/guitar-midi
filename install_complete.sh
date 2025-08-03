#!/bin/bash

echo "🎸 Guitar-MIDI Complete System - Instalador ÚNICO"
echo "================================================="
echo ""
echo "Este instalador REEMPLAZA todo el sistema anterior con:"
echo "• UN SOLO archivo Python (guitar_midi_complete.py)"
echo "• Auto-detección de audio automática"
echo "• Base de datos SQLite integrada"
echo "• Interfaz web móvil moderna"
echo "• Auto-inicio en arranque"
echo "• Hotspot WiFi propio"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "guitar_midi_complete.py" ]; then
    echo "❌ Error: Ejecutar desde el directorio guitar-midi"
    echo "💡 Uso: cd ~/guitar-midi && ./install_complete.sh"
    exit 1
fi

GUITAR_MIDI_DIR=$(pwd)
USER=$(whoami)

read -p "¿Continuar con la instalación COMPLETA? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Instalación cancelada"
    exit 1
fi

echo ""
echo "🧹 1. Limpiando sistema anterior..."

# Detener servicios anteriores
OLD_SERVICES=("guitar-midi.service" "guitar-midi-complete.service" "guitar-midi-web.service")
for service in "${OLD_SERVICES[@]}"; do
    if systemctl is-enabled $service >/dev/null 2>&1; then
        echo "   Deteniendo: $service"
        sudo systemctl disable $service >/dev/null 2>&1
        sudo systemctl stop $service >/dev/null 2>&1
    fi
done

# Remover scripts antiguos
OLD_SCRIPTS=(
    "/usr/local/bin/guitar-midi-start.sh"
    "/usr/local/bin/guitar-midi-start"
    "/usr/local/bin/guitar-midi-stop"
    "/usr/local/bin/guitar-midi-status"
    "/usr/local/bin/guitar-midi-logs"
    "/usr/local/bin/guitar-midi-restart"
    "/usr/local/bin/guitar-midi"
)
for script in "${OLD_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        sudo rm -f "$script"
    fi
done

# Remover carpetas innecesarias
echo "   Limpiando archivos innecesarios..."
rm -rf scripts/
rm -rf web/
rm -f *.sh audio_debug.sh fix_audio.sh hotspot_simple.sh install*.sh setup_*.sh start_*.sh test_*.sh test_*.py
rm -f SETUP_COMPLETO.md

echo "   ✅ Sistema anterior limpiado"

echo ""
echo "📦 2. Instalando dependencias..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y fluidsynth fluid-soundfont-gm
sudo apt install -y alsa-utils
sudo apt install -y sqlite3

echo ""
echo "🐍 3. Configurando entorno Python..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "📚 Instalando dependencias Python..."
pip install --upgrade pip
pip install python-rtmidi pyfluidsynth
pip install Flask Flask-SocketIO eventlet

echo ""
echo "📡 4. Configurando hotspot WiFi..."
if ! systemctl is-enabled hostapd >/dev/null 2>&1; then
    echo "   Instalando software de hotspot..."
    sudo apt install -y hostapd dnsmasq
    
    # Configurar hostapd
    sudo tee /etc/hostapd/hostapd.conf > /dev/null << EOF
interface=wlan0
driver=nl80211
ssid=Guitar-MIDI
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=guitarmidi2024
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

    # Configurar dnsmasq
    sudo tee /etc/dnsmasq.conf > /dev/null << EOF
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
EOF

    # Configurar IP estática
    sudo tee -a /etc/dhcpcd.conf > /dev/null << EOF

# Guitar-MIDI Hotspot
interface wlan0
static ip_address=192.168.4.1/24
nohook wpa_supplicant
EOF

    # Habilitar servicios
    sudo systemctl unmask hostapd
    sudo systemctl enable hostapd
    sudo systemctl enable dnsmasq
    sudo sed -i 's/#DAEMON_CONF=""/DAEMON_CONF="\/etc\/hostapd\/hostapd.conf"/g' /etc/default/hostapd
    
    echo "   ✅ Hotspot configurado"
else
    echo "   ✅ Hotspot ya configurado"
fi

echo ""
echo "⚙️  5. Configurando servicio systemd ÚNICO..."
sudo tee /etc/systemd/system/guitar-midi-complete.service > /dev/null << EOF
[Unit]
Description=Guitar-MIDI Complete System
After=network.target sound.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$GUITAR_MIDI_DIR
Environment=HOME=/home/$USER
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/$USER/.local/bin
ExecStartPre=/bin/sleep 15
ExecStartPre=/bin/bash -c 'if systemctl is-enabled hostapd; then systemctl start hostapd dnsmasq; fi'
ExecStart=$GUITAR_MIDI_DIR/venv/bin/python guitar_midi_complete.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/guitar-midi-complete.log
StandardError=append:/var/log/guitar-midi-complete.log

# Límites de recursos
MemoryMax=512M
CPUQuota=80%

# Timeouts
TimeoutStartSec=120
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "📝 6. Configurando logs..."
sudo touch /var/log/guitar-midi-complete.log
sudo chown $USER:$USER /var/log/guitar-midi-complete.log
sudo chmod 644 /var/log/guitar-midi-complete.log

echo ""
echo "🎛️ 7. Creando comando de control único..."
sudo tee /usr/local/bin/guitar-midi > /dev/null << 'EOF'
#!/bin/bash

SERVICE_NAME="guitar-midi-complete.service"

case "$1" in
    start)
        echo "🎸 Iniciando Guitar-MIDI Complete System..."
        sudo systemctl start $SERVICE_NAME
        sleep 3
        systemctl is-active $SERVICE_NAME >/dev/null && echo "✅ Sistema iniciado" || echo "❌ Error al iniciar"
        ;;
    stop)
        echo "🛑 Deteniendo Guitar-MIDI Complete System..."
        sudo systemctl stop $SERVICE_NAME
        echo "✅ Sistema detenido"
        ;;
    restart)
        echo "🔄 Reiniciando Guitar-MIDI Complete System..."
        sudo systemctl restart $SERVICE_NAME
        sleep 3
        systemctl is-active $SERVICE_NAME >/dev/null && echo "✅ Sistema reiniciado" || echo "❌ Error al reiniciar"
        ;;
    status)
        echo "📊 Guitar-MIDI Complete System Status"
        echo "====================================="
        echo ""
        echo "🔧 Servicio:"
        systemctl is-active $SERVICE_NAME >/dev/null && echo "   ✅ ACTIVO" || echo "   ❌ INACTIVO"
        echo ""
        echo "🌐 Red:"
        IP=$(ip addr show wlan0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
        if [ -z "$IP" ]; then
            IP=$(hostname -I | awk '{print $1}')
        fi
        echo "   IP: ${IP:-No disponible}"
        echo "   URL: http://${IP:-IP}:5000"
        echo ""
        echo "📋 Comandos:"
        echo "   guitar-midi start    - Iniciar sistema"
        echo "   guitar-midi stop     - Detener sistema"
        echo "   guitar-midi restart  - Reiniciar sistema"
        echo "   guitar-midi logs     - Ver logs"
        ;;
    logs)
        echo "📋 Guitar-MIDI Complete Logs (Ctrl+C para salir)"
        echo "=============================================="
        tail -f /var/log/guitar-midi-complete.log
        ;;
    *)
        echo "🎸 Guitar-MIDI Complete System Control"
        echo "======================================"
        echo ""
        echo "Uso: guitar-midi {start|stop|restart|status|logs}"
        echo ""
        echo "Comandos:"
        echo "  start    - Iniciar el sistema completo"
        echo "  stop     - Detener el sistema"
        echo "  restart  - Reiniciar el sistema"
        echo "  status   - Ver estado del sistema"
        echo "  logs     - Ver logs en tiempo real"
        echo ""
        exit 1
        ;;
esac
EOF

sudo chmod +x /usr/local/bin/guitar-midi

echo ""
echo "✅ 8. Habilitando servicio..."
sudo systemctl daemon-reload
sudo systemctl enable guitar-midi-complete.service

echo ""
echo "🧪 9. Probando sistema (10 segundos)..."
sudo systemctl start guitar-midi-complete.service
sleep 10

if systemctl is-active guitar-midi-complete.service >/dev/null; then
    echo "   ✅ Sistema funciona correctamente"
    sudo systemctl stop guitar-midi-complete.service
else
    echo "   ⚠️  Sistema tiene problemas, ver logs: guitar-midi logs"
fi

echo ""
echo "🎉 INSTALACIÓN COMPLETA TERMINADA!"
echo "================================="
echo ""
echo "📋 Sistema Guitar-MIDI Complete configurado:"
echo "   • UN SOLO archivo Python ✅"
echo "   • Auto-detección de audio ✅"
echo "   • Base de datos SQLite ✅"
echo "   • Interfaz web móvil moderna ✅"
echo "   • Auto-inicio en arranque ✅"
echo "   • Hotspot WiFi propio ✅"
echo ""
echo "🎛️ Control del sistema:"
echo "   guitar-midi start    - Iniciar sistema"
echo "   guitar-midi stop     - Detener sistema"  
echo "   guitar-midi status   - Ver estado"
echo "   guitar-midi logs     - Ver logs"
echo ""
echo "🔄 Para activar completamente:"
echo "   sudo reboot"
echo ""
echo "📱 Después del reinicio (~2 minutos):"
echo "   1. Conectar celular a WiFi 'Guitar-MIDI'"
echo "   2. Contraseña: guitarmidi2024"
echo "   3. Abrir: http://192.168.4.1:5000"
echo ""
echo "🎸 ¡Sistema Guitar-MIDI Complete listo!"
echo ""
echo "🔍 Para verificar estado después del reinicio:"
echo "   guitar-midi status"
echo ""
echo "📁 Archivos del sistema:"
echo "   - guitar_midi_complete.py (ÚNICO archivo principal)"
echo "   - guitar_midi.db (base de datos SQLite)"
echo "   - venv/ (entorno Python)"