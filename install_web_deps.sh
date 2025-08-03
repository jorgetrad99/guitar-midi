#!/bin/bash

# Guitar-MIDI Web Interface - Instalador de dependencias
echo "🎸 Guitar-MIDI Web Interface - Instalando dependencias..."

# Verificar que estamos en un entorno virtual
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Se recomienda usar un entorno virtual"
    echo "💡 Para crear uno: python3 -m venv venv && source venv/bin/activate"
    read -p "¿Continuar sin entorno virtual? (y/N): " continue_anyway
    if [[ $continue_anyway != "y" && $continue_anyway != "Y" ]]; then
        echo "❌ Instalación cancelada"
        exit 1
    fi
fi

echo "📦 Instalando dependencias Flask..."
pip install Flask==2.3.3
pip install Flask-SocketIO==5.3.6
pip install python-socketio==5.9.0
pip install eventlet==0.33.3

echo "📊 Instalando psutil para monitoreo del sistema..."
pip install psutil==5.9.0

echo "🧪 Verificando instalación..."
cd web
python3 -c "
try:
    from flask import Flask
    from flask_socketio import SocketIO
    import psutil
    print('✅ Todas las dependencias instaladas correctamente')
    print('🚀 Para iniciar el servidor: cd web && python3 app.py')
except ImportError as e:
    print(f'❌ Error de importación: {e}')
    print('💡 Intenta: pip install --upgrade Flask Flask-SocketIO psutil')
"

echo "🎉 Instalación completa!"
echo ""
echo "📋 Próximos pasos:"
echo "1. cd web"
echo "2. python3 app.py"
echo "3. Abrir navegador en http://[IP-RASPBERRY]:5000"
echo ""
echo "💡 Tip: Usa 'hostname -I' para obtener la IP de la Raspberry Pi"