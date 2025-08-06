#!/usr/bin/env python3
"""
🔍 Debug MIDI Connections - Verificar conexiones ALSA
"""

import subprocess
import time

def check_midi_connections():
    print("🔍 Verificando conexiones MIDI ALSA...")
    
    try:
        # Ver todas las conexiones actuales
        result = subprocess.run(['aconnect', '-l'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Error ejecutando aconnect -l")
            return
        
        print("\n📋 TODOS los clientes MIDI:")
        print("="*50)
        
        controllers = []
        fluidsynth_clients = []
        
        for line in result.stdout.split('\n'):
            if line.strip():
                print(line)
                
                # Identificar controladores
                if 'client' in line and any(keyword in line.lower() for keyword in ['pico', 'captain', 'mpk', 'akai', 'mvave']):
                    try:
                        client_num = line.split('client ')[1].split(':')[0]
                        device_name = line.split("'")[1] if "'" in line else line.split(':')[1].strip()
                        controllers.append((client_num, device_name))
                        print(f"   🎛️ CONTROLADOR: {device_name} (cliente {client_num})")
                    except:
                        pass
                
                # Identificar FluidSynth
                if 'FLUID' in line and 'Synth input' in line:
                    try:
                        client_num = line.split('client ')[1].split(':')[0]
                        fluidsynth_clients.append(client_num)
                        print(f"   🎹 FLUIDSYNTH: cliente {client_num}")
                    except:
                        pass
        
        print("\n" + "="*50)
        print(f"📊 Encontrados: {len(controllers)} controladores, {len(fluidsynth_clients)} FluidSynth")
        
        # Mostrar conexiones actuales
        print("\n🔗 CONEXIONES ACTUALES:")
        result2 = subprocess.run(['aconnect', '-l'], capture_output=True, text=True)
        
        connected_pairs = []
        for line in result2.stdout.split('\n'):
            if 'Connected From:' in line or 'Connecting To:' in line:
                print(f"   {line.strip()}")
        
        return controllers, fluidsynth_clients
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return [], []

def force_connections():
    print("\n🔧 FORZANDO CONEXIONES...")
    
    controllers, fluidsynth_clients = check_midi_connections()
    
    if not controllers:
        print("❌ No se encontraron controladores MIDI")
        return
    
    if not fluidsynth_clients:
        print("❌ No se encontró FluidSynth")
        return
    
    # Conectar cada controlador a FluidSynth
    for controller_client, controller_name in controllers:
        for fluidsynth_client in fluidsynth_clients:
            try:
                # Desconectar primero (por si ya está conectado)
                subprocess.run(['aconnect', '-d', f'{controller_client}:0', f'{fluidsynth_client}:0'], 
                             capture_output=True)
                
                # Conectar
                cmd = ['aconnect', f'{controller_client}:0', f'{fluidsynth_client}:0']
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ CONECTADO: {controller_name} ({controller_client}) → FluidSynth ({fluidsynth_client})")
                else:
                    print(f"❌ Error conectando {controller_name}: {result.stderr.strip()}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
    
    print("\n🔍 Verificando conexiones finales...")
    time.sleep(1)
    check_connections_summary()

def check_connections_summary():
    """Verificar resumen de conexiones"""
    try:
        result = subprocess.run(['aconnect', '-l'], capture_output=True, text=True)
        
        print("\n📋 RESUMEN DE CONEXIONES:")
        print("="*40)
        
        lines = result.stdout.split('\n')
        for i, line in enumerate(lines):
            if 'client' in line and any(keyword in line.lower() for keyword in ['pico', 'captain', 'mpk', 'akai']):
                print(f"🎛️ {line.strip()}")
                
                # Buscar conexiones en las siguientes líneas
                for j in range(i+1, min(i+5, len(lines))):
                    if 'Connected From:' in lines[j] or 'Connecting To:' in lines[j]:
                        print(f"   {lines[j].strip()}")
                    elif 'client' in lines[j]:
                        break
        
        print("="*40)
        
    except Exception as e:
        print(f"❌ Error verificando conexiones: {e}")

def test_live_midi():
    """Probar MIDI en vivo"""
    print("\n🎹 PRUEBA EN VIVO:")
    print("Toca una tecla en tu controlador MIDI...")
    print("(Presiona Ctrl+C para salir)")
    
    try:
        import rtmidi
        
        midi_in = rtmidi.MidiIn()
        ports = midi_in.get_ports()
        
        print(f"Puertos disponibles: {ports}")
        
        # Conectar al primer controlador encontrado
        for i, port in enumerate(ports):
            if any(keyword in port.lower() for keyword in ['pico', 'captain', 'mpk', 'akai']):
                midi_in.open_port(i)
                print(f"🔌 Escuchando: {port}")
                
                def callback(message, data):
                    msg, _ = message
                    print(f"🎵 MIDI recibido: {[hex(b) for b in msg]} - Raw: {msg}")
                
                midi_in.set_callback(callback)
                
                # Esperar mensajes
                input("Presiona Enter cuando termines de probar...")
                midi_in.close_port()
                return
        
        print("❌ No se encontró controlador para monitorear")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🎸 Debug MIDI Connections")
    print("="*50)
    
    try:
        while True:
            print("\n📋 Opciones:")
            print("1. Ver conexiones actuales")
            print("2. Forzar conexiones")
            print("3. Probar MIDI en vivo")
            print("q. Salir")
            
            choice = input("\n> ").strip().lower()
            
            if choice == '1':
                check_midi_connections()
            elif choice == '2':
                force_connections()
            elif choice == '3':
                test_live_midi()
            elif choice == 'q':
                break
            else:
                print("❌ Opción no válida")
                
    except KeyboardInterrupt:
        print("\n👋 Terminado")