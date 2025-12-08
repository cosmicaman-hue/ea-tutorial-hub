#!/usr/bin/env python3
"""
EA Tutorial Hub - Network Server Setup Script
Automates the setup process for running on a server PC
"""

import os
import sys
import socket
import subprocess
import platform
from pathlib import Path

class ServerSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / '.venv'
        self.python_exe = self.venv_path / 'Scripts' / 'python.exe' if platform.system() == 'Windows' else self.venv_path / 'bin' / 'python'
        self.requirements_file = self.project_root / 'requirements.txt'
        
    def print_header(self, text):
        """Print formatted header"""
        print("\n" + "="*60)
        print(f"  {text}")
        print("="*60 + "\n")
    
    def print_step(self, step_num, text):
        """Print step with number"""
        print(f"\n[Step {step_num}] {text}")
        print("-" * 60)
    
    def get_server_ip(self):
        """Get server's IP address"""
        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            return ip_address
        except:
            return "Unable to determine"
    
    def check_python(self):
        """Check if Python is installed"""
        self.print_step(1, "Checking Python Installation")
        try:
            result = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
            print(f"✅ Python found: {result.stdout.strip()}")
            return True
        except:
            print("❌ Python not found!")
            print("Please install Python 3.10+ from https://www.python.org/downloads/")
            return False
    
    def create_venv(self):
        """Create virtual environment"""
        self.print_step(2, "Creating Virtual Environment")
        
        if self.venv_path.exists():
            print(f"✅ Virtual environment already exists at: {self.venv_path}")
            return True
        
        try:
            subprocess.run([sys.executable, '-m', 'venv', str(self.venv_path)], check=True)
            print(f"✅ Virtual environment created at: {self.venv_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False
    
    def install_dependencies(self):
        """Install required packages"""
        self.print_step(3, "Installing Dependencies")
        
        if not self.requirements_file.exists():
            print(f"❌ requirements.txt not found at: {self.requirements_file}")
            return False
        
        try:
            if platform.system() == 'Windows':
                subprocess.run([str(self.python_exe), '-m', 'pip', 'install', '-r', str(self.requirements_file)], check=True)
            else:
                subprocess.run([str(self.python_exe), '-m', 'pip', 'install', '-r', str(self.requirements_file)], check=True)
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    def check_database(self):
        """Check if database exists"""
        self.print_step(4, "Checking Database")
        
        db_path = self.project_root / 'instance' / 'ea_tutorial.db'
        
        if db_path.exists():
            print(f"✅ Database found at: {db_path}")
            size = db_path.stat().st_size / 1024  # Size in KB
            print(f"   Database size: {size:.2f} KB")
            return True
        else:
            print(f"⚠️  Database not found at: {db_path}")
            print("   It will be created automatically when you start the application")
            return True
    
    def get_network_info(self):
        """Get network information"""
        self.print_step(5, "Network Information")
        
        ip_address = self.get_server_ip()
        hostname = socket.gethostname()
        
        print(f"Server Hostname: {hostname}")
        print(f"Server IP Address: {ip_address}")
        print(f"\nAccess URLs from other PCs on the network:")
        print(f"  • Main URL: http://{ip_address}:5000")
        print(f"  • Login: http://{ip_address}:5000/auth/login")
        print(f"  • Admin Dashboard: http://{ip_address}:5000/admin/dashboard")
        
        return ip_address
    
    def create_launcher_scripts(self):
        """Create launcher scripts for convenience"""
        self.print_step(6, "Creating Launcher Scripts")
        
        if platform.system() == 'Windows':
            # Create batch file for Windows
            batch_file = self.project_root / 'run_server.bat'
            batch_content = f"""@echo off
REM EA Tutorial Hub - Server Launcher
REM This script starts the Flask application for network access

cd /d "{self.project_root}"
{self.venv_path}\\Scripts\\python.exe run.py
pause
"""
            with open(batch_file, 'w') as f:
                f.write(batch_content)
            print(f"✅ Created: {batch_file}")
            print(f"   Double-click this file to start the server")
        
        # Create PowerShell script
        ps_file = self.project_root / 'run_server.ps1'
        ps_content = f"""# EA Tutorial Hub - Server Launcher (PowerShell)
# This script starts the Flask application for network access

Set-Location "{self.project_root}"
& "{self.venv_path}\\Scripts\\python.exe" run.py
"""
        with open(ps_file, 'w') as f:
            f.write(ps_content)
        print(f"✅ Created: {ps_file}")
    
    def create_config_file(self):
        """Create configuration file for 24x7 setup"""
        self.print_step(7, "Creating Server Configuration")
        
        config_file = self.project_root / 'server_config.txt'
        server_ip = self.get_server_ip()
        
        config_content = f"""# EA Tutorial Hub - Server Configuration
# Generated: {__import__('datetime').datetime.now().isoformat()}

[SERVER_INFO]
Hostname: {socket.gethostname()}
IP_Address: {server_ip}
Port: 5000

[ACCESS_URLS]
Main: http://{server_ip}:5000
Login: http://{server_ip}:5000/auth/login
Admin_Dashboard: http://{server_ip}:5000/admin/dashboard

[DATABASE]
Location: {self.project_root / 'instance' / 'ea_tutorial.db'}
Type: SQLite3

[DEFAULT_CREDENTIALS]
Admin_Username: Admin
Admin_Password: admin123
Teacher_Username: Teacher
Teacher_Password: teacher123
Student_Username: EA24C001
Student_Password: student123

[INSTRUCTIONS]
1. Keep this server PC on 24x7
2. Double-click 'run_server.bat' to start the application
3. Access from other PCs using the URLs above
4. To stop, press Ctrl+C in the terminal

[FIREWALL]
If Python is blocked by firewall:
1. Settings > Privacy & Security > Firewall
2. Allow an app through firewall
3. Find 'python.exe' and check 'Private'
4. Click OK

[TROUBLESHOOTING]
- Port already in use: netstat -ano | findstr :5000
- Database error: Delete 'instance/ea_tutorial.db' and restart
- Can't connect: Make sure both PCs on same WiFi network
- Check this guide: NETWORK_DEPLOYMENT_GUIDE.md
"""
        
        with open(config_file, 'w') as f:
            f.write(config_content)
        print(f"✅ Configuration file created: {config_file}")
    
    def run_setup(self):
        """Run complete setup"""
        self.print_header("EA Tutorial Hub - Network Server Setup")
        
        print("This script will help you set up the application for 24x7 network access\n")
        
        # Run checks
        if not self.check_python():
            return False
        
        if not self.create_venv():
            return False
        
        if not self.install_dependencies():
            return False
        
        if not self.check_database():
            return False
        
        server_ip = self.get_network_info()
        
        self.create_launcher_scripts()
        
        self.create_config_file()
        
        # Summary
        self.print_header("Setup Complete! ✅")
        
        print("Next Steps:")
        print(f"\n1. Read the setup guide: NETWORK_DEPLOYMENT_GUIDE.md")
        print(f"\n2. Start the server:")
        if platform.system() == 'Windows':
            print(f"   • Double-click 'run_server.bat' (easiest)")
            print(f"   • Or run in PowerShell: python run.py")
        else:
            print(f"   • Run: python run.py")
        
        print(f"\n3. Access from other PCs on your WiFi network:")
        print(f"   • http://{server_ip}:5000")
        print(f"   • http://{server_ip}:5000/auth/login")
        
        print(f"\n4. For auto-start on boot (Windows):")
        print(f"   • See 'NETWORK_DEPLOYMENT_GUIDE.md' for Task Scheduler setup")
        
        print(f"\n5. Default credentials:")
        print(f"   • Admin: Admin / admin123")
        print(f"   • Teacher: Teacher / teacher123")
        print(f"   • Student: EA24C001 / student123")
        
        print("\n" + "="*60)
        print("Your EA Tutorial Hub is ready for 24x7 network deployment!")
        print("="*60 + "\n")
        
        return True

if __name__ == '__main__':
    setup = ServerSetup()
    setup.run_setup()
