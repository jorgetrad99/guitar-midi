"""
FluidSynth Utilities for Guitar-MIDI Complete System
Extracts real instrument data from FluidSynth and manages audio configuration
"""

import fluidsynth
import os
from typing import Dict, List, Any, Optional

class FluidSynthInstrumentExtractor:
    """Extract real instrument data from FluidSynth SoundFont"""
    
    def __init__(self):
        self.fs = None
        self.sfid = None
        
    def initialize(self, soundfont_path: str = "/usr/share/sounds/sf2/FluidR3_GM.sf2") -> bool:
        """Initialize FluidSynth for instrument extraction"""
        try:
            self.fs = fluidsynth.Synth()
            self.fs.start(driver='alsa')
            
            if os.path.exists(soundfont_path):
                self.sfid = self.fs.sfload(soundfont_path)
                print(f"   ✅ SoundFont cargado: {soundfont_path} (SFID: {self.sfid})")
                return True
            else:
                print(f"   ❌ SoundFont no encontrado: {soundfont_path}")
                return False
                
        except Exception as e:
            print(f"Error initializing FluidSynth: {e}")
            return False
    
    def get_gm_instruments(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract General MIDI instruments organized by category
        Returns real instruments that FluidSynth can actually play
        """
        if not self.fs or self.sfid is None:
            return self._get_fallback_instruments()
        
        try:
            # General MIDI instrument map (Program Change 0-127)
            gm_instruments = {
                # PIANO (0-7)
                "Piano": [
                    {"id": 0, "name": "Acoustic Grand Piano", "program": 0, "bank": 0, "channel": 0, "icon": "🎹"},
                    {"id": 1, "name": "Bright Acoustic Piano", "program": 1, "bank": 0, "channel": 0, "icon": "🎹"},
                    {"id": 2, "name": "Electric Grand Piano", "program": 2, "bank": 0, "channel": 0, "icon": "🎹"},
                    {"id": 3, "name": "Honky-tonk Piano", "program": 3, "bank": 0, "channel": 0, "icon": "🎹"},
                    {"id": 4, "name": "Electric Piano 1", "program": 4, "bank": 0, "channel": 0, "icon": "🎹"},
                    {"id": 5, "name": "Electric Piano 2", "program": 5, "bank": 0, "channel": 0, "icon": "🎹"},
                    {"id": 6, "name": "Harpsichord", "program": 6, "bank": 0, "channel": 0, "icon": "🎹"},
                    {"id": 7, "name": "Clavi", "program": 7, "bank": 0, "channel": 0, "icon": "🎹"},
                ],
                
                # CHROMATIC PERCUSSION (8-15)
                "Chromatic Percussion": [
                    {"id": 8, "name": "Celesta", "program": 8, "bank": 0, "channel": 0, "icon": "🔔"},
                    {"id": 9, "name": "Glockenspiel", "program": 9, "bank": 0, "channel": 0, "icon": "🔔"},
                    {"id": 10, "name": "Music Box", "program": 10, "bank": 0, "channel": 0, "icon": "🎵"},
                    {"id": 11, "name": "Vibraphone", "program": 11, "bank": 0, "channel": 0, "icon": "🎤"},
                    {"id": 12, "name": "Marimba", "program": 12, "bank": 0, "channel": 0, "icon": "🥁"},
                    {"id": 13, "name": "Xylophone", "program": 13, "bank": 0, "channel": 0, "icon": "🎼"},
                    {"id": 14, "name": "Tubular Bells", "program": 14, "bank": 0, "channel": 0, "icon": "🔔"},
                    {"id": 15, "name": "Dulcimer", "program": 15, "bank": 0, "channel": 0, "icon": "🎻"},
                ],
                
                # ORGAN (16-23)
                "Organ": [
                    {"id": 16, "name": "Drawbar Organ", "program": 16, "bank": 0, "channel": 0, "icon": "🎹"},
                    {"id": 17, "name": "Percussive Organ", "program": 17, "bank": 0, "channel": 0, "icon": "🎹"},
                    {"id": 18, "name": "Rock Organ", "program": 18, "bank": 0, "channel": 0, "icon": "🎸"},
                    {"id": 19, "name": "Church Organ", "program": 19, "bank": 0, "channel": 0, "icon": "⛪"},
                    {"id": 20, "name": "Reed Organ", "program": 20, "bank": 0, "channel": 0, "icon": "🎹"},
                    {"id": 21, "name": "Accordion", "program": 21, "bank": 0, "channel": 0, "icon": "🪗"},
                    {"id": 22, "name": "Harmonica", "program": 22, "bank": 0, "channel": 0, "icon": "🎼"},
                    {"id": 23, "name": "Tango Accordion", "program": 23, "bank": 0, "channel": 0, "icon": "🪗"},
                ],
                
                # GUITAR (24-31)
                "Guitar": [
                    {"id": 24, "name": "Acoustic Guitar (nylon)", "program": 24, "bank": 0, "channel": 0, "icon": "🎸"},
                    {"id": 25, "name": "Acoustic Guitar (steel)", "program": 25, "bank": 0, "channel": 0, "icon": "🎸"},
                    {"id": 26, "name": "Electric Guitar (jazz)", "program": 26, "bank": 0, "channel": 0, "icon": "🎸"},
                    {"id": 27, "name": "Electric Guitar (clean)", "program": 27, "bank": 0, "channel": 0, "icon": "🎸"},
                    {"id": 28, "name": "Electric Guitar (muted)", "program": 28, "bank": 0, "channel": 0, "icon": "🎸"},
                    {"id": 29, "name": "Overdriven Guitar", "program": 29, "bank": 0, "channel": 0, "icon": "🎸"},
                    {"id": 30, "name": "Distortion Guitar", "program": 30, "bank": 0, "channel": 0, "icon": "🎸"},
                    {"id": 31, "name": "Guitar harmonics", "program": 31, "bank": 0, "channel": 0, "icon": "🎸"},
                ],
                
                # BASS (32-39)
                "Bass": [
                    {"id": 32, "name": "Acoustic Bass", "program": 32, "bank": 0, "channel": 1, "icon": "🎸"},
                    {"id": 33, "name": "Electric Bass (finger)", "program": 33, "bank": 0, "channel": 1, "icon": "🎸"},
                    {"id": 34, "name": "Electric Bass (pick)", "program": 34, "bank": 0, "channel": 1, "icon": "🎸"},
                    {"id": 35, "name": "Fretless Bass", "program": 35, "bank": 0, "channel": 1, "icon": "🎸"},
                    {"id": 36, "name": "Slap Bass 1", "program": 36, "bank": 0, "channel": 1, "icon": "🎸"},
                    {"id": 37, "name": "Slap Bass 2", "program": 37, "bank": 0, "channel": 1, "icon": "🎸"},
                    {"id": 38, "name": "Synth Bass 1", "program": 38, "bank": 0, "channel": 1, "icon": "🎛️"},
                    {"id": 39, "name": "Synth Bass 2", "program": 39, "bank": 0, "channel": 1, "icon": "🎛️"},
                ],
                
                # STRINGS (40-47)
                "Strings": [
                    {"id": 40, "name": "Violin", "program": 40, "bank": 0, "channel": 2, "icon": "🎻"},
                    {"id": 41, "name": "Viola", "program": 41, "bank": 0, "channel": 2, "icon": "🎻"},
                    {"id": 42, "name": "Cello", "program": 42, "bank": 0, "channel": 2, "icon": "🎻"},
                    {"id": 43, "name": "Contrabass", "program": 43, "bank": 0, "channel": 2, "icon": "🎻"},
                    {"id": 44, "name": "Tremolo Strings", "program": 44, "bank": 0, "channel": 2, "icon": "🎻"},
                    {"id": 45, "name": "Pizzicato Strings", "program": 45, "bank": 0, "channel": 2, "icon": "🎻"},
                    {"id": 46, "name": "Orchestral Harp", "program": 46, "bank": 0, "channel": 2, "icon": "🎼"},
                    {"id": 47, "name": "Timpani", "program": 47, "bank": 0, "channel": 2, "icon": "🥁"},
                ],
                
                # ENSEMBLE (48-55)
                "Ensemble": [
                    {"id": 48, "name": "String Ensemble 1", "program": 48, "bank": 0, "channel": 3, "icon": "🎻"},
                    {"id": 49, "name": "String Ensemble 2", "program": 49, "bank": 0, "channel": 3, "icon": "🎻"},
                    {"id": 50, "name": "SynthStrings 1", "program": 50, "bank": 0, "channel": 3, "icon": "🎛️"},
                    {"id": 51, "name": "SynthStrings 2", "program": 51, "bank": 0, "channel": 3, "icon": "🎛️"},
                    {"id": 52, "name": "Choir Aahs", "program": 52, "bank": 0, "channel": 3, "icon": "👥"},
                    {"id": 53, "name": "Voice Oohs", "program": 53, "bank": 0, "channel": 3, "icon": "👥"},
                    {"id": 54, "name": "Synth Voice", "program": 54, "bank": 0, "channel": 3, "icon": "🎛️"},
                    {"id": 55, "name": "Orchestra Hit", "program": 55, "bank": 0, "channel": 3, "icon": "🎺"},
                ],
                
                # BRASS (56-63)
                "Brass": [
                    {"id": 56, "name": "Trumpet", "program": 56, "bank": 0, "channel": 4, "icon": "🎺"},
                    {"id": 57, "name": "Trombone", "program": 57, "bank": 0, "channel": 4, "icon": "🎺"},
                    {"id": 58, "name": "Tuba", "program": 58, "bank": 0, "channel": 4, "icon": "🎺"},
                    {"id": 59, "name": "Muted Trumpet", "program": 59, "bank": 0, "channel": 4, "icon": "🎺"},
                    {"id": 60, "name": "French Horn", "program": 60, "bank": 0, "channel": 4, "icon": "🎺"},
                    {"id": 61, "name": "Brass Section", "program": 61, "bank": 0, "channel": 4, "icon": "🎺"},
                    {"id": 62, "name": "SynthBrass 1", "program": 62, "bank": 0, "channel": 4, "icon": "🎛️"},
                    {"id": 63, "name": "SynthBrass 2", "program": 63, "bank": 0, "channel": 4, "icon": "🎛️"},
                ],
                
                # REED (64-71)
                "Reed": [
                    {"id": 64, "name": "Soprano Sax", "program": 64, "bank": 0, "channel": 5, "icon": "🎷"},
                    {"id": 65, "name": "Alto Sax", "program": 65, "bank": 0, "channel": 5, "icon": "🎷"},
                    {"id": 66, "name": "Tenor Sax", "program": 66, "bank": 0, "channel": 5, "icon": "🎷"},
                    {"id": 67, "name": "Baritone Sax", "program": 67, "bank": 0, "channel": 5, "icon": "🎷"},
                    {"id": 68, "name": "Oboe", "program": 68, "bank": 0, "channel": 5, "icon": "🪈"},
                    {"id": 69, "name": "English Horn", "program": 69, "bank": 0, "channel": 5, "icon": "🪈"},
                    {"id": 70, "name": "Bassoon", "program": 70, "bank": 0, "channel": 5, "icon": "🪈"},
                    {"id": 71, "name": "Clarinet", "program": 71, "bank": 0, "channel": 5, "icon": "🪈"},
                ],
                
                # PIPE (72-79)
                "Pipe": [
                    {"id": 72, "name": "Piccolo", "program": 72, "bank": 0, "channel": 6, "icon": "🪈"},
                    {"id": 73, "name": "Flute", "program": 73, "bank": 0, "channel": 6, "icon": "🪈"},
                    {"id": 74, "name": "Recorder", "program": 74, "bank": 0, "channel": 6, "icon": "🪈"},
                    {"id": 75, "name": "Pan Flute", "program": 75, "bank": 0, "channel": 6, "icon": "🪈"},
                    {"id": 76, "name": "Blown Bottle", "program": 76, "bank": 0, "channel": 6, "icon": "🍾"},
                    {"id": 77, "name": "Shakuhachi", "program": 77, "bank": 0, "channel": 6, "icon": "🪈"},
                    {"id": 78, "name": "Whistle", "program": 78, "bank": 0, "channel": 6, "icon": "🪈"},
                    {"id": 79, "name": "Ocarina", "program": 79, "bank": 0, "channel": 6, "icon": "🪈"},
                ],
                
                # SYNTH LEAD (80-87)
                "Synth Lead": [
                    {"id": 80, "name": "Lead 1 (square)", "program": 80, "bank": 0, "channel": 7, "icon": "🎛️"},
                    {"id": 81, "name": "Lead 2 (sawtooth)", "program": 81, "bank": 0, "channel": 7, "icon": "🎛️"},
                    {"id": 82, "name": "Lead 3 (calliope)", "program": 82, "bank": 0, "channel": 7, "icon": "🎛️"},
                    {"id": 83, "name": "Lead 4 (chiff)", "program": 83, "bank": 0, "channel": 7, "icon": "🎛️"},
                    {"id": 84, "name": "Lead 5 (charang)", "program": 84, "bank": 0, "channel": 7, "icon": "🎛️"},
                    {"id": 85, "name": "Lead 6 (voice)", "program": 85, "bank": 0, "channel": 7, "icon": "🎛️"},
                    {"id": 86, "name": "Lead 7 (fifths)", "program": 86, "bank": 0, "channel": 7, "icon": "🎛️"},
                    {"id": 87, "name": "Lead 8 (bass + lead)", "program": 87, "bank": 0, "channel": 7, "icon": "🎛️"},
                ],
                
                # SYNTH PAD (88-95)
                "Synth Pad": [
                    {"id": 88, "name": "Pad 1 (new age)", "program": 88, "bank": 0, "channel": 8, "icon": "🎛️"},
                    {"id": 89, "name": "Pad 2 (warm)", "program": 89, "bank": 0, "channel": 8, "icon": "🎛️"},
                    {"id": 90, "name": "Pad 3 (polysynth)", "program": 90, "bank": 0, "channel": 8, "icon": "🎛️"},
                    {"id": 91, "name": "Pad 4 (choir)", "program": 91, "bank": 0, "channel": 8, "icon": "🎛️"},
                    {"id": 92, "name": "Pad 5 (bowed)", "program": 92, "bank": 0, "channel": 8, "icon": "🎛️"},
                    {"id": 93, "name": "Pad 6 (metallic)", "program": 93, "bank": 0, "channel": 8, "icon": "🎛️"},
                    {"id": 94, "name": "Pad 7 (halo)", "program": 94, "bank": 0, "channel": 8, "icon": "🎛️"},
                    {"id": 95, "name": "Pad 8 (sweep)", "program": 95, "bank": 0, "channel": 8, "icon": "🎛️"},
                ],
                
                # SYNTH EFFECTS (96-103)
                "Synth Effects": [
                    {"id": 96, "name": "FX 1 (rain)", "program": 96, "bank": 0, "channel": 9, "icon": "🌧️"},
                    {"id": 97, "name": "FX 2 (soundtrack)", "program": 97, "bank": 0, "channel": 9, "icon": "🎬"},
                    {"id": 98, "name": "FX 3 (crystal)", "program": 98, "bank": 0, "channel": 9, "icon": "💎"},
                    {"id": 99, "name": "FX 4 (atmosphere)", "program": 99, "bank": 0, "channel": 9, "icon": "🌌"},
                    {"id": 100, "name": "FX 5 (brightness)", "program": 100, "bank": 0, "channel": 9, "icon": "✨"},
                    {"id": 101, "name": "FX 6 (goblins)", "program": 101, "bank": 0, "channel": 9, "icon": "👹"},
                    {"id": 102, "name": "FX 7 (echoes)", "program": 102, "bank": 0, "channel": 9, "icon": "🔊"},
                    {"id": 103, "name": "FX 8 (sci-fi)", "program": 103, "bank": 0, "channel": 9, "icon": "🚀"},
                ],
                
                # ETHNIC (104-111)
                "Ethnic": [
                    {"id": 104, "name": "Sitar", "program": 104, "bank": 0, "channel": 10, "icon": "🪕"},
                    {"id": 105, "name": "Banjo", "program": 105, "bank": 0, "channel": 10, "icon": "🪕"},
                    {"id": 106, "name": "Shamisen", "program": 106, "bank": 0, "channel": 10, "icon": "🎸"},
                    {"id": 107, "name": "Koto", "program": 107, "bank": 0, "channel": 10, "icon": "🎼"},
                    {"id": 108, "name": "Kalimba", "program": 108, "bank": 0, "channel": 10, "icon": "🎵"},
                    {"id": 109, "name": "Bag pipe", "program": 109, "bank": 0, "channel": 10, "icon": "🪈"},
                    {"id": 110, "name": "Fiddle", "program": 110, "bank": 0, "channel": 10, "icon": "🎻"},
                    {"id": 111, "name": "Shanai", "program": 111, "bank": 0, "channel": 10, "icon": "🪈"},
                ],
                
                # PERCUSSIVE (112-119)
                "Percussive": [
                    {"id": 112, "name": "Tinkle Bell", "program": 112, "bank": 0, "channel": 11, "icon": "🔔"},
                    {"id": 113, "name": "Agogo", "program": 113, "bank": 0, "channel": 11, "icon": "🥁"},
                    {"id": 114, "name": "Steel Drums", "program": 114, "bank": 0, "channel": 11, "icon": "🛢️"},
                    {"id": 115, "name": "Woodblock", "program": 115, "bank": 0, "channel": 11, "icon": "🪵"},
                    {"id": 116, "name": "Taiko Drum", "program": 116, "bank": 0, "channel": 11, "icon": "🥁"},
                    {"id": 117, "name": "Melodic Tom", "program": 117, "bank": 0, "channel": 11, "icon": "🥁"},
                    {"id": 118, "name": "Synth Drum", "program": 118, "bank": 0, "channel": 11, "icon": "🎛️"},
                    {"id": 119, "name": "Reverse Cymbal", "program": 119, "bank": 0, "channel": 11, "icon": "🥁"},
                ],
                
                # SOUND EFFECTS (120-127)
                "Sound Effects": [
                    {"id": 120, "name": "Guitar Fret Noise", "program": 120, "bank": 0, "channel": 12, "icon": "🎸"},
                    {"id": 121, "name": "Breath Noise", "program": 121, "bank": 0, "channel": 12, "icon": "💨"},
                    {"id": 122, "name": "Seashore", "program": 122, "bank": 0, "channel": 12, "icon": "🌊"},
                    {"id": 123, "name": "Bird Tweet", "program": 123, "bank": 0, "channel": 12, "icon": "🐦"},
                    {"id": 124, "name": "Telephone Ring", "program": 124, "bank": 0, "channel": 12, "icon": "📞"},
                    {"id": 125, "name": "Helicopter", "program": 125, "bank": 0, "channel": 12, "icon": "🚁"},
                    {"id": 126, "name": "Applause", "program": 126, "bank": 0, "channel": 12, "icon": "👏"},
                    {"id": 127, "name": "Gunshot", "program": 127, "bank": 0, "channel": 12, "icon": "💥"},
                ],
                
                # DRUMS (special bank 128, channel 9)
                "Drums": [
                    {"id": 128, "name": "Standard Drum Kit", "program": 0, "bank": 128, "channel": 9, "icon": "🥁"},
                    {"id": 129, "name": "Room Drum Kit", "program": 8, "bank": 128, "channel": 9, "icon": "🥁"},
                    {"id": 130, "name": "Power Drum Kit", "program": 16, "bank": 128, "channel": 9, "icon": "🥁"},
                    {"id": 131, "name": "Electronic Drum Kit", "program": 24, "bank": 128, "channel": 9, "icon": "🥁"},
                    {"id": 132, "name": "TR-808 Drum Kit", "program": 25, "bank": 128, "channel": 9, "icon": "🥁"},
                    {"id": 133, "name": "Jazz Drum Kit", "program": 32, "bank": 128, "channel": 9, "icon": "🥁"},
                    {"id": 134, "name": "Brush Drum Kit", "program": 40, "bank": 128, "channel": 9, "icon": "🥁"},
                    {"id": 135, "name": "Orchestra Drum Kit", "program": 48, "bank": 128, "channel": 9, "icon": "🥁"},
                ]
            }
            
            # Verify instruments work with FluidSynth
            verified_instruments = {}
            for category, instruments in gm_instruments.items():
                verified_list = []
                for instrument in instruments:
                    if self._test_instrument(instrument):
                        verified_list.append(instrument)
                
                if verified_list:
                    verified_instruments[category] = verified_list
            
            return verified_instruments
            
        except Exception as e:
            print(f"Error extracting GM instruments: {e}")
            return self._get_fallback_instruments()
    
    def _test_instrument(self, instrument: Dict[str, Any]) -> bool:
        """Test if an instrument can be loaded in FluidSynth"""
        try:
            channel = instrument['channel']
            bank = instrument['bank']
            program = instrument['program']
            
            # Try to select the program
            # print(f"   🔧 Configurando: Canal={channel}, Bank={bank}, Program={program}")
            result = self.fs.program_select(channel, self.sfid, bank, program)
            print(f"   🎹 program_select resultado: {result}")
            return result == 0  # 0 indicates success in FluidSynth
            
        except Exception:
            return False
    
    def _get_fallback_instruments(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fallback instrument list if FluidSynth is not available"""
        return {
            "Piano": [
                {"id": 0, "name": "Acoustic Grand Piano", "program": 0, "bank": 0, "channel": 0, "icon": "🎹"},
                {"id": 4, "name": "Electric Piano 1", "program": 4, "bank": 0, "channel": 0, "icon": "🎹"},
            ],
            "Guitar": [
                {"id": 24, "name": "Acoustic Guitar (nylon)", "program": 24, "bank": 0, "channel": 0, "icon": "🎸"},
                {"id": 27, "name": "Electric Guitar (clean)", "program": 27, "bank": 0, "channel": 0, "icon": "🎸"},
            ],
            "Bass": [
                {"id": 32, "name": "Acoustic Bass", "program": 32, "bank": 0, "channel": 1, "icon": "🎸"},
                {"id": 33, "name": "Electric Bass (finger)", "program": 33, "bank": 0, "channel": 1, "icon": "🎸"},
            ],
            "Brass": [
                {"id": 56, "name": "Trumpet", "program": 56, "bank": 0, "channel": 4, "icon": "🎺"},
                {"id": 64, "name": "Soprano Sax", "program": 64, "bank": 0, "channel": 5, "icon": "🎷"},
            ],
            "Strings": [
                {"id": 40, "name": "Violin", "program": 40, "bank": 0, "channel": 2, "icon": "🎻"},
                {"id": 48, "name": "String Ensemble 1", "program": 48, "bank": 0, "channel": 3, "icon": "🎻"},
            ],
            "Drums": [
                {"id": 128, "name": "Standard Drum Kit", "program": 0, "bank": 128, "channel": 9, "icon": "🥁"},
            ]
        }
    
    def cleanup(self):
        """Clean up FluidSynth resources"""
        if self.fs:
            try:
                self.fs.delete()
                print("   ✅ Recursos de FluidSynth liberados")
            except Exception as e:
                print(f"   ⚠️  Error al liberar recursos de FluidSynth: {e}")
            self.fs = None
            self.sfid = None