# Phase 3 Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the EA Tutorial Hub with Phase 3 enhancements to a production environment.

## Pre-Deployment Checklist

- [ ] All Phase 3 code changes applied
- [ ] Database backup created
- [ ] SSL/TLS certificates prepared
- [ ] Environment variables configured
- [ ] Admin has reviewed security settings
- [ ] All tests passed (see PHASE_3_TESTING.md)
- [ ] Database migration strategy confirmed
- [ ] Backup and recovery plan documented

## System Requirements

### Server Requirements
- Operating System: Linux/Windows Server/macOS
- Python: 3.7 or higher
- RAM: Minimum 2GB (4GB+ recommended)
- Storage: 10GB+ for application and data
- Network: Stable internet connection
- Port 443 (HTTPS) - open and available
- Port 80 (HTTP) - open for redirects

### Database Requirements
- SQLite3 (included in Python) for small deployments
- Or: PostgreSQL/MySQL for larger deployments
- Database size: 100MB+ free space

### Browser Compatibility
- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions

## Pre-Deployment Setup

### 1. Clone/Transfer Application Files
```bash
# Copy project files to server
# Option A: Git clone
git clone <repository-url> /opt/ea-tutorial-hub

# Option B: Direct file transfer
scp -r "Project EA" user@server:/opt/ea-tutorial-hub
```

### 2. Create Virtual Environment
```bash
cd /opt/ea-tutorial-hub
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create .env File
```bash
# Create .env file in project root
cat > .env << EOF
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
DATABASE_URL=sqlite:///ea_tutorial.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/ea_tutorial
UPLOAD_FOLDER=app/static/uploads
MAX_CONTENT_LENGTH=52428800
DEBUG=False
EOF
```

### 5. Initialize Database
```bash
# Activate virtual environment first
source venv/bin/activate  # or: venv\Scripts\activate

# Run initialization script
python init_sample_data.py

# Expected output:
# [OK] Database reset complete
# [OK] Admin created: Admin (password: admin123)
# [OK] Teacher created: Teacher (password: teacher123)
# [OK] Student created: EA24C01 (password: student123)
# [OK] SAMPLE DATA INITIALIZATION COMPLETE!
```

### 6. Create Upload Directory
```bash
mkdir -p app/static/uploads
chmod 755 app/static/uploads
```

## Production Server Configuration

### Option A: Using Gunicorn (Recommended)

1. **Install Gunicorn:**
```bash
pip install gunicorn
```

2. **Create systemd service file** (`/etc/systemd/system/ea-tutorial-hub.service`):
```ini
[Unit]
Description=EA Tutorial Hub Flask Application
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/ea-tutorial-hub
ExecStart=/opt/ea-tutorial-hub/venv/bin/gunicorn \
          --workers 4 \
          --worker-class sync \
          --bind 127.0.0.1:5000 \
          --timeout 60 \
          run:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

3. **Enable and start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable ea-tutorial-hub
sudo systemctl start ea-tutorial-hub
```

4. **Check status:**
```bash
sudo systemctl status ea-tutorial-hub
```

### Option B: Using Nginx as Reverse Proxy

1. **Install Nginx:**
```bash
sudo apt-get install nginx
```

2. **Create Nginx configuration** (`/etc/nginx/sites-available/ea-tutorial-hub`):
```nginx
upstream ea_tutorial {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    client_max_body_size 50M;

    location / {
        proxy_pass http://ea_tutorial;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/ea-tutorial-hub/app/static/;
        expires 30d;
    }
}
```

3. **Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/ea-tutorial-hub /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Option C: Using Apache with mod_wsgi

1. **Install Apache and mod_wsgi:**
```bash
sudo apt-get install apache2 libapache2-mod-wsgi-py3
```

2. **Create WSGI application file** (`/opt/ea-tutorial-hub/app.wsgi`):
```python
import sys
sys.path.insert(0, '/opt/ea-tutorial-hub')

from app import create_app
app = create_app()

if __name__ == "__main__":
    app.run()
```

3. **Create Apache configuration** (`/etc/apache2/sites-available/ea-tutorial-hub.conf`):
```apache
<VirtualHost *:443>
    ServerName example.com
    ServerAlias www.example.com
    
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/example.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/example.com/privkey.pem

    WSGIDaemonProcess ea_tutorial python-home=/opt/ea-tutorial-hub/venv
    WSGIProcessGroup ea_tutorial
    WSGIScriptAlias / /opt/ea-tutorial-hub/app.wsgi

    <Directory /opt/ea-tutorial-hub>
        WSGIProcessGroup ea_tutorial
        WSGIApplicationGroup %{GLOBAL}
        Order allow,deny
        Allow from all
    </Directory>

    Alias /static /opt/ea-tutorial-hub/app/static
    <Directory /opt/ea-tutorial-hub/app/static>
        Order allow,deny
        Allow from all
    </Directory>
</VirtualHost>

<VirtualHost *:80>
    ServerName example.com
    ServerAlias www.example.com
    Redirect permanent / https://example.com/
</VirtualHost>
```

4. **Enable site:**
```bash
sudo a2enmod ssl
sudo a2ensite ea-tutorial-hub
sudo apache2ctl -t
sudo systemctl restart apache2
```

## SSL/TLS Configuration

### Using Let's Encrypt (Free)

1. **Install Certbot:**
```bash
sudo apt-get install certbot python3-certbot-nginx
# Or for Apache:
# sudo apt-get install certbot python3-certbot-apache
```

2. **Obtain certificate:**
```bash
# For Nginx:
sudo certbot certonly --nginx -d example.com -d www.example.com

# For Apache:
# sudo certbot certonly --apache -d example.com -d www.example.com
```

3. **Auto-renewal (optional):**
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

## Database Backup & Recovery

### Automated Backups

1. **Create backup script** (`/opt/ea-tutorial-hub/backup.sh`):
```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/ea-tutorial-hub"
mkdir -p $BACKUP_DIR

# SQLite backup
cp /opt/ea-tutorial-hub/ea_tutorial.db $BACKUP_DIR/ea_tutorial_$(date +%Y%m%d_%H%M%S).db

# Keep only last 30 days of backups
find $BACKUP_DIR -type f -mtime +30 -delete

# Optional: Upload to cloud storage
# aws s3 sync $BACKUP_DIR s3://my-backup-bucket/ea-tutorial-hub/
```

2. **Schedule with cron** (daily 2 AM):
```bash
0 2 * * * /opt/ea-tutorial-hub/backup.sh
```

### Recovery Procedure

1. **Stop the application:**
```bash
sudo systemctl stop ea-tutorial-hub
```

2. **Restore database:**
```bash
cp /opt/backups/ea-tutorial-hub/ea_tutorial_YYYYMMDD_HHMMSS.db /opt/ea-tutorial-hub/ea_tutorial.db
```

3. **Restart application:**
```bash
sudo systemctl start ea-tutorial-hub
```

## Monitoring & Logging

### Application Logging

1. **Configure Flask logging** (in `run.py`):
```python
import logging
from logging.handlers import RotatingFileHandler
import os

if not app.debug and not app.testing:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/ea_tutorial.log', 
                                       maxBytes=10240000, 
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('EA Tutorial Hub startup')
```

2. **View logs:**
```bash
tail -f /opt/ea-tutorial-hub/logs/ea_tutorial.log
```

### Performance Monitoring

1. **Monitor system resources:**
```bash
# Check memory usage
free -h

# Check disk usage
df -h

# Check process status
ps aux | grep gunicorn
```

2. **Monitor application:**
```bash
# Check if service is running
sudo systemctl status ea-tutorial-hub

# View recent logs
sudo journalctl -u ea-tutorial-hub -n 50 -f
```

## Security Hardening

### Essential Security Steps

1. **Update system packages:**
```bash
sudo apt-get update && sudo apt-get upgrade
```

2. **Configure firewall:**
```bash
sudo ufw enable
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw status
```

3. **Secure .env file:**
```bash
chmod 600 /opt/ea-tutorial-hub/.env
sudo chown www-data:www-data /opt/ea-tutorial-hub/.env
```

4. **Change default credentials:**
```python
# After deployment, change admin password
# Login as Admin and use "Change Password" feature
```

5. **Enable HSTS** (in Nginx):
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

6. **Disable debug mode:**
```bash
# In .env
DEBUG=False
FLASK_ENV=production
```

## First-Time Setup Checklist

After deployment:

- [ ] Application accessible at domain
- [ ] SSL/TLS working (green lock in browser)
- [ ] Admin login works (Admin / admin123)
- [ ] Teacher login works (Teacher / teacher123)
- [ ] Student login works (EA24C01 / student123)
- [ ] Database initialization complete
- [ ] File uploads working
- [ ] Activity logs recording
- [ ] Password change functionality works
- [ ] Admin can reset user passwords
- [ ] Backups running automatically
- [ ] Logs being written
- [ ] Performance acceptable (<2s page load)

## Maintenance Schedule

### Daily
- [ ] Check application is running: `sudo systemctl status ea-tutorial-hub`
- [ ] Review error logs: `tail -f logs/ea_tutorial.log`
- [ ] Verify backups completed

### Weekly
- [ ] Review activity logs for suspicious activity
- [ ] Check disk space: `df -h`
- [ ] Review user registrations

### Monthly
- [ ] Update system packages: `sudo apt-get update && upgrade`
- [ ] Verify database integrity
- [ ] Review and archive old logs
- [ ] Test backup restoration

### Quarterly
- [ ] Security audit
- [ ] Performance optimization
- [ ] Database optimization
- [ ] Review and update documentation

## Troubleshooting

### Application won't start
```bash
# Check Python syntax
python -m py_compile run.py

# Check logs
journalctl -u ea-tutorial-hub -n 50

# Test Gunicorn directly
gunicorn --bind 127.0.0.1:5000 run:app
```

### Port already in use
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>
```

### Database locked
```bash
# Stop application
sudo systemctl stop ea-tutorial-hub

# Check for stale processes
ps aux | grep python

# Restart application
sudo systemctl start ea-tutorial-hub
```

### High memory usage
```bash
# Check Gunicorn workers
ps aux | grep gunicorn

# Reduce workers in systemd service
# (typically 2-4 per CPU core)

# Restart service
sudo systemctl restart ea-tutorial-hub
```

## Support & Escalation

For issues or support:
1. Check application logs
2. Review Activity Log in admin dashboard
3. Verify system resources
4. Contact development team with:
   - Error message
   - Steps to reproduce
   - System information
   - Recent log entries

## Post-Deployment Validation

After successful deployment:

```bash
# Test connectivity
curl -I https://example.com

# Verify SSL
openssl s_client -connect example.com:443

# Check application health
curl https://example.com/auth/login

# Verify database
python -c "from app import db; db.engine.execute('SELECT 1')"

# Test file uploads
# (Upload a PDF through web interface)

# Monitor performance
# (Run sample quiz and measure page load time)
```

## Conclusion

Your EA Tutorial Hub Phase 3 deployment is complete. For ongoing support and updates, refer to the main README.md and other documentation files.

**Application Address:** https://example.com
**Admin Contact:** admin@example.com
**Support Email:** support@example.com
