#!/usr/bin/env python
"""
🚀 EXCEL ACADEMY LEADERSHIP BOARD - Launcher
Offline Student Scoring System - Auto-Start Script
"""

import os
import sys
import subprocess
import webbrowser
import time

def main():
    print("\n" + "="*70)
    print("🚀 EXCEL ACADEMY LEADERSHIP BOARD - LAUNCHER 🚀")
    print("   Offline Student Scoring System")
    print("="*70 + "\n")
    
    # Project directory - automatically detect from script location
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    print(f"📁 Project Directory: {project_dir}")
    print(f"🐍 Python Version: {sys.version.split()[0]}")
    print()
    
    # Check virtual environment
    venv_path = os.path.join(project_dir, ".venv")
    if not os.path.exists(venv_path):
        print("⚠️  Virtual environment not found. Creating...")
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
        print("✅ Virtual environment created.\n")
    
    # Activate virtual environment
    activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
    print(f"🔄 Using Python from: {venv_path}")
    
    # Check dependencies
    print("\n📦 Checking dependencies...")
    try:
        import flask
        print("✅ Flask installed")
    except ImportError:
        print("⚠️  Installing dependencies...")
        subprocess.run([os.path.join(venv_path, "Scripts", "pip"), "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed")
    
    # Print server info
    print("\n" + "="*70)
    print("📊 SERVER INFORMATION:")
    print("="*70)
    print("\n  🌐 Offline System: http://127.0.0.1:5000/scoreboard/offline")
    print("  📱 Mobile Access: http://[YOUR_PC_IP]:5000/scoreboard/offline")
    print("  🛑 To Stop: Press Ctrl+C\n")
    print("="*70 + "\n")
    
    # Open browser
    print("🌐 Opening browser...")
    time.sleep(2)
    url = "http://127.0.0.1:5000/scoreboard/offline"
    webbrowser.open(url)
    
    # Start Flask server
    print("✅ Starting Flask server...\n")
    print("-" * 70)
    
    try:
        subprocess.run([
            os.path.join(venv_path, "Scripts", "python"),
            "run.py"
        ], check=False)
    except KeyboardInterrupt:
        print("\n\n" + "-" * 70)
        print("⛔ Server stopped.")
        print("="*70 + "\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
