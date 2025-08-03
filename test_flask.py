#!/usr/bin/env python3
"""
Test script to verify Flask app setup
"""

print("🧪 Testing Flask app setup...")

try:
    # Test basic imports
    print("📦 Testing imports...")
    import sys
    import os
    
    # Add web directory to path
    web_dir = os.path.join(os.path.dirname(__file__), 'web')
    sys.path.insert(0, web_dir)
    
    # Test Flask imports
    from flask import Flask
    print("✅ Flask import successful")
    
    from flask_socketio import SocketIO
    print("✅ Flask-SocketIO import successful")
    
    # Test our app import
    import app as guitar_app
    print("✅ Guitar-MIDI app import successful")
    
    # Test route registration
    print(f"📋 Registered routes: {list(guitar_app.app.url_map.iter_rules())}")
    
    print("🎉 All tests passed! Flask app is ready to run.")
    print("💡 To start the server, run: python web/app.py")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure all dependencies are installed:")
    print("   pip install Flask Flask-SocketIO python-socketio eventlet")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()