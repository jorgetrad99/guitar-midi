#!/bin/bash

# Guitar-MIDI Hotspot Setup
# Configura la Raspberry Pi como punto de acceso WiFi independiente

echo "🎸 Guitar-MIDI Hotspot Setup"
echo "============================="
echo ""
echo "Este script configurará tu Raspberry Pi como un hotspot WiFi"
echo "para que puedas conectarte directamente desde tu celular"
echo ""

# Verificar si es root o pedir sudo
if [[ $EUID -eq 0 ]]; then
   echo "⚠️  Este script no debe ejecutarse como root"
   echo "💡 Ejecuta: ./setup_hotspot.sh (sin sudo)"
   exit 1
fi

# Configuración del hotspot
HOTSPOT_NAME="Guitar-MIDI"
HOTSPOT_PASSWORD="guitarmidi2024"
HOTSPOT_IP="192.168.4.1"
DHCP_RANGE_START="192.168.4.2"
DHCP_RANGE_END="192.168.4.20"

echo "📋 Configuración del hotspot:"
echo "   Nombre WiFi: $HOTSPOT_NAME"
echo "   Contraseña: $HOTSPOT_PASSWORD"
echo "   IP del servidor: $HOTSPOT_IP"
echo "   URL para acceder: http://$HOTSPOT_IP:5000"
echo ""

read -p "¿Continuar con la instalación? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Instalación cancelada"
    exit 1
fi

echo ""
echo "🔧 Iniciando configuración..."

# 1. Actualizar sistema
echo "📦 1. Actualizando sistema..."
sudo apt update

# 2. Instalar hostapd y dnsmasq
echo "📡 2. Instalando software de hotspot..."
sudo apt install -y hostapd dnsmasq

# 3. Detener servicios para configurar
echo "⏸️  3. Deteniendo servicios para configuración..."
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq

# 4. Configurar hostapd
echo "🔧 4. Configurando hostapd..."
sudo tee /etc/hostapd/hostapd.conf > /dev/null << EOF
# Guitar-MIDI Hotspot Configuration
interface=wlan0
driver=nl80211
ssid=$HOTSPOT_NAME
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$HOTSPOT_PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# 5. Configurar dnsmasq
echo "🌐 5. Configurando DHCP..."
sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup
sudo tee /etc/dnsmasq.conf > /dev/null << EOF
# Guitar-MIDI DHCP Configuration
interface=wlan0
dhcp-range=$DHCP_RANGE_START,$DHCP_RANGE_END,255.255.255.0,24h

# DNS entries for easy access
address=/guitar-midi.local/$HOTSPOT_IP
address=/control.local/$HOTSPOT_IP
address=/guitarmidi/$HOTSPOT_IP
EOF

# 6. Configurar interfaz de red
echo "🔌 6. Configurando interfaz de red..."
sudo tee -a /etc/dhcpcd.conf > /dev/null << EOF

# Guitar-MIDI Hotspot static IP
interface wlan0
static ip_address=$HOTSPOT_IP/24
nohook wpa_supplicant
EOF

# 7. Habilitar IP forwarding (opcional para futuro)
echo "🔄 7. Habilitando IP forwarding..."
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf

# 8. Configurar hostapd daemon
echo "⚙️  8. Configurando daemon hostapd..."
sudo sed -i 's/#DAEMON_CONF=""/DAEMON_CONF="\/etc\/hostapd\/hostapd.conf"/g' /etc/default/hostapd

# 9. Habilitar servicios
echo "✅ 9. Habilitando servicios..."
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

# 10. Crear script de control del hotspot
echo "📝 10. Creando scripts de control..."

# Script para activar hotspot
sudo tee /usr/local/bin/guitar-midi-hotspot-start > /dev/null << 'EOF'
#!/bin/bash
echo "🔥 Activando Guitar-MIDI Hotspot..."
sudo systemctl start hostapd
sudo systemctl start dnsmasq
echo "✅ Hotspot activo"
echo "📡 Red WiFi: Guitar-MIDI"
echo "🔑 Contraseña: guitarmidi2024"
echo "🌐 URL: http://192.168.4.1:5000"
EOF

# Script para desactivar hotspot
sudo tee /usr/local/bin/guitar-midi-hotspot-stop > /dev/null << 'EOF'
#!/bin/bash
echo "⏹️  Desactivando Guitar-MIDI Hotspot..."
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
echo "✅ Hotspot desactivado"
EOF

# Script para estado del hotspot
sudo tee /usr/local/bin/guitar-midi-hotspot-status > /dev/null << 'EOF'
#!/bin/bash
echo "📊 Estado del Guitar-MIDI Hotspot:"
echo "=================================="
echo ""
echo "🔧 Servicios:"
systemctl is-active --quiet hostapd && echo "   hostapd: ✅ ACTIVO" || echo "   hostapd: ❌ INACTIVO"
systemctl is-active --quiet dnsmasq && echo "   dnsmasq: ✅ ACTIVO" || echo "   dnsmasq: ❌ INACTIVO"
echo ""
echo "🌐 Configuración de red:"
ip addr show wlan0 | grep "inet " && echo "   IP configurada: ✅" || echo "   IP: ❌ NO CONFIGURADA"
echo ""
echo "📱 Dispositivos conectados:"
cat /var/lib/dhcp/dhcpd.leases 2>/dev/null | grep "binding state active" | wc -l | xargs echo "   Clientes: "
echo ""
echo "💡 Comandos útiles:"
echo "   Activar:    guitar-midi-hotspot-start"
echo "   Desactivar: guitar-midi-hotspot-stop"
echo "   Estado:     guitar-midi-hotspot-status"
EOF

sudo chmod +x /usr/local/bin/guitar-midi-hotspot-*

# 11. Crear script integrado para Guitar-MIDI
cat > ~/guitar-midi/start_complete_system.sh << 'EOF'
#!/bin/bash

echo "🎸 Guitar-MIDI Complete System Startup"
echo "======================================"

# 1. Activar hotspot
echo "📡 1. Activando hotspot WiFi..."
sudo /usr/local/bin/guitar-midi-hotspot-start

# 2. Esperar a que la red esté lista
echo "⏳ 2. Esperando a que la red esté lista..."
sleep 5

# 3. Activar entorno virtual si existe
if [ -d ~/guitar-midi/venv ]; then
    echo "🐍 3. Activando entorno virtual..."
    source ~/guitar-midi/venv/bin/activate
fi

# 4. Iniciar sistema MIDI
echo "🎹 4. Iniciando sistema MIDI..."
cd ~/guitar-midi/scripts
python3 midi_listener.py &
MIDI_PID=$!

# 5. Iniciar servidor web
echo "🌐 5. Iniciando servidor web..."
cd ~/guitar-midi/web

echo ""
echo "🎯 SISTEMA GUITAR-MIDI LISTO!"
echo "============================="
echo ""
echo "📡 Red WiFi disponible:"
echo "   Nombre: Guitar-MIDI"
echo "   Contraseña: guitarmidi2024"
echo ""
echo "📱 Para conectar desde tu celular:"
echo "   1. Conectar a WiFi 'Guitar-MIDI'"
echo "   2. Abrir navegador"
echo "   3. Ir a: http://192.168.4.1:5000"
echo "   4. O también: http://guitar-midi.local:5000"
echo ""
echo "🔴 Presiona Ctrl+C para detener todo el sistema"
echo ""

# Trap para limpiar al salir
trap 'echo ""; echo "🛑 Deteniendo sistema..."; kill $MIDI_PID 2>/dev/null; sudo /usr/local/bin/guitar-midi-hotspot-stop; exit' INT TERM

# Iniciar Flask
python3 app.py
EOF

chmod +x ~/guitar-midi/start_complete_system.sh

# 12. Información final
echo ""
echo "🎉 CONFIGURACIÓN COMPLETADA!"
echo "============================="
echo ""
echo "📋 Resumen de la configuración:"
echo "   Red WiFi: $HOTSPOT_NAME"
echo "   Contraseña: $HOTSPOT_PASSWORD"
echo "   IP del servidor: $HOTSPOT_IP"
echo "   URL de acceso: http://$HOTSPOT_IP:5000"
echo ""
echo "🔄 IMPORTANTE: Es necesario reiniciar la Raspberry Pi"
echo "   sudo reboot"
echo ""
echo "📱 Después del reinicio, para usar el sistema:"
echo "   ~/guitar-midi/start_complete_system.sh"
echo ""
echo "🛠️  Comandos de control del hotspot:"
echo "   Activar:    guitar-midi-hotspot-start"
echo "   Desactivar: guitar-midi-hotspot-stop"
echo "   Estado:     guitar-midi-hotspot-status"
echo ""
echo "🎯 Flujo de uso:"
echo "   1. Encender Raspberry Pi"
echo "   2. Ejecutar: ~/guitar-midi/start_complete_system.sh"
echo "   3. En el celular: conectar a WiFi 'Guitar-MIDI'"
echo "   4. Abrir navegador: http://192.168.4.1:5000"
echo ""
echo "¡Ya tienes tu sistema Guitar-MIDI completamente portátil! 🎸📱"