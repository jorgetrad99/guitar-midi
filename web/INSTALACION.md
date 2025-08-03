# 🎸 Guitar-MIDI Web Interface - Guía de Instalación

## 📋 Resumen
Interfaz web móvil para control en tiempo real del sistema Guitar-MIDI. Permite configurar instrumentos, gestionar presets y controlar efectos desde cualquier dispositivo móvil conectado a la misma red WiFi.

## 🛠️ Componentes Completados

### ✅ Backend (Flask + SocketIO)
- **`app.py`**: Servidor principal con rutas y WebSocket
- **`api/midi_controller.py`**: API para control de instrumentos MIDI  
- **`api/presets.py`**: Gestión de presets (guardar/cargar configuraciones)
- **`api/system_info.py`**: Información del sistema y estadísticas

### ✅ Frontend (Mobile-First PWA)
- **Templates HTML**: 
  - `base.html`: Layout base con navegación
  - `index.html`: Control principal con grid de instrumentos
  - `instruments.html`: Editor avanzado de instrumentos con lista GM
  - `presets.html`: Gestor completo de presets con import/export
- **CSS Responsive**: `mobile.css` optimizado para dispositivos móviles
- **JavaScript**:
  - `app.js`: Lógica principal de la aplicación
  - `websocket.js`: Comunicación en tiempo real
- **PWA**: `manifest.json` y `sw.js` para instalación como app nativa

## 📦 Dependencias (Ya agregadas a requirements.txt)
```
Flask==2.3.3
Flask-SocketIO==5.3.6
python-socketio==5.9.0
eventlet==0.33.3
```

## 🚀 Instalación en Raspberry Pi

### 1. Navegar al directorio del proyecto
```bash
cd /path/to/guitar-midi
```

### 2. Activar entorno virtual (si existe)
```bash
source venv/bin/activate  # o el nombre de tu entorno virtual
```

### 3. Instalar dependencias web
```bash
pip install Flask Flask-SocketIO python-socketio eventlet
```

### 4. Verificar instalación
```bash
cd web
python3 test_flask.py  # Script de prueba que creamos
```

### 5. Iniciar servidor
```bash
cd web
python3 app.py
```

El servidor estará disponible en:
- **Local**: http://localhost:5000
- **Red local**: http://[IP-de-la-Raspberry]:5000

## 📱 Uso desde Dispositivos Móviles

### Encontrar la IP de la Raspberry Pi
```bash
hostname -I
```

### Conectar desde móvil
1. Conectar el móvil a la misma red WiFi que la Raspberry Pi
2. Abrir navegador e ir a: `http://[IP-RASPBERRY]:5000`
3. **Opcional**: Agregar a pantalla de inicio para comportamiento de app nativa

### Funcionalidades Disponibles

#### 🎛️ Página Principal (/)
- **Display del instrumento actual** con icono, nombre y detalles técnicos
- **Mapa rápido de pedales (PC 0-7)** para cambio rápido de instrumentos
- **Controles globales**: Volumen Master, Reverb, Chorus
- **Log de actividad MIDI** en tiempo real
- **Botón PANIC** para detener todas las notas
- **Gestión de presets** básica

#### 🎹 Editor de Instrumentos (/instruments)
- **Configuración detallada** por pedal (PC 0-7)
- **Campos editables**: Nombre, Bank MSB/LSB, Program Change, Canal MIDI
- **Lista General MIDI integrada** con búsqueda
- **Función de prueba** para cada instrumento
- **Reset y guardado** masivo

#### 💾 Gestor de Presets (/presets)
- **Crear, editar y eliminar** presets
- **Import/Export** de configuraciones en JSON
- **Búsqueda y filtrado** por nombre, descripción o tags
- **Vista previa** de configuraciones antes de cargar
- **Acciones rápidas**: Guardar estado actual, duplicar, resetear

## 🔧 Configuración del Sistema

### Auto-inicio con systemd (Opcional)
Crear servicio para inicio automático del web server:

```bash
sudo nano /etc/systemd/system/guitar-midi-web.service
```

```ini
[Unit]
Description=Guitar-MIDI Web Interface
After=network.target guitar-midi.service
Requires=guitar-midi.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/guitar-midi/web
Environment=PATH=/home/pi/guitar-midi/venv/bin
ExecStart=/home/pi/guitar-midi/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable guitar-midi-web
sudo systemctl start guitar-midi-web
```

### Configuración de Red
Para acceso desde internet (opcional y solo para redes seguras):
```bash
# En router: Forward puerto 5000 a IP de Raspberry Pi
# Acceso: http://[IP-PUBLICA]:5000
```

## 🔌 Integración con MIDI

### Conexión con midi_listener.py
El web server se conecta automáticamente con el sistema MIDI existente a través de:
- **APIs REST** para cambios de configuración
- **WebSockets** para actualizaciones en tiempo real
- **Archivos JSON** para persistencia de presets

### Flujo de Datos
1. **Usuario** interactúa con la interfaz web móvil
2. **Frontend** envía comandos via WebSocket/HTTP
3. **Flask API** procesa y valida comandos
4. **MIDI Controller** ejecuta cambios en FluidSynth
5. **Actualizaciones** se propagan a todos los clientes conectados

## 🎨 Personalización

### Temas y Colores
Modificar variables CSS en `mobile.css`:
```css
:root {
    --primary-color: #1a1a1a;     /* Fondo principal */
    --accent-color: #4CAF50;      /* Color de acento */
    --danger-color: #f44336;      /* Botones de peligro */
    /* ... más variables */
}
```

### Agregar Instrumentos a la Lista GM
Editar `instruments.html` en la sección modal para agregar más categorías:
```html
<div class="gm-category">
    <h4>Nueva Categoría (X-Y)</h4>
    <div class="gm-list">
        <button class="gm-item" data-pc="X">X - Nuevo Instrumento</button>
        <!-- ... más instrumentos -->
    </div>
</div>
```

## 🐛 Troubleshooting

### Error: "Module not found"
```bash
# Verificar que las dependencias estén instaladas
pip list | grep -i flask

# Reinstalar si es necesario
pip install --upgrade Flask Flask-SocketIO
```

### Error: "Address already in use"
```bash
# Encontrar proceso usando puerto 5000
sudo lsof -i :5000

# Terminar proceso si es necesario
sudo kill -9 [PID]
```

### No se conecta desde móvil
```bash
# Verificar firewall
sudo ufw status
sudo ufw allow 5000

# Verificar que el servidor esté escuchando en todas las interfaces
netstat -tulnp | grep :5000
```

### WebSocket no conecta
- Verificar que el navegador soporte WebSockets
- Revisar consola del navegador para errores
- Probar con HTTP en lugar de HTTPS si hay problemas de certificados

## 📈 Próximas Mejoras
- [ ] Configuración WiFi hotspot para independencia de red
- [ ] Grabación y reproducción de secuencias MIDI
- [ ] Control de pedales de expresión en tiempo real
- [ ] Sincronización con metrónomos externos
- [ ] Backup automático en la nube

## 🆘 Soporte
Para problemas o mejoras, revisar:
1. Los logs del servidor Flask en consola
2. La consola del navegador (F12) para errores de frontend
3. El archivo `CLAUDE.md` para contexto del proyecto completo