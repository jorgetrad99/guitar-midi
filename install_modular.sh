#!/bin/bash

echo "🎸 Guitar-MIDI Modular System v2.0 - Instalador Completo"
echo "======================================================="
echo ""
echo "🎯 Sistema Multi-Controlador:"
echo "• MVAVE Pocket → 4 presets percusivos (canal 9)"
echo "• Controlador Hexafónico → 6 cuerdas → canales melódicos (0-5)"
echo "• MIDI Captain → control maestro de presets"
echo "• Interfaz web modular con configuración por dispositivo"
echo "• Presets configurables al 100% con base de datos SQLite"
echo "• Auto-detección y hot-plug de dispositivos MIDI"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "guitar_midi_modular.py" ]; then
    echo "❌ Error: Ejecutar desde el directorio guitar-midi"
    echo "💡 Uso: cd ~/guitar-midi && ./install_modular.sh"
    exit 1
fi

GUITAR_MIDI_DIR=$(pwd)
USER=$(whoami)

read -p "¿Continuar con la instalación del sistema MODULAR? (y/N): " -n 1 -r
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

echo "   ✅ Sistema anterior limpiado"

echo ""
echo "📦 2. Instalando dependencias del sistema..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y fluidsynth fluid-soundfont-gm
sudo apt install -y alsa-utils pulseaudio-utils
sudo apt install -y sqlite3

echo ""
echo "🐍 3. Configurando entorno Python modular..."
if [ ! -d "venv_modular" ]; then
    python3 -m venv venv_modular
fi
source venv_modular/bin/activate

echo "📚 Instalando dependencias Python específicas..."
pip install --upgrade pip
pip install python-rtmidi==1.5.8
pip install pyfluidsynth==1.3.3
pip install Flask==3.0.0
pip install Flask-SocketIO==5.3.6
pip install eventlet==0.33.3

echo ""
echo "🎼 4. Configurando audio optimizado..."

# Configurar ALSA para múltiples canales
sudo tee /etc/asound.conf > /dev/null << 'EOF'
# Guitar-MIDI Modular Audio Configuration
pcm.!default {
    type pulse
    server "unix:/run/user/$(id -u)/pulse/native"
}

ctl.!default {
    type pulse
    server "unix:/run/user/$(id -u)/pulse/native"
}

# FluidSynth multi-canal
pcm.fluidsynth {
    type dmix
    ipc_key 1234
    slave {
        pcm "hw:0,0"
        channels 32
        rate 44100
        buffer_size 2048
        period_size 512
    }
}
EOF

# Configurar PulseAudio para baja latencia
mkdir -p ~/.config/pulse
tee ~/.config/pulse/daemon.conf > /dev/null << 'EOF'
# Guitar-MIDI Modular PulseAudio Configuration
high-priority = yes
nice-level = -15
realtime-scheduling = yes
realtime-priority = 9
resample-method = speex-float-1
default-sample-format = float32le
default-sample-rate = 44100
default-sample-channels = 32
default-fragments = 2
default-fragment-size-msec = 5
EOF

echo "   ✅ Audio configurado para múltiples canales"

echo ""
echo "📡 5. Configurando hotspot WiFi (si no existe)..."
if ! systemctl is-enabled hostapd >/dev/null 2>&1; then
    echo "   Instalando software de hotspot..."
    sudo apt install -y hostapd dnsmasq
    
    # Configurar hostapd
    sudo tee /etc/hostapd/hostapd.conf > /dev/null << EOF
interface=wlan0
driver=nl80211
ssid=Guitar-MIDI-Modular
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

# Guitar-MIDI Modular Hotspot
interface wlan0
static ip_address=192.168.4.1/24
nohook wpa_supplicant
EOF

    # Habilitar servicios
    sudo systemctl unmask hostapd
    sudo systemctl enable hostapd
    sudo systemctl enable dnsmasq
    sudo sed -i 's/#DAEMON_CONF=""/DAEMON_CONF="\/etc\/hostapd\/hostapd.conf"/g' /etc/default/hostapd
    
    echo "   ✅ Hotspot configurado: Guitar-MIDI-Modular"
else
    echo "   ✅ Hotspot ya configurado"
fi

echo ""
echo "⚙️  6. Configurando servicio systemd MODULAR..."
sudo tee /etc/systemd/system/guitar-midi-modular.service > /dev/null << EOF
[Unit]
Description=Guitar-MIDI Modular System v2.0
After=network.target sound.target pulseaudio.service
Wants=network.target sound.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$GUITAR_MIDI_DIR
Environment=HOME=/home/$USER  
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/$USER/.local/bin
Environment=XDG_RUNTIME_DIR=/run/user/$(id -u $USER)
Environment=PULSE_SERVER="unix:/run/user/$(id -u $USER)/pulse/native"

# Pre-start: Configurar audio y hotspot
ExecStartPre=/bin/sleep 20
ExecStartPre=/bin/bash -c 'pulseaudio --check -v || pulseaudio --start --log-target=syslog'
ExecStartPre=/bin/bash -c 'if systemctl is-enabled hostapd; then systemctl start hostapd dnsmasq; fi'

# Ejecutar sistema modular
ExecStart=$GUITAR_MIDI_DIR/venv_modular/bin/python guitar_midi_modular.py

# Configuración de reinicio
Restart=always
RestartSec=15
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30

# Límites de recursos
MemoryMax=1G
CPUQuota=90%

# Timeouts
TimeoutStartSec=180
TimeoutStopSec=60

# Logs
StandardOutput=append:/var/log/guitar-midi-modular.log
StandardError=append:/var/log/guitar-midi-modular.log

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "📝 7. Configurando logs y permisos..."
sudo touch /var/log/guitar-midi-modular.log
sudo chown $USER:$USER /var/log/guitar-midi-modular.log
sudo chmod 644 /var/log/guitar-midi-modular.log

# Configurar logrotate
sudo tee /etc/logrotate.d/guitar-midi-modular > /dev/null << 'EOF'
/var/log/guitar-midi-modular.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    postrotate
        systemctl reload guitar-midi-modular.service > /dev/null 2>&1 || true
    endscript
}
EOF

echo ""
echo "🎛️ 8. Creando comando de control MODULAR..."
sudo tee /usr/local/bin/guitar-midi-modular > /dev/null << 'EOF'
#!/bin/bash

SERVICE_NAME="guitar-midi-modular.service"

case "$1" in
    start)
        echo "🎸 Iniciando Guitar-MIDI Modular System v2.0..."
        sudo systemctl start $SERVICE_NAME
        sleep 5
        systemctl is-active $SERVICE_NAME >/dev/null && echo "✅ Sistema modular iniciado" || echo "❌ Error al iniciar"
        ;;
    stop)
        echo "🛑 Deteniendo Guitar-MIDI Modular System..."
        sudo systemctl stop $SERVICE_NAME
        echo "✅ Sistema modular detenido"
        ;;
    restart)
        echo "🔄 Reiniciando Guitar-MIDI Modular System..."
        sudo systemctl restart $SERVICE_NAME
        sleep 5
        systemctl is-active $SERVICE_NAME >/dev/null && echo "✅ Sistema modular reiniciado" || echo "❌ Error al reiniciar"
        ;;
    status)
        echo "📊 Guitar-MIDI Modular System v2.0 Status"
        echo "=========================================="
        echo ""
        echo "🔧 Servicio:"
        if systemctl is-active $SERVICE_NAME >/dev/null; then
            echo "   ✅ ACTIVO"
        else
            echo "   ❌ INACTIVO"
        fi
        echo ""
        echo "🌐 Red:"
        IP=$(ip addr show wlan0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
        if [ -z "$IP" ]; then
            IP=$(hostname -I | awk '{print $1}')
        fi
        echo "   IP: ${IP:-No disponible}"
        echo "   URL: http://${IP:-IP}:5000"
        echo ""
        echo "🎛️ Controladores soportados:"
        echo "   • MVAVE Pocket → 4 presets percusivos"
        echo "   • Hexafónico → 6 cuerdas → canales melódicos"
        echo "   • MIDI Captain → control maestro"
        echo ""
        echo "📋 Comandos:"
        echo "   guitar-midi-modular start    - Iniciar sistema"
        echo "   guitar-midi-modular stop     - Detener sistema"
        echo "   guitar-midi-modular restart  - Reiniciar sistema"
        echo "   guitar-midi-modular logs     - Ver logs"
        echo "   guitar-midi-modular devices  - Listar dispositivos"
        ;;
    logs)
        echo "📋 Guitar-MIDI Modular Logs (Ctrl+C para salir)"
        echo "=============================================="
        tail -f /var/log/guitar-midi-modular.log
        ;;
    devices)
        echo "🎛️ Dispositivos MIDI Detectados"
        echo "==============================="
        if command -v aconnect >/dev/null 2>&1; then
            aconnect -l | grep -E "(client|port)" | while read line; do
                echo "   $line"
            done
        else
            echo "   ⚠️  aconnect no disponible"
        fi
        ;;
    *)
        echo "🎸 Guitar-MIDI Modular System v2.0 Control"
        echo "=========================================="
        echo ""
        echo "Uso: guitar-midi-modular {start|stop|restart|status|logs|devices}"
        echo ""
        echo "🎯 Sistema Multi-Controlador:"
        echo "  • MVAVE Pocket → Presets percusivos"
        echo "  • Hexafónico → Control por cuerdas"
        echo "  • MIDI Captain → Control maestro"
        echo ""
        echo "Comandos:"
        echo "  start    - Iniciar el sistema modular"
        echo "  stop     - Detener el sistema"
        echo "  restart  - Reiniciar el sistema"
        echo "  status   - Ver estado completo del sistema"
        echo "  logs     - Ver logs en tiempo real"
        echo "  devices  - Listar dispositivos MIDI detectados"
        echo ""
        exit 1
        ;;
esac
EOF

sudo chmod +x /usr/local/bin/guitar-midi-modular

echo ""
echo "✅ 9. Habilitando servicio modular..."
sudo systemctl daemon-reload
sudo systemctl enable guitar-midi-modular.service

echo ""
echo "🧪 10. Probando sistema modular (15 segundos)..."
sudo systemctl start guitar-midi-modular.service
sleep 15

if systemctl is-active guitar-midi-modular.service >/dev/null; then
    echo "   ✅ Sistema modular funciona correctamente"
    sudo systemctl stop guitar-midi-modular.service
else
    echo "   ⚠️  Sistema tiene problemas, ver logs: guitar-midi-modular logs"
fi

echo ""
echo "🎉 INSTALACIÓN MODULAR COMPLETADA!"
echo "=================================="
echo ""
echo "🎯 Sistema Guitar-MIDI Modular v2.0 configurado:"
echo "   • Arquitectura multi-controlador ✅"
echo "   • MVAVE Pocket (4 presets percusivos) ✅"
echo "   • Controlador hexafónico (6 canales) ✅"
echo "   • MIDI Captain (control maestro) ✅"
echo "   • Auto-detección de dispositivos ✅"
echo "   • Hot-plug de dispositivos USB ✅"
echo "   • Base de datos SQLite para presets ✅"
echo "   • Interfaz web modular ✅"
echo "   • Audio multi-canal optimizado ✅"
echo "   • Auto-inicio en arranque ✅"
echo "   • Hotspot WiFi propio ✅"
echo ""
echo "🎛️ Control del sistema:"
echo "   guitar-midi-modular start    - Iniciar sistema"
echo "   guitar-midi-modular stop     - Detener sistema"  
echo "   guitar-midi-modular status   - Ver estado completo"
echo "   guitar-midi-modular logs     - Ver logs en tiempo real"
echo "   guitar-midi-modular devices  - Listar dispositivos MIDI"
echo ""
echo "🔄 Para activar completamente:"
echo "   sudo reboot"
echo ""
echo "📱 Después del reinicio (~3 minutos):"
echo "   1. Conectar celular a WiFi 'Guitar-MIDI-Modular'"
echo "   2. Contraseña: guitarmidi2024"
echo "   3. Abrir: http://192.168.4.1:5000"
echo ""
echo "🎸 Controladores soportados:"
echo "   • Conecta tu MVAVE Pocket para presets percusivos"
echo "   • Conecta controlador hexafónico para canales por cuerda"
echo "   • Conecta MIDI Captain para control maestro de presets"
echo ""
echo "🔍 Para verificar estado después del reinicio:"
echo "   guitar-midi-modular status"
echo ""
echo "📁 Archivos del sistema modular:"
echo "   - guitar_midi_modular.py (sistema principal)"
echo "   - guitar_midi_modular.db (base de datos SQLite)"
echo "   - venv_modular/ (entorno Python específico)"
echo ""
echo "🎸 ¡Guitar-MIDI Modular System v2.0 listo!"