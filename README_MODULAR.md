# 🎸 Guitar-MIDI Modular System v2.0

**Sistema modular para múltiples controladores MIDI específicos**

## 🎯 ¿Qué es esto?

Un sistema Guitar-MIDI **completamente modular** que detecta y maneja automáticamente múltiples controladores MIDI específicos, cada uno con sus propios presets, canales y configuración personalizada.

### 🎛️ Controladores Soportados

| Controlador | Función | Presets | Canales | Uso |
|-------------|---------|---------|---------|-----|
| **🥁 MVAVE Pocket** | Percusión | 4 presets de batería | Canal 9 (GM Drums) | Triggers percusivos |
| **🎸 Hexafónico** | Melódico | 6 presets por cuerda | Canales 0-5 | Una cuerda = un canal |
| **🎚️ MIDI Captain** | Control Maestro | 8 configuraciones globales | Canal 15 | Cambio de presets y efectos |

## 🚀 Instalación SÚPER SIMPLE

```bash
cd ~/guitar-midi
chmod +x install_modular.sh
./install_modular.sh
sudo reboot
```

## 🎛️ Uso del Sistema

**Control del sistema:**
```bash
guitar-midi-modular start     # Iniciar sistema modular
guitar-midi-modular stop      # Detener sistema  
guitar-midi-modular status    # Ver estado completo
guitar-midi-modular logs      # Ver logs en tiempo real
guitar-midi-modular devices   # Listar dispositivos MIDI
```

**Acceso móvil:**
1. Conectar a WiFi: `Guitar-MIDI-Modular`
2. Contraseña: `guitarmidi2024`
3. Abrir: http://192.168.4.1:5000

## 🏗️ Arquitectura Modular

```
🎸 Guitar-MIDI Modular System v2.0
├── 🎛️ DeviceManager (detecta controladores automáticamente)
│   ├── 🥁 MVAVEController (4 presets percusivos)
│   ├── 🎸 HexaphonicController (6 cuerdas → canales)  
│   └── 🎚️ MIDICaptainController (control maestro)
├── 🎹 AudioEngine (FluidSynth multi-canal - 32 canales)
├── 🗄️ PresetManager (SQLite con presets por dispositivo)
├── 🔀 MIDIRouter (routing automático por controlador)
└── 🌐 WebInterface (configuración modular por dispositivo)
```

## 📁 Estructura de Archivos

```
guitar-midi/
├── guitar_midi_modular.py        # ← Sistema principal modular
├── install_modular.sh            # ← Instalador único  
├── guitar_midi_modular.db        # ← Base datos SQLite (se crea automáticamente)
├── venv_modular/                 # ← Entorno Python específico
└── README_MODULAR.md             # ← Esta documentación
```

## 🎹 Configuración de Controladores

### 🥁 MVAVE Pocket Controller
- **Función:** Presets percusivos especializados
- **Canal MIDI:** 9 (GM Drums)
- **Presets por defecto:**
  - `0`: Standard Kit 🥁
  - `1`: Rock Kit 🤘  
  - `2`: Electronic Kit 🔊
  - `3`: Jazz Kit 🎷
- **Cambio de presets:** PC 0-3 o notas C2, C#2, D2, D#2

### 🎸 Hexaphonic Controller  
- **Función:** Control melódico por cuerda
- **Canales MIDI:** 0-5 (una cuerda = un canal)
- **Mapeo de cuerdas:**
  - Cuerda E grave → Canal 0 (Bass/Low)
  - Cuerda A → Canal 1 (Strings/Ensemble)
  - Cuerda D → Canal 2 (Synth Lead)
  - Cuerda G → Canal 3 (Brass)
  - Cuerda B → Canal 4 (Reed/Woodwinds)
  - Cuerda E aguda → Canal 5 (Pipe/Flutes)
- **Presets configurables** por canal independiente

### 🎚️ MIDI Captain Controller
- **Función:** Control maestro del sistema
- **Canal MIDI:** 15 (Control)
- **Controles:**
  - PC 0-7: Configuraciones globales del sistema
  - CC 7: Volumen global
  - CC 91: Reverb global
  - CC 93: Chorus global
  - CC 120: PANIC (All Sound Off)

## 🔧 Características Avanzadas

### ✅ **Auto-Detección Inteligente**
- Detecta automáticamente controladores por nombre/patrón
- Hot-plug: reconecta dispositivos USB automáticamente
- Sin configuración manual necesaria

### ✅ **Base de Datos Persistente**
- SQLite integrado para guardar configuraciones
- Presets personalizables por dispositivo
- Backup automático de configuraciones

### ✅ **Multi-Canal Optimizado**
- FluidSynth configurado para 32 canales internos
- Audio routing optimizado por controlador
- Efectos independientes por canal

### ✅ **Interfaz Web Responsive**
- Diseño mobile-first para uso en vivo
- Control en tiempo real por dispositivo
- Editor de presets integrado
- Visualización de estado por controlador

### ✅ **Sistema de Efectos**
- Volumen, reverb, chorus, cutoff, resonance por canal
- Control en tiempo real desde web o MIDI
- Configuración persistente

## 🎵 Casos de Uso

### 🎸 **Guitarrista en Vivo**
1. **MVAVE Pocket en el pie** → Triggers de percusión para acompañamiento
2. **Controlador hexafónico en guitarra** → Cada cuerda toca un instrumento diferente
3. **MIDI Captain en pedalboard** → Cambio rápido entre configuraciones de canción
4. **Celular como interfaz** → Ajustes rápidos entre canciones

### 🎹 **Estudio de Grabación**
1. **Múltiples controladores simultáneos** → Capas de instrumentos complejas
2. **Presets por proyecto** → Configuraciones guardadas automáticamente
3. **Control preciso de efectos** → Cada canal independiente
4. **Routing flexible** → Sin configuración manual de ALSA

### 🎭 **Performance en Vivo**
1. **Configuraciones por canción** → Cambio con un botón
2. **Hot-plug confiable** → Conexión/desconexión sin problemas
3. **Backup automático** → Sin pérdida de configuraciones
4. **Interfaz touch optimizada** → Control fácil en oscuridad

## 🛠️ Solución de Problemas

### **No se detectan dispositivos MIDI:**
```bash
guitar-midi-modular devices
# Ver lista de dispositivos detectados

guitar-midi-modular logs
# Ver logs de detección en tiempo real
```

### **Audio no funciona:**
```bash
guitar-midi-modular status
# Verificar estado del audio engine

pulseaudio --check -v || pulseaudio --start
# Reiniciar PulseAudio si es necesario
```

### **Interfaz web no carga:**
```bash
guitar-midi-modular status
# Verificar IP y estado del servidor

# Acceder directo por IP de la Raspberry Pi
curl http://IP_DE_LA_RASPBERRY:5000
```

### **Controlador no reconocido:**
1. Verificar que el dispositivo aparece en `guitar-midi-modular devices`
2. Si aparece pero no se reconoce, contactar para añadir patrón de detección
3. Los patrones actuales están en el código:
   - MVAVE: `["MVAVE.*Pocket", "Pocket.*MVAVE", "MVAVE.*"]`
   - Hexafónico: `["HEX.*", "Hexaphonic.*", "Guitar.*Synth", ".*Hexaphonic.*"]`
   - MIDI Captain: `[".*Captain.*", "Captain.*", "Pico.*Captain.*", "MIDI.*Captain.*"]`

## 🔄 Migración desde Sistema Anterior

El instalador modular:
- ✅ **Limpia automáticamente** el sistema anterior
- ✅ **Migra configuraciones** existentes cuando es posible
- ✅ **Mantiene hotspot WiFi** con nueva configuración
- ✅ **Preserva datos** importantes automáticamente

## 🚀 Desarrollo y Extensión

### **Añadir Nuevo Controlador:**
1. Crear clase heredando de `MIDIController`
2. Implementar `setup_presets()` y `handle_midi_message()`
3. Registrar en `DeviceManager._register_controllers()`
4. Definir patrones de detección por nombre

### **Personalizar Presets:**
1. Usar interfaz web para edición visual
2. O modificar directamente en base de datos SQLite
3. Exportar/importar configuraciones como JSON

### **Integrar con DAW:**
1. Sistema funciona como sintetizador independiente
2. Salida de audio puede capturarse por cualquier DAW
3. Control MIDI puede integrarse vía ALSA/JACK

---

**🎸 Guitar-MIDI Modular System v2.0**  
*Arquitectura profesional para control MIDI multi-dispositivo en vivo*

**Desarrollado con:**
- Python 3.11+ con asyncio y threading
- FluidSynth 2.4+ para síntesis multi-canal
- Flask + SocketIO para interfaz web en tiempo real
- SQLite para persistencia de configuraciones
- ALSA + PulseAudio para audio de baja latencia
- Diseño mobile-first para uso en vivo