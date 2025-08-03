#!/bin/bash

# Instalador de auto-inicio para Guitar-MIDI
echo "🎸 Guitar-MIDI Auto-Start Setup"
echo "==============================="

# Verificar que estamos en el directorio correcto
if [ ! -f "scripts/midi_engine.py" ]; then
    echo "❌ Error: Ejecutar desde el directorio guitar-midi"
    echo "💡 Uso: cd ~/guitar-midi && ./install_autostart.sh"
    exit 1
fi

# Obtener directorio actual absoluto
GUITAR_MIDI_DIR=$(pwd)
USER=$(whoami)

echo "📋 Configuración:"
echo "   Directorio: $GUITAR_MIDI_DIR"
echo "   Usuario: $USER"
echo "   Servicio: guitar-midi-complete.service"
echo ""

read -p "¿Instalar auto-inicio? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Instalación cancelada"
    exit 1
fi

# 1. Crear script de inicio del sistema
echo "📝 1. Creando script de inicio del sistema..."
cat > /tmp/guitar-midi-start.sh << EOF
#!/bin/bash

# Guitar-MIDI Complete System Auto-Start
echo "\$(date): 🎸 Iniciando Guitar-MIDI Complete System..." >> /var/log/guitar-midi.log

# Cambiar al directorio del proyecto
cd $GUITAR_MIDI_DIR

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Función de limpieza
cleanup() {
    echo "\$(date): 🛑 Deteniendo Guitar-MIDI..." >> /var/log/guitar-midi.log
    
    # Terminar procesos hijos
    pkill -P \$\$
    
    # Limpiar archivos temporales
    rm -f /tmp/guitar_midi_*.json 2>/dev/null
    
    exit 0
}

# Configurar trap
trap cleanup INT TERM

# Esperar a que la red esté lista
echo "\$(date): ⏳ Esperando red..." >> /var/log/guitar-midi.log
sleep 10

# Activar hotspot si está configurado
if systemctl is-enabled hostapd >/dev/null 2>&1; then
    echo "\$(date): 📡 Activando hotspot..." >> /var/log/guitar-midi.log
    systemctl start hostapd
    systemctl start dnsmasq
    sleep 5
fi

# Obtener IP
IP=\$(ip addr show wlan0 2>/dev/null | grep "inet " | awk '{print \$2}' | cut -d'/' -f1)
if [ -z "\$IP" ]; then
    IP=\$(hostname -I | awk '{print \$1}')
fi

echo "\$(date): 🌐 IP del servidor: \$IP" >> /var/log/guitar-midi.log

# Iniciar MIDI Engine
echo "\$(date): 🎹 Iniciando MIDI Engine..." >> /var/log/guitar-midi.log
cd scripts
python3 midi_engine.py &
MIDI_PID=\$!
cd ..

# Esperar inicialización
sleep 5

# Verificar MIDI Engine
if ! kill -0 \$MIDI_PID 2>/dev/null; then
    echo "\$(date): ❌ Error: MIDI Engine falló" >> /var/log/guitar-midi.log
    exit 1
fi

echo "\$(date): ✅ MIDI Engine iniciado (PID: \$MIDI_PID)" >> /var/log/guitar-midi.log

# Iniciar Flask
echo "\$(date): 🌐 Iniciando servidor web..." >> /var/log/guitar-midi.log
cd web
python3 app.py &
FLASK_PID=\$!
cd ..

# Esperar inicialización
sleep 3

# Verificar Flask
if ! kill -0 \$FLASK_PID 2>/dev/null; then
    echo "\$(date): ❌ Error: Flask falló" >> /var/log/guitar-midi.log
    kill \$MIDI_PID 2>/dev/null
    exit 1
fi

echo "\$(date): ✅ Flask iniciado (PID: \$FLASK_PID)" >> /var/log/guitar-midi.log
echo "\$(date): 🎯 Guitar-MIDI sistema listo en http://\$IP:5000" >> /var/log/guitar-midi.log

# Monitorear procesos
while true; do
    if ! kill -0 \$MIDI_PID 2>/dev/null; then
        echo "\$(date): ❌ MIDI Engine se detuvo" >> /var/log/guitar-midi.log
        kill \$FLASK_PID 2>/dev/null
        exit 1
    fi
    
    if ! kill -0 \$FLASK_PID 2>/dev/null; then
        echo "\$(date): ❌ Flask se detuvo" >> /var/log/guitar-midi.log
        kill \$MIDI_PID 2>/dev/null
        exit 1
    fi
    
    sleep 30
done
EOF

# Instalar script con permisos correctos
sudo mv /tmp/guitar-midi-start.sh /usr/local/bin/guitar-midi-start.sh
sudo chmod +x /usr/local/bin/guitar-midi-start.sh
sudo chown root:root /usr/local/bin/guitar-midi-start.sh

echo "   ✅ Script de inicio creado"

# 2. Crear servicio systemd
echo "📝 2. Creando servicio systemd..."
sudo tee /etc/systemd/system/guitar-midi-complete.service > /dev/null << EOF
[Unit]
Description=Guitar-MIDI Complete System (MIDI Engine + Web Interface)
After=network.target sound.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$GUITAR_MIDI_DIR
Environment=HOME=/home/$USER
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/$USER/.local/bin
ExecStart=/usr/local/bin/guitar-midi-start.sh
Restart=always
RestartSec=10
StandardOutput=append:/var/log/guitar-midi.log
StandardError=append:/var/log/guitar-midi.log

# Límites de recursos
MemoryMax=512M
CPUQuota=80%

# Timeout configurations
TimeoutStartSec=60
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
EOF

echo "   ✅ Servicio systemd creado"

# 3. Configurar log
echo "📝 3. Configurando logs..."
sudo touch /var/log/guitar-midi.log
sudo chown $USER:$USER /var/log/guitar-midi.log
sudo chmod 644 /var/log/guitar-midi.log

echo "   ✅ Sistema de logs configurado"

# 4. Deshabilitar servicio anterior si existe
echo "🔄 4. Verificando servicios anteriores..."
if systemctl is-enabled guitar-midi.service >/dev/null 2>&1; then
    echo "   Deshabilitando servicio anterior..."
    sudo systemctl disable guitar-midi.service
    sudo systemctl stop guitar-midi.service 2>/dev/null
fi

if systemctl is-enabled guitar-midi-web.service >/dev/null 2>&1; then
    echo "   Deshabilitando servicio web anterior..."
    sudo systemctl disable guitar-midi-web.service
    sudo systemctl stop guitar-midi-web.service 2>/dev/null
fi

echo "   ✅ Servicios anteriores limpiados"

# 5. Habilitar y configurar nuevo servicio
echo "⚙️  5. Habilitando servicio..."
sudo systemctl daemon-reload
sudo systemctl enable guitar-midi-complete.service

echo "   ✅ Servicio habilitado para auto-inicio"

# 6. Crear comandos de control
echo "📝 6. Creando comandos de control..."

# Comando para iniciar manualmente
sudo tee /usr/local/bin/guitar-midi-start > /dev/null << 'EOF'
#!/bin/bash
echo "🎸 Iniciando Guitar-MIDI Complete System..."
sudo systemctl start guitar-midi-complete.service
echo "✅ Sistema iniciado"
echo "📊 Para ver estado: guitar-midi-status"
EOF

# Comando para detener
sudo tee /usr/local/bin/guitar-midi-stop > /dev/null << 'EOF'
#!/bin/bash
echo "🛑 Deteniendo Guitar-MIDI Complete System..."
sudo systemctl stop guitar-midi-complete.service
echo "✅ Sistema detenido"
EOF

# Comando para ver estado
sudo tee /usr/local/bin/guitar-midi-status > /dev/null << 'EOF'
#!/bin/bash
echo "📊 Guitar-MIDI Complete System Status"
echo "====================================="
echo ""

# Estado del servicio
echo "🔧 Servicio systemd:"
systemctl is-active guitar-midi-complete.service >/dev/null 2>&1 && echo "   ✅ ACTIVO" || echo "   ❌ INACTIVO"
echo ""

# Estado de los procesos
echo "🎹 Procesos:"
MIDI_PROC=$(pgrep -f "midi_engine.py")
FLASK_PROC=$(pgrep -f "app.py")

if [ ! -z "$MIDI_PROC" ]; then
    echo "   MIDI Engine: ✅ EJECUTÁNDOSE (PID: $MIDI_PROC)"
else
    echo "   MIDI Engine: ❌ NO EJECUTÁNDOSE"
fi

if [ ! -z "$FLASK_PROC" ]; then
    echo "   Flask Web: ✅ EJECUTÁNDOSE (PID: $FLASK_PROC)"
else
    echo "   Flask Web: ❌ NO EJECUTÁNDOSE"
fi

echo ""

# IP del sistema
echo "🌐 Acceso de red:"
IP=$(ip addr show wlan0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
if [ -z "$IP" ]; then
    IP=$(hostname -I | awk '{print $1}')
fi

if [ ! -z "$IP" ]; then
    echo "   IP: $IP"
    echo "   URL: http://$IP:5000"
    echo "   URL Simple: http://$IP:5000/simple"
else
    echo "   ⚠️  IP no disponible"
fi

echo ""
echo "📋 Comandos útiles:"
echo "   guitar-midi-start   - Iniciar sistema"
echo "   guitar-midi-stop    - Detener sistema"
echo "   guitar-midi-logs    - Ver logs"
echo "   guitar-midi-restart - Reiniciar sistema"
EOF

# Comando para ver logs
sudo tee /usr/local/bin/guitar-midi-logs > /dev/null << 'EOF'
#!/bin/bash
echo "📋 Guitar-MIDI Logs (Ctrl+C para salir)"
echo "======================================="
tail -f /var/log/guitar-midi.log
EOF

# Comando para reiniciar
sudo tee /usr/local/bin/guitar-midi-restart > /dev/null << 'EOF'
#!/bin/bash
echo "🔄 Reiniciando Guitar-MIDI Complete System..."
sudo systemctl restart guitar-midi-complete.service
echo "✅ Sistema reiniciado"
echo "📊 Para ver estado: guitar-midi-status"
EOF

# Hacer ejecutables los comandos
sudo chmod +x /usr/local/bin/guitar-midi-*

echo "   ✅ Comandos de control creados"

# 7. Información final
echo ""
echo "🎉 AUTO-INICIO CONFIGURADO EXITOSAMENTE!"
echo "========================================"
echo ""
echo "📋 Servicio creado:"
echo "   Nombre: guitar-midi-complete.service"
echo "   Estado: Habilitado para auto-inicio"
echo "   Logs: /var/log/guitar-midi.log"
echo ""
echo "🎛️ Comandos disponibles:"
echo "   guitar-midi-start    - Iniciar manualmente"
echo "   guitar-midi-stop     - Detener sistema"
echo "   guitar-midi-status   - Ver estado"
echo "   guitar-midi-restart  - Reiniciar sistema"
echo "   guitar-midi-logs     - Ver logs en tiempo real"
echo ""
echo "🔄 Para que tome efecto:"
echo "   sudo reboot"
echo ""
echo "📱 Después del reinicio, el sistema estará disponible en:"
echo "   http://[IP-RASPBERRY]:5000/simple"
echo ""
echo "🎯 Flujo de uso automático:"
echo "   1. Encender Raspberry Pi"
echo "   2. Esperar ~2 minutos"
echo "   3. Conectar celular a WiFi 'Guitar-MIDI'"
echo "   4. Abrir http://192.168.4.1:5000/simple"
echo "   5. ¡Tocar!"