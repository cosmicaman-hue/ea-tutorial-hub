# 🌐 EA Tutorial Hub - Internet Hosting Guide

## Catchy URL Suggestions

Choose one of these memorable domain options for your students and teachers:

### 🎓 **Recommended Options** (Short & Catchy)

1. **`learnea.com`** ⭐ Simple, memorable, professional
2. **`eacademy.online`** - Clearly educational
3. **`tuitionea.app`** - Direct and clear
4. **`quizea.live`** - Perfect for quiz focus
5. **`studyea.pro`** - Professional and catchy

### 📚 **Alternative Options**

- `eahub.net`
- `ealearn.info`
- `tutoreat.com`
- `quiztime.online`
- `classea.io`
- `eaclass.tech`

### 💡 **Personalized Options** (Using your school name)

- `[schoolname]-ea.com`
- `[schoolname]-learn.com`
- `[schoolname]-academy.online`

---

## Complete Hosting Requirements

### **1. Domain & DNS**

#### Cost: $10-15/year
- Register domain from: GoDaddy, Namecheap, or Google Domains
- Point DNS to your hosting provider
- Setup SSL certificate (free with Let's Encrypt)

**Examples:**
```
Domain: learnea.com
DNS Records:
- A Record: points to your server IP
- CNAME: www → learnea.com
```

---

### **2. Server Requirements**

#### **Option A: Cloud Hosting (RECOMMENDED for 100-1000 users)**

**Cost: $5-20/month**

**Popular Providers:**
- **Render.com** - $7-18/month (easiest)
- **Railway.app** - $5-20/month (developer-friendly)
- **Heroku** - $7-50/month (reliable)
- **DigitalOcean** - $6-24/month (scalable)
- **AWS Lightsail** - $3.50-24/month (powerful)

**Minimum Specifications:**
- **CPU:** 1 core (2 cores recommended)
- **RAM:** 2GB minimum (4GB recommended)
- **Storage:** 20GB (50GB for larger deployments)
- **Bandwidth:** Unlimited or 1TB/month

---

#### **Option B: Dedicated Server (for 1000+ users)**

**Cost: $50-200+/month**

**Providers:**
- Bluehost, SiteGround, Hostgator, A2 Hosting
- Linode, Vultr, Hetzner

**Specifications:**
- **CPU:** 2-4 cores
- **RAM:** 4-8GB
- **Storage:** 100GB SSD
- **Bandwidth:** Unlimited

---

### **3. Database Setup**

#### **Option A: SQLite (Current - Small deployments)**

- **Users:** Up to 100
- **Size:** 50-500MB
- **Setup:** Already configured
- **Backup:** Daily to cloud storage
- **Cost:** $0 (included)

#### **Option B: PostgreSQL (Recommended for scale)**

- **Users:** 100-10,000+
- **Cost:** $15-100/month (managed services)
- **Providers:** AWS RDS, DigitalOcean, Heroku Postgres
- **Storage:** 10GB-1TB depending on plan

#### **Option C: MySQL**

- **Cost:** $10-50/month
- **Users:** Similar to PostgreSQL
- **Providers:** All major hosting companies

---

### **4. SSL/TLS Certificate**

#### **Cost: FREE or $10-100/year**

**Option A: Let's Encrypt (FREE)** ⭐ Recommended
```bash
# Automatic renewal, no cost
# Works with all hosting providers
# Certificate valid for 90 days (auto-renews)
```

**Option B: Paid Certificates**
- Comodo, DigiCert, Sectigo
- Cost: $50-200/year
- Longer validity (2-5 years)

---

### **5. Email Hosting** (Optional but recommended)

#### **Cost: $3-6/month**

**Providers:**
- Google Workspace: $6-14/month per user
- Zoho Mail: $2-5/month
- SendGrid: Free-$100/month (transactional emails)

**For:**
- Admin notifications
- Password reset emails
- Student alerts
- Teacher announcements

---

### **6. Backup & Recovery**

#### **Cost: $5-20/month**

**Recommended Setup:**
- Daily database backups
- Weekly full system backups
- Cloud storage (AWS S3, Google Cloud, Backblaze)
- 30-day retention minimum

**Providers:**
- AWS S3: $0.023 per GB
- DigitalOcean Spaces: $5/month
- Backblaze: $7/month
- Google Cloud Storage: Pay-per-use

---

### **7. Monitoring & Uptime**

#### **Cost: FREE-$30/month**

**Recommended Tools:**
- **Uptime Robot** (free): Monitors if site is up
- **New Relic** (free tier): Performance monitoring
- **DataDog** ($15+): Advanced monitoring
- **PagerDuty** ($15+): Alert management

---

### **8. CDN for Static Files** (Optional)

#### **Cost: FREE-$50/month**

**Benefits:**
- Faster page loads globally
- Reduce server bandwidth

**Providers:**
- Cloudflare: Free CDN included
- AWS CloudFront: $0.085 per GB
- Bunny CDN: $0.01 per GB

---

## Recommended Hosting Setup for EA Tutorial Hub

### **For Small School (100 students/teachers)**

```
Total Monthly Cost: $15-25

Components:
├─ Domain: $1/month (yearly ~$12)
├─ Cloud Server (Render/Railway): $7-15/month
├─ Database (PostgreSQL): $5/month
├─ SSL Certificate: FREE (Let's Encrypt)
├─ Backups: Built-in
└─ Monitoring: FREE (Uptime Robot)

Total: $15-25/month (~$200/year)
```

### **For Large School (500+ students/teachers)**

```
Total Monthly Cost: $40-80

Components:
├─ Domain: $1/month
├─ Cloud Server (DigitalOcean): $24/month
├─ PostgreSQL Database: $15/month
├─ SSL Certificate: FREE
├─ Email Service: $10/month
├─ Backups: $5/month
├─ Monitoring: $10/month
└─ CDN: $5-10/month

Total: $40-80/month (~$500-1000/year)
```

---

## Step-by-Step Deployment Guide

### **Step 1: Choose Provider & Domain**

**Recommended:** Render.com + Namecheap Domain

```
1. Visit namecheap.com
2. Search for domain (e.g., "learnea.com")
3. Add to cart and purchase
4. Save domain name & credentials
```

### **Step 2: Setup Render.com (Easy - 10 minutes)**

```bash
1. Go to render.com
2. Sign up with GitHub (recommended)
3. Connect your GitHub repository
4. Create new Web Service
5. Select Python 3.13
6. Build command: pip install -r requirements.txt
7. Start command: gunicorn run:app
8. Add environment variables:
   - SECRET_KEY: [generate random key]
   - DATABASE_URL: [Render PostgreSQL or SQLite]
   - FLASK_ENV: production
   - DEBUG: False
```

### **Step 3: Configure Database**

**Using Render PostgreSQL:**
```bash
1. In Render dashboard
2. Create new PostgreSQL database
3. Copy DATABASE_URL
4. Add to web service environment variables
5. Run migration (if needed)
```

### **Step 4: Connect Domain**

**In Namecheap:**
```
1. Go to Domain Settings
2. Nameservers tab
3. Add Render's nameservers:
   - ns1.render.com
   - ns2.render.com
   - ns3.render.com
   - ns4.render.com
```

**In Render:**
```
1. Web Service Settings
2. Custom Domains
3. Add your domain
4. SSL certificate auto-generates
```

### **Step 5: Configure App for Production**

**Update `run.py`:**
```python
import os
from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Production settings
    if os.getenv('FLASK_ENV') == 'production':
        app.run(
            host='0.0.0.0',
            port=int(os.getenv('PORT', 5000)),
            debug=False
        )
    else:
        app.run(debug=True)
```

### **Step 6: Initialize Production Database**

```bash
# SSH into server or use Render Shell
python init_sample_data.py

# Or create admin via Flask shell:
flask shell
>>> from app.models import User
>>> admin = User(login_id='Admin', role='admin')
>>> admin.set_password('admin123')
>>> db.session.add(admin)
>>> db.session.commit()
```

---

## Domain Configuration Examples

### **Example 1: learnea.com**

```
Access URLs:
├─ Main: https://learnea.com
├─ Login: https://learnea.com/auth/login
├─ Admin: https://learnea.com/admin/dashboard
├─ Register: https://learnea.com/auth/register
└─ Activity Log: https://learnea.com/admin/activity-log

Student Access:
Share link: https://learnea.com
Login: EA24C01
Password: [assigned by admin]
```

### **Example 2: eaacademy.online**

```
Access URLs:
├─ Main: https://eaacademy.online
├─ Admin: https://eaacademy.online/admin
├─ Activity: https://eaacademy.online/admin/activity-log
└─ Quizzes: https://eaacademy.online/quiz

Share with students:
"Visit https://eaacademy.online to login"
```

---

## Email Configuration (Optional)

### **For Password Reset Emails**

**Setup SendGrid:**

```python
# In .env
SENDGRID_API_KEY=your_api_key
SENDGRID_FROM_EMAIL=admin@learnea.com

# In app/__init__.py
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_password_reset_email(user_email, reset_link):
    message = Mail(
        from_email='admin@learnea.com',
        to_emails=user_email,
        subject='Password Reset - EA Tutorial Hub',
        html_content=f'<a href="{reset_link}">Reset Password</a>'
    )
    sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
    sg.send(message)
```

---

## Security Checklist for Production

- [ ] Change all default passwords
- [ ] Enable HTTPS/SSL (Let's Encrypt)
- [ ] Set strong SECRET_KEY
- [ ] Enable HSTS headers
- [ ] Configure WAF (Web Application Firewall)
- [ ] Set up automated backups
- [ ] Configure rate limiting
- [ ] Enable logging to external service
- [ ] Setup uptime monitoring
- [ ] Configure email for alerts
- [ ] Review PHASE_3_DEPLOYMENT.md security section

---

## Monitoring Your Live Site

### **Check if Site is Working:**

```bash
# Test from command line
curl -I https://learnea.com

# Should return HTTP 200
```

### **Monitor Performance:**

```bash
# Use Uptime Robot (free)
1. Go to uptimerobot.com
2. Add your domain
3. Gets emails if site goes down
```

### **View Server Logs:**

```bash
# Using Render.com
1. Go to Service Dashboard
2. Logs tab
3. Real-time log view
```

---

## Typical Costs Breakdown

| Item | Monthly | Annual |
|------|---------|--------|
| Domain | $1 | $12 |
| Server (Render) | $12 | $144 |
| Database | $5 | $60 |
| Email | $5 | $60 |
| Backups | $3 | $36 |
| SSL | $0 | $0 |
| Monitoring | $0 | $0 |
| **TOTAL** | **$26** | **$312** |

*Can be reduced to $12/month with smaller server*

---

## FAQ - Hosting

**Q: How many students/teachers can it handle?**
```
Small server: 100-500 concurrent users
Large server: 1000-5000 concurrent users
Enterprise: 5000+ with load balancing
```

**Q: Will it be fast?**
```
Yes! Cloud servers are optimized for web apps.
Expected page load: <1 second
Login response: <500ms
```

**Q: Is data secure?**
```
Yes with proper setup:
✓ HTTPS/SSL encryption
✓ Database encryption
✓ Automated backups
✓ Regular security updates
✓ Activity logging
```

**Q: What if I have more users later?**
```
Easy to scale:
- Increase server size: 2 minutes
- Add more servers: If needed
- No app changes required
```

**Q: How do I backup data?**
```
Automatic with all providers:
- Daily backups
- 30-day retention
- One-click restore
- Export to cloud storage
```

---

## Next Steps

1. **Choose a domain** from suggestions above
2. **Select hosting provider** (Render.com recommended)
3. **Follow deployment steps** in this guide
4. **Test with 5-10 users first**
5. **Monitor for 1 week**
6. **Roll out to all students/teachers**

---

## Support & Resources

- **Render Docs:** docs.render.com
- **Flask Deployment:** flask.palletsprojects.com/deployment
- **Let's Encrypt:** letsencrypt.org
- **PostgreSQL:** postgresql.org/docs

---

**Ready to launch? Follow PHASE_3_DEPLOYMENT.md for detailed server setup!**

🌐 **Your EA Tutorial Hub will be live and accessible to all your students!** 🌐
