"""
System Info API
Información del sistema y estado del hardware
"""

import time
import subprocess
import os
import sys
from typing import Dict, List, Any

# Importar psutil con fallback
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️  psutil no disponible. Funcionalidad de sistema limitada.")

class SystemInfoAPI:
    def __init__(self):
        self.start_time = time.time()
    
    def get_info(self) -> Dict[str, Any]:
        """Obtener información completa del sistema"""
        return {
            'system': self._get_system_info(),
            'hardware': self._get_hardware_info(),
            'midi': self._get_midi_info(),
            'audio': self._get_audio_info(),
            'network': self._get_network_info(),
            'performance': self._get_performance_info()
        }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Información del sistema operativo"""
        try:
            system_info = {
                'os': f"{os.uname().sysname} {os.uname().release}",
                'hostname': os.uname().nodename,
                'architecture': os.uname().machine,
                'python_version': sys.version.split()[0],
                'app_uptime': int(time.time() - self.start_time)
            }
            
            if PSUTIL_AVAILABLE:
                uptime = time.time() - psutil.boot_time()
                system_info.update({
                    'uptime_seconds': int(uptime),
                    'uptime_formatted': self._format_uptime(uptime)
                })
            else:
                system_info['uptime_note'] = 'psutil required for uptime info'
                
            return system_info
        except Exception as e:
            return {'error': str(e)}
    
    def _get_hardware_info(self) -> Dict[str, Any]:
        """Información del hardware"""
        try:
            hardware_info = {
                'cpu_model': self._get_cpu_model(),
                'temperature': self._get_cpu_temperature()
            }
            
            if PSUTIL_AVAILABLE:
                hardware_info.update({
                    'cpu_cores': psutil.cpu_count(),
                    'cpu_usage': psutil.cpu_percent(interval=1),
                    'memory_total': psutil.virtual_memory().total,
                    'memory_used': psutil.virtual_memory().used,
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_usage': self._get_disk_usage()
                })
            else:
                hardware_info['note'] = 'psutil required for detailed hardware info'
                
            return hardware_info
        except Exception as e:
            return {'error': str(e)}
    
    def _get_midi_info(self) -> Dict[str, Any]:
        """Información de dispositivos MIDI"""
        try:
            # Intentar obtener lista de dispositivos MIDI
            midi_devices = []
            
            try:
                import rtmidi
                midi_in = rtmidi.MidiIn()
                available_ports = midi_in.get_ports()
                
                for i, port in enumerate(available_ports):
                    midi_devices.append({
                        'port': i,
                        'name': port,
                        'status': 'available'
                    })
                    
            except ImportError:
                midi_devices = [{'error': 'rtmidi not available'}]
            except Exception as e:
                midi_devices = [{'error': str(e)}]
            
            return {
                'devices': midi_devices,
                'devices_count': len(midi_devices)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _get_audio_info(self) -> Dict[str, Any]:
        """Información del sistema de audio"""
        try:
            audio_info = {
                'alsa_devices': [],
                'pulse_status': 'unknown',
                'fluidsynth_status': 'unknown'
            }
            
            # Obtener dispositivos ALSA
            try:
                result = subprocess.run(['aplay', '-l'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                if result.returncode == 0:
                    audio_info['alsa_devices'] = self._parse_aplay_output(result.stdout)
            except:
                pass
            
            # Verificar PulseAudio
            try:
                result = subprocess.run(['pulseaudio', '--check'], 
                                      capture_output=True, 
                                      timeout=5)
                audio_info['pulse_status'] = 'running' if result.returncode == 0 else 'not running'
            except:
                pass
            
            # Verificar FluidSynth
            try:
                result = subprocess.run(['which', 'fluidsynth'], 
                                      capture_output=True, 
                                      timeout=5)
                audio_info['fluidsynth_status'] = 'available' if result.returncode == 0 else 'not found'
            except:
                pass
            
            return audio_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_network_info(self) -> Dict[str, Any]:
        """Información de red"""
        try:
            network_info = {
                'interfaces': [],
                'wifi_status': 'unknown'
            }
            
            if PSUTIL_AVAILABLE:
                # Obtener interfaces de red con psutil
                for interface, addrs in psutil.net_if_addrs().items():
                    interface_info = {
                        'name': interface,
                        'addresses': []
                    }
                    
                    for addr in addrs:
                        if addr.family == 2:  # IPv4
                            interface_info['addresses'].append({
                                'type': 'IPv4',
                                'address': addr.address,
                                'netmask': addr.netmask
                            })
                    
                    if interface_info['addresses']:  # Solo incluir si tiene direcciones IPv4
                        network_info['interfaces'].append(interface_info)
            else:
                # Fallback usando comandos del sistema
                try:
                    result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        ips = result.stdout.strip().split()
                        for ip in ips:
                            network_info['interfaces'].append({
                                'name': 'unknown',
                                'addresses': [{'type': 'IPv4', 'address': ip, 'netmask': 'unknown'}]
                            })
                except:
                    network_info['note'] = 'psutil required for detailed network info'
            
            return network_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_performance_info(self) -> Dict[str, Any]:
        """Información de rendimiento"""
        try:
            performance_info = {}
            
            if PSUTIL_AVAILABLE:
                performance_info.update({
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'cpu_freq': psutil.cpu_freq().current if psutil.cpu_freq() else None,
                    'memory_percent': psutil.virtual_memory().percent,
                    'processes': len(psutil.pids()),
                    'boot_time': psutil.boot_time()
                })
            else:
                performance_info['note'] = 'psutil required for performance info'
            
            # Load average disponible sin psutil en sistemas Unix
            try:
                performance_info['load_average'] = os.getloadavg()
            except:
                performance_info['load_average'] = None
                
            return performance_info
        except Exception as e:
            return {'error': str(e)}
    
    def _get_cpu_model(self) -> str:
        """Obtener modelo de CPU"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                for line in f:
                    if 'model name' in line:
                        return line.split(':')[1].strip()
            return 'Unknown'
        except:
            return 'Unknown'
    
    def _get_cpu_temperature(self) -> float:
        """Obtener temperatura de CPU (Raspberry Pi)"""
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read().strip()) / 1000.0
                return temp
        except:
            return None
    
    def _get_disk_usage(self) -> Dict[str, Any]:
        """Obtener uso de disco"""
        try:
            if PSUTIL_AVAILABLE:
                disk = psutil.disk_usage('/')
                return {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                }
            else:
                # Fallback usando df
                try:
                    result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        if len(lines) >= 2:
                            parts = lines[1].split()
                            if len(parts) >= 5:
                                return {
                                    'total': parts[1],
                                    'used': parts[2],
                                    'free': parts[3],
                                    'percent': parts[4],
                                    'note': 'Using df command (human readable)'
                                }
                except:
                    pass
                return {'note': 'psutil required for detailed disk info'}
        except:
            return {}
    
    def _parse_aplay_output(self, output: str) -> List[Dict]:
        """Parsear salida de aplay -l"""
        devices = []
        try:
            lines = output.split('\n')
            for line in lines:
                if 'card' in line and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        device_info = parts[1].strip()
                        devices.append({
                            'name': device_info,
                            'raw_line': line.strip()
                        })
        except:
            pass
        
        return devices
    
    def _format_uptime(self, seconds: float) -> str:
        """Formatear tiempo de funcionamiento"""
        try:
            days = int(seconds // 86400)
            hours = int((seconds % 86400) // 3600)
            minutes = int((seconds % 3600) // 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except:
            return "Unknown"