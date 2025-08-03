# 🎸 Guitar-MIDI System - Setup Completo
## Sistema Plug & Play para Raspberry Pi 4 + DietPi

---

## 📋 **Resumen del Sistema**

**Hardware:**
- Raspberry Pi 4 con DietPi
- MIDI Captain Foot Controller (USB)
- Akai MPK Mini (USB) o cualquier controlador MIDI
- Salida de audio por jack 3.5mm

**Software:**
- Python con FluidSynth + pyfluidsynth
- Auto-inicio con systemd
- Detección automática de dispositivos MIDI
- 8 instrumentos mapeados (Piano, Drums, Bass, Guitar, Saxophone, Strings, Organ, Flute)

---

## 🛠️ **Instalación Base**

### **1. Dependencias del sistema:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv fluidsynth fluid-soundfont-gm
```

### **2. Crear proyecto:**
```bash
cd /root
git clone [tu-repo] guitar-midi
cd guitar-midi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **3. requirements.txt:**
```
numpy==2.3.2
pyfluidsynth==1.3.4
pygame==2.6.1
python-rtmidi==1.5.8
```

---

## 🔊 **Configuración de Audio**

### **1. Configurar salida por jack 3.5mm:**
```bash
# Activar audio (unmute)
sudo amixer cset numid=2 on

# Volumen al 100%
sudo amixer cset numid=1 100%

# Verificar configuración
amixer
```

### **2. Amplificar volumen (si está bajo):**
```bash
# Instalar PulseAudio
sudo apt install pulseaudio

# Amplificar al 150%
pulseaudio --start
pactl set-sink-volume 0 150%
```

---

## 🎹 **Script Principal MIDI**

### **Archivo: `scripts/midi_listener.py`**
- Detecta automáticamente todos los dispositivos MIDI conectados
- Mapeo de instrumentos via Program Change (PC 0-7)
- Configuración optimizada de FluidSynth con ganancia 2x
- Manejo de múltiples dispositivos simultáneamente

### **Mapeo de Instrumentos:**
- **PC 0**: Piano
- **PC 1**: Drums (Bank 128)
- **PC 2**: Bass
- **PC 3**: Guitar
- **PC 4**: Saxophone
- **PC 5**: Strings
- **PC 6**: Organ
- **PC 7**: Flute

---

## 🚀 **Auto-inicio del Sistema**

### **1. Script de inicio: `scripts/start_guitar_midi.sh`**
```bash
#!/bin/bash
# Auto-inicio del sistema Guitar-MIDI
# Para uso en vivo - Plug and Play

echo "🎸 Iniciando sistema Guitar-MIDI..."

# Esperar a que el sistema termine de cargar completamente
echo "⏳ Esperando estabilización del sistema..."
sleep 10

# Configurar audio automáticamente
echo "🔊 Configurando audio..."
amixer cset numid=2 on > /dev/null 2>&1  # Unmute
amixer cset numid=1 100% > /dev/null 2>&1 # Volumen 100%

# Esperar a que los dispositivos USB se detecten
echo "🔌 Esperando dispositivos USB MIDI..."
sleep 5

# Ir al directorio del proyecto
cd /root/guitar-midi

# Activar entorno virtual
source venv/bin/activate

# Ejecutar el sistema MIDI
echo "🎹 Iniciando sistema MIDI..."
echo "✅ Sistema listo para tocar en vivo!"
echo ""

# Ejecutar el script principal
python scripts/midi_listener.py
```

### **2. Servicio de Audio: `/etc/systemd/system/guitar-midi-audio.service`**
```ini
[Unit]
Description=Guitar MIDI Audio Setup
After=sound.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/bash -c 'amixer cset numid=2 on && amixer cset numid=1 100%'
User=root

[Install]
WantedBy=multi-user.target
```

### **3. Servicio Principal: `/etc/systemd/system/guitar-midi.service`**
```ini
[Unit]
Description=Guitar MIDI System
After=multi-user.target network.target sound.target
Wants=guitar-midi-audio.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/guitar-midi
ExecStart=/root/guitar-midi/scripts/start_guitar_midi.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### **4. Activar servicios:**
```bash
chmod +x /root/guitar-midi/scripts/start_guitar_midi.sh
sudo systemctl daemon-reload
sudo systemctl enable guitar-midi-audio.service
sudo systemctl enable guitar-midi.service
```

---

## ⚡ **Problemas Conocidos**

### **🔧 SOLUCIONADO: Arranque con múltiples dispositivos USB**
- **Problema:** Raspberry Pi no arranca con múltiples dispositivos USB MIDI conectados
- **Solución aplicada:** Configuración de boot_delay en config.txt y parámetros USB en cmdline.txt
- **Estado:** ✅ Funcionando

### **⚠️ PENDIENTE: Arranque automático con 2 USBs**
- **Problema actual:** Después de optimizaciones de latencia, el arranque con ambos dispositivos USB conectados dejó de funcionar consistentemente
- **Workaround temporal:** Conectar un dispositivo durante el arranque, luego conectar el segundo
- **Solución pendiente:** Revisar y ajustar parámetros de arranque USB para mayor estabilidad

### **Configuración actual en `/boot/firmware/config.txt`:**
```ini
# Configuración USB MIDI para múltiples dispositivos
boot_delay=4
boot_delay_ms=2000
bootcode_delay=2
```

### **Configuración actual en `/boot/firmware/cmdline.txt`:**
```
rootdelay=10 usbcore.old_scheme_first=1 usbcore.initial_descriptor_timeout=10000 usb-storage.delay_use=8
```

### **Para mayor estabilidad (si el problema persiste):**
- Aumentar `boot_delay=8` y `boot_delay_ms=4000`
- Aumentar `rootdelay=15`
- Usar hub USB con alimentación externa

---

## 🖥️ **Problema de Audio con Desktop**

### **Problema:** El audio se corta cuando carga la interfaz gráfica

### **Solución:** Configurar DietPi para arrancar sin desktop
```bash
sudo dietpi-autostart
# Seleccionar: Console (opción 7)
```

---

## 🧪 **Verificación del Sistema**

### **1. Probar audio:**
```bash
speaker-test -t wav -c 1 -l 1
```

### **2. Verificar dispositivos MIDI:**
```bash
aconnect -l
# o
python -c "import rtmidi; print(rtmidi.MidiIn().get_ports())"
```

### **3. Estado de servicios:**
```bash
sudo systemctl status guitar-midi.service
sudo systemctl status guitar-midi-audio.service
```

### **4. Ver logs:**
```bash
sudo journalctl -u guitar-midi.service --no-pager
```

---

## 🎯 **Flujo de Uso en Vivo**

### **Arranque:**
1. Conectar MIDI Captain y controlador MIDI a USB
2. Encender Raspberry Pi
3. Esperar 2-3 minutos para auto-inicio completo
4. Sistema listo automáticamente

### **Operación:**
1. **MIDI Captain** → Cambiar instrumentos (pedales configurados para PC 0-7)
2. **Akai/Controlador** → Tocar notas del instrumento actual
3. **Audio** → Salida automática por jack 3.5mm

### **Indicadores visuales:**
- `🦶 [Puerto X]` - Mensaje del controlador de pedales
- `🎹 [Puerto Y]` - Mensaje del teclado/controlador
- `🎹 Instrumento cambiado a: [Nombre]` - Confirmación de cambio

---

## 📁 **Estructura de Archivos**

```
/root/guitar-midi/
├── scripts/
│   ├── midi_listener.py           # Script principal MIDI
│   └── start_guitar_midi.sh       # Script de auto-inicio
├── context/
│   └── CLAUDE.md                  # Contexto del proyecto
├── requirements.txt               # Dependencias Python
├── README.md                      # Documentación del proyecto
└── SETUP_COMPLETO.md             # Esta documentación
```

---

## 🔧 **Comandos de Mantenimiento**

### **Reiniciar servicio:**
```bash
sudo systemctl restart guitar-midi.service
```

### **Ver estado en tiempo real:**
```bash
sudo systemctl status guitar-midi.service -f
```

### **Deshabilitar auto-inicio:**
```bash
sudo systemctl disable guitar-midi.service
```

### **Ejecutar manualmente:**
```bash
cd /root/guitar-midi
./scripts/start_guitar_midi.sh
```

---

## ✅ **Sistema Plug & Play Listo**

Una vez configurado, el sistema es completamente autónomo:
- ✅ Arranque automático al encender (~45 segundos)
- ✅ Detección automática de dispositivos MIDI
- ✅ Audio configurado automáticamente
- ✅ Sin comandos manuales necesarios
- ✅ Listo para uso en vivo

**Flujo de uso actual:** 
1. Enchufar Raspberry Pi con UN dispositivo USB
2. Esperar 45 segundos
3. Conectar segundo dispositivo USB
4. ¡Listo para tocar! 🎸

**Flujo ideal (pendiente):** Enchufar ambos USB → Esperar 45 segundos → Tocar 🎸