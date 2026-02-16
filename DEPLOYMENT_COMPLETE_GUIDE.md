# 🚀 Complete Deployment Guide - All Options

**Consolidated guide for EA Tutorial Hub deployment across all platforms**

---

## 🎯 Quick Decision Tree

```
↓ Choose your deployment scenario:

Are you deploying locally?
├─ YES (Windows PC/Server) → Jump to "Local Windows Setup"
└─ NO → Continue below

Do you have a domain & budget?
├─ YES ($50+/month) → Jump to "Production Hosting"
└─ NO → Jump to "Free Cloud Options"

Want simplest setup?
└─ → Replit or PythonAnywhere (both FREE)
```

---

## Quick Links to Specific Guides

| Scenario | Time | Cost | Go To |
|----------|------|------|-------|
| **Local Windows Setup** | 15 min | $0 | [LOCAL_WINDOWS_DEPLOYMENT](#local-windows-deployment) |
| **Free PythonAnywhere** | 20 min | $0 | [PYTHONANYWHRE_DEPLOYMENT](#pythonanywhre-free-deployment) |
| **Free Replit** | 30 min | $0 | [REPLIT_DEPLOYMENT](#replit-free-deployment) |
| **Production Hosting** | 1-2 hrs | $5-20/mo | [PRODUCTION_HOSTING](#production-hosting) |
| **Network/Cluster** | 2 hrs | $0-100/mo | [NETWORK_DEPLOYMENT](#network-deployment) |

---

## Local Windows Deployment

**Best For:** Testing, learning, small school (single computer)  
**Cost:** FREE  
**Time:** 15 minutes

### Prerequisites
- Windows 10 or later
- Python 3.8+
- 500MB free disk space

### Setup Steps

#### 1. Activate Virtual Environment
```powershell
cd "c:\Users\sujit\Desktop\Project EA"
.venv\Scripts\Activate.ps1
```

#### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

#### 3. Run the Application
```powershell
python run.py
```

#### 4. Access Application
```
http://127.0.0.1:5000
```

### Default Login Credentials
```
Admin: Admin / admin123
Teacher: Teacher / teacher123
Student: EA24C01 / student123
```

### Making Computer Accessible to Others

#### Option A: Same Network (WiFi/LAN)
1. Find your computer's IP address:
   ```powershell
   ipconfig
   ```
   Look for "IPv4 Address" (usually 192.168.x.x)

2. Share URL with others on same network:
   ```
   http://[YOUR-IP]:5000
   Example: http://192.168.1.100:5000
   ```

#### Option B: Port Forwarding (Advanced)
1. Configure router port forwarding
2. Forward port 5000 to your computer
3. Share public IP address with others
4. ⚠️ Security warning: Only for trusted networks

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 5000 already in use | Change port in `run.py`: `app.run(port=5001)` |
| Virtual env not found | Create new: `python -m venv .venv` |
| Modules not found | Run: `pip install -r requirements.txt` |

---

## PythonAnywhere (Free Deployment)

**Best For:** Teachers wanting a live URL, students accessing from anywhere  
**Cost:** FREE (with limitations) or $5/month for custom domain  
**Time:** 20 minutes

### Prerequisites
- GitHub account (free)
- PythonAnywhere account (free)

### Step-by-Step Setup

#### 1. Create GitHub Account (if needed)
```
Go to: https://github.com/signup
Create account with your email
Verify email
```

#### 2. Push Code to GitHub
```powershell
cd "c:\Users\sujit\Desktop\Project EA"
git init
git add .
git commit -m "Initial upload"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/ea-tutorial-hub.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username.

#### 3. Create PythonAnywhere Account
```
Go to: https://www.pythonanywhere.com
Click "Sign up"
Choose free plan
Verify email
```

#### 4. Deploy from GitHub
```
1. Go to Consoles (left menu)
2. Click "Bash"
3. Clone your repo:
   git clone https://github.com/YOUR-USERNAME/ea-tutorial-hub.git
4. Go to Web (left menu)
5. Add new web app
6. Choose Flask
7. Choose Python 3.11
8. Point to /ea-tutorial-hub folder
```

#### 5. Configure .env File
```
1. Go to Files (left menu)
2. Navigate to /ea-tutorial-hub
3. Create .env file:
   FLASK_APP=run.py
   FLASK_ENV=production
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=sqlite:///ea_tutorial.db
```

#### 6. Reload Web App
```
1. Go to Web (left menu)
2. Click "Reload" button
```

#### 7. Access Your App
```
Your URL: https://YOUR-USERNAME.pythonanywhere.com
Example: https://john123.pythonanywhere.com
```

### PythonAnywhere Limitations (Free Tier)
- App sleeps after 100 minutes of inactivity
- Limited to 100 HTTP hits per day (counting any request)
- 512MB disk space
- No custom domain

### To Remove Limitations
- Upgrade to Beginner ($5/month) for:
  - Always-on web app
  - Unlimited web hits
  - 1GB disk space
  - Custom domain support

---

## Replit (Free Deployment)

**Best For:** Quick deployment, shared link with class  
**Cost:** FREE (with limitations) or $7/month Pro  
**Time:** 30 minutes

### Prerequisites
- GitHub account
- Replit account

### Setup Steps

#### 1. Push Code to GitHub (same as PythonAnywhere)
```powershell
# See "Push Code to GitHub" section above
```

#### 2. Create Replit Account
```
Go to: https://replit.com
Sign up with GitHub
```

#### 3. Import from GitHub
```
1. Click "Create" (top left)
2. Select "Import from GitHub"
3. Paste: https://github.com/YOUR-USERNAME/ea-tutorial-hub
4. Click "Import"
```

#### 4. Install Dependencies
```
1. Click "Shell" tab
2. Run: pip install -r requirements.txt
3. Wait for installation
```

#### 5. Run Application
```
In Shell, run: python run.py

Or click "Run" button (if configured)
```

#### 6. Access Your App
```
Replit generates a URL like:
https://ea-tutorial-hub.USERNAME.repl.co

Share this with your students
```

### Replit Considerations
- Apps go offline after 1 hour of inactivity (free tier)
- Upgrade to Pro ($7/month) for always-on
- Good for demonstrations and learning
- Has built-in code editor

---

## Production Hosting

**Best For:** Long-term deployment, 100+ users, custom domain  
**Cost:** $5-50/month depending on traffic  
**Time:** 1-2 hours setup

### Recommended Providers

#### 1. **Render.com** (Recommended)
- **Cost:** $7-18/month
- **Setup Time:** 30 minutes
- **Features:** Easy deployment, custom domain, SSL included
- **Best For:** Small to medium schools

**Quick Deploy:**
```
1. Go to: https://render.com
2. Sign up
3. Click "New" → "Web Service"
4. Connect GitHub repo
5. Select Python environment
6. Deploy
```

#### 2. **Railway.app**
- **Cost:** $5-20/month
- **Setup Time:** 30 minutes
- **Features:** Developer-friendly, GitHub integration
- **Best For:** Technical users

#### 3. **DigitalOcean**
- **Cost:** $6-24/month
- **Setup Time:** 1-2 hours
- **Features:** Full control, scalable, SSH access
- **Best For:** Advanced users, large deployments

#### 4. **Heroku** (Legacy - being phased out)
- **Cost:** $7-50/month
- **Note:** Limited free tier as of 2024

### Production Deployment Checklist
- [ ] Custom domain purchased ($10-15/year)
- [ ] SSL certificate configured (usually free)
- [ ] Database backed up
- [ ] Email notifications configured (optional)
- [ ] Monitoring set up
- [ ] Disaster recovery plan

### Domain Options
- `learnea.com` - Simple, memorable
- `eacademy.online` - Clearly educational
- `[schoolname]-academy.com` - Branded
- Cost: $10-15/year from GoDaddy, Namecheap, Google Domains

---

## Network Deployment

**Best For:** Deploying to school network, 24/7 server  
**Cost:** $0-100/month (depending on existing hardware)  
**Time:** 2-4 hours

### Option 1: Dedicated Server (Recommended)

#### Hardware Requirements
- Processor: 2-4 cores
- RAM: 4-8GB
- Storage: 100GB SSD
- Network: Gigabit Ethernet
- OS: Windows Server 2022 or Linux

#### Setup
1. Install Python 3.8+
2. Clone application code
3. Install Flask with Gunicorn
4. Configure Nginx reverse proxy
5. Set up SSL with Let's Encrypt
6. Configure firewall rules

See: [NETWORK_DEPLOYMENT_GUIDE.md](NETWORK_DEPLOYMENT_GUIDE.md)

### Option 2: School Network PC
- Use as always-on application server
- Configure Windows startup scripts
- Set up UPS for power stability
- Use dynamic DNS for access

See: [SERVER_PC_SETUP_GUIDE.md](SERVER_PC_SETUP_GUIDE.md)

---

## Offline Deployment

**Best For:** Schools without reliable internet, standalone system  
**Cost:** FREE (except hardware)

See: [README_OFFLINE_SYSTEM.md](README_OFFLINE_SYSTEM.md)

Features:
- ✅ Works without internet
- ✅ Data saved locally
- ✅ Full feature access
- ✅ Can sync when online

---

## Deployment Comparison Matrix

| Feature | Local | PythonAnywhere | Replit | Production | Network |
|---------|-------|---|--------|-----------|---------|
| **Setup Time** | 15 min | 20 min | 30 min | 1-2 hrs | 2-4 hrs |
| **Cost** | FREE | FREE/$5 | FREE/$7 | $5+ | $0-100 |
| **Users** | 5-10 | 10-100 | 5-50 | 100-1000+ | 100-500 |
| **Uptime** | 50% | 95% | 80% | 99%+ | 99%+ |
| **Custom Domain** | ❌ | ✅ | ❌ | ✅ | ✅ |
| **Always On** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Easy Setup** | ✅ | ✅ | ✅ | ⚠️ | ⚠️ |
| **Scalable** | ❌ | Limited | Limited | ✅ | ✅ |

---

## 🔒 Security Checklist

Before going live:
- [ ] Change default Admin/Teacher passwords
- [ ] Generate new SECRET_KEY
- [ ] Set FLASK_ENV=production
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall rules
- [ ] Set up regular backups
- [ ] Configure database backups
- [ ] Test authentication thoroughly
- [ ] Review file upload settings
- [ ] Monitor activity logs

---

## 📊 Performance Tips

### Small School (50-200 users)
- Use SQLite database
- Deploy to PythonAnywhere or Replit
- Monitor activity with dashboards
- Backup weekly

### Medium School (200-1000 users)
- Upgrade to PostgreSQL database
- Use Production hosting (Render, Railway)
- Enable caching
- Monitor performance metrics
- Backup daily

### Large Deployment (1000+ users)
- Use PostgreSQL with read replicas
- Deploy to infrastructure service
- Configure load balancing
- Set up CDN for static files
- Backup hourly
- Monitor with APM tools

---

## Troubleshooting

### Application Won't Start
```
1. Check Python version: python --version
2. Verify dependencies: pip install -r requirements.txt
3. Check port availability: netstat -an | findstr :5000
4. Review error logs
```

### Database Issues
```
1. Verify database_url in .env
2. Check database permissions
3. Try: python -c "from app import db; db.create_all()"
```

### Connection Issues
```
1. If local: Check firewall
2. If cloud: Check security groups
3. Verify IP whitelisting
4. Check database connection string
```

---

## 🆘 Getting Help

| Issue | Resource |
|-------|----------|
| PythonAnywhere setup | [PYTHONANYWHRE_COMPLETE_GUIDE.md](PYTHONANYWHRE_COMPLETE_GUIDE.md) |
| Replit setup | [REPLIT_DEPLOYMENT_GUIDE.md](REPLIT_DEPLOYMENT_GUIDE.md) |
| Network setup | [NETWORK_DEPLOYMENT_GUIDE.md](NETWORK_DEPLOYMENT_GUIDE.md) |
| Windows PC setup | [SERVER_PC_COMPLETE_SETUP.md](SERVER_PC_COMPLETE_SETUP.md) |
| General troubleshooting | [SERVER_OPERATIONS_GUIDE.md](SERVER_OPERATIONS_GUIDE.md) |

---

**Choose your deployment option above and follow the detailed guide. All options preserve your data - no data loss!**
