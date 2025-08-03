#!/bin/bash

# Configuración simple de hotspot para Guitar-MIDI
echo "🔥 Guitar-MIDI Hotspot Simple Setup"
echo "===================================="
echo ""
echo "Este script crea una red WiFi simple para tu Raspberry Pi"
echo ""

# Parámetros
SSID="Guitar-MIDI"
PASSWORD="guitarmidi2024"
IP="192.168.4.1"

echo "📋 Configuración:"
echo "   Red WiFi: $SSID" 
echo "   Contraseña: $PASSWORD"
echo "   IP: $IP"
echo "   URL: http://$IP:5000"
echo ""

read -p "¿Instalar? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Instalar hostapd y dnsmasq
echo "📦 Instalando software..."
sudo apt update
sudo apt install -y hostapd dnsmasq

# Configurar hostapd
echo "🔧 Configurando WiFi..."
sudo tee /etc/hostapd/hostapd.conf > /dev/null << EOF
interface=wlan0
driver=nl80211
ssid=$SSID
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Configurar dnsmasq
echo "🌐 Configurando DHCP..."
sudo tee /etc/dnsmasq.conf > /dev/null << EOF
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
EOF

# Configurar IP estática
echo "🔌 Configurando IP..."
sudo tee -a /etc/dhcpcd.conf > /dev/null << EOF

# Guitar-MIDI Hotspot
interface wlan0
static ip_address=$IP/24
nohook wpa_supplicant
EOF

# Habilitar servicios
echo "✅ Habilitando servicios..."
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

# Configurar hostapd daemon
sudo sed -i 's/#DAEMON_CONF=""/DAEMON_CONF="\/etc\/hostapd\/hostapd.conf"/g' /etc/default/hostapd

# Crear comando de inicio rápido
cat > ~/start-guitar-midi.sh << 'EOF'
#!/bin/bash
echo "🎸 Iniciando Guitar-MIDI System..."

# Activar hotspot
sudo systemctl start hostapd
sudo systemctl start dnsmasq

# Activar entorno virtual
if [ -d ~/guitar-midi/venv ]; then
    source ~/guitar-midi/venv/bin/activate
fi

# Ir al directorio web
cd ~/guitar-midi/web

echo ""
echo "🎯 GUITAR-MIDI LISTO!"
echo "===================="
echo ""
echo "📡 WiFi: Guitar-MIDI"
echo "🔑 Contraseña: guitarmidi2024" 
echo "📱 URL: http://192.168.4.1:5000"
echo ""
echo "🔴 Ctrl+C para detener"
echo ""

# Iniciar servidor
python3 app.py
EOF

chmod +x ~/start-guitar-midi.sh

echo ""
echo "🎉 INSTALACIÓN COMPLETA!"
echo "========================"
echo ""
echo "🔄 Reinicia la Raspberry Pi:"
echo "   sudo reboot"
echo ""
echo "📱 Después del reinicio:"
echo "   1. Ejecutar: ~/start-guitar-midi.sh"
echo "   2. En tu celular: conectar a WiFi 'Guitar-MIDI'"
echo "   3. Abrir navegador: http://192.168.4.1:5000"
echo ""
echo "¡Ya tienes tu propio WiFi Guitar-MIDI! 🎸📱"