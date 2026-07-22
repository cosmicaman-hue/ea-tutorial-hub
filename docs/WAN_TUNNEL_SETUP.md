# Global WAN Synchronization & Cloudflare Tunnel Setup Guide

This guide provides step-by-step instructions to securely expose the local **EA Scoreboard Server** running on your classroom PC to the internet using **Cloudflare Tunnels (Option B)**. This allows teachers and students to securely sync scores, update rosters, and receive real-time background notifications from anywhere in the world on their Android devices.

---

## 🔒 Why Cloudflare Tunnels?

Exposing a local server normally requires Port Forwarding on your router and a static public IP address. This poses significant security risks, as it leaves open ports vulnerable to public scanning. 

**Cloudflare Tunnels** solve this by:
- Creating a secure, **outgoing-only** connection from your local classroom PC to Cloudflare's edge network.
- Eliminating the need to touch your router configuration or open incoming ports (like 80/443 or 5000).
- Providing automatic **SSL/TLS encryption** (HTTPS) out of the box.
- Allowing granular firewall rules to prevent unauthorized traffic from hitting your local server.

---

## 🛠️ Step 1: Install `cloudflared` on the Classroom PC

1. **Download the Cloudflare Tunnel CLI (`cloudflared`)**:
   - Go to the [Cloudflare Downloads page](https://github.com/cloudflare/cloudflared/releases) and download the Windows version (`cloudflared-windows-amd64.msi` or `.exe`).
   - Alternatively, you can download it via PowerShell:
     ```powershell
     Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.msi" -OutFile "$env:TEMP\cloudflared.msi"
     Start-Process msiexec.exe -ArgumentList "/i $env:TEMP\cloudflared.msi /quiet /qn" -Wait
     ```

2. **Verify Installation**:
   - Open PowerShell or Command Prompt as Administrator and run:
     ```cmd
     cloudflared --version
     ```
   - If it returns the version string, the installation was successful!

---

## 🔑 Step 2: Authenticate with Cloudflare

To hook the tunnel into your custom domain or a free subdomain:

1. **Log in via CLI**:
   - In PowerShell, run the login command:
     ```cmd
     cloudflared tunnel login
     ```
   - A browser window will automatically open. Log in to your Cloudflare account (create one for free if you don't have one).
   - Select a domain you have registered in Cloudflare to authorize the tunnel.
   - Once authorized, `cloudflared` will download a certificate (`cert.pem`) into your user profile directory (e.g. `C:\Users\<YourUser>\.cloudflared\cert.pem`).

---

## 🚀 Step 3: Create the Tunnel

Now create a persistent tunnel that will host your scoreboard service:

1. **Create the tunnel**:
   - Run the following command (replace `ea-scoreboard-tunnel` with your desired tunnel name):
     ```cmd
     cloudflared tunnel create ea-scoreboard-tunnel
     ```
   - This command will return a **Tunnel UUID** (e.g., `a1b2c3d4-e5f6-7a8b-9c0d-e1f2a3b4c5d6`) and generate a credentials JSON file in your `.cloudflared` directory.

2. **Configure the Tunnel Route**:
   - Map your tunnel to a public subdomain. Run the following command:
     ```cmd
     cloudflared tunnel route dns ea-scoreboard-tunnel sync.yourdomain.com
     ```
   - *Note: Replace `sync.yourdomain.com` with a domain or subdomain managed in your Cloudflare account.* This automatically configures a CNAME record in your DNS settings.

---

## 📝 Step 4: Write the Configuration File

Create a configuration file named `config.yml` inside the `.cloudflared` folder (e.g. `C:\Users\<YourUser>\.cloudflared\config.yml`) to define which port the tunnel redirects traffic to:

```yaml
tunnel: a1b2c3d4-e5f6-7a8b-9c0d-e1f2a3b4c5d6 # Replace with your Tunnel UUID
credentials-file: C:\Users\<YourUser>\.cloudflared\a1b2c3d4-e5f6-7a8b-9c0d-e1f2a3b4c5d6.json # Replace with your JSON path

ingress:
  # Route scoreboard API and web traffic to the local Waitress / Flask server port (default 5000)
  - hostname: sync.yourdomain.com
    service: http://localhost:5000
  
  # Catch-all rule returning a 404 for any other request
  - service: http_status:404
```

---

## ⚙️ Step 5: Install & Run as a Windows Service (Autostart)

To ensure the tunnel starts automatically when the Windows server boots up, install it as a native Windows Service:

1. **Install the service**:
   - Open PowerShell **as Administrator** and run:
     ```cmd
     cloudflared --config C:\Users\<YourUser>\.cloudflared\config.yml service install
     ```

2. **Start the service**:
   - Start the service immediately and set it to automatic:
     ```powershell
     Start-Service -Name "Cloudflare Tunnel"
     Set-Service -Name "Cloudflare Tunnel" -StartupType Automatic
     ```

3. **Verify Connection**:
   - Visit `https://sync.yourdomain.com` from a phone or external network.
   - It should securely serve the EA Scoreboard homepage with a valid HTTPS certificate!

---

## 📱 Step 6: Connect the Android Application

To link the Android App to your new WAN endpoint:

1. **Open the App Settings**:
   - Launch the **EA Scoreboard** app on your Android device.
   - Click the **Gear Icon** in the top-right corner to open the glassmorphic Settings Panel.

2. **Configure Credentials**:
   - Enter your public WAN URL: `https://sync.yourdomain.com`
   - Enter your unique **Login ID** (e.g. `T-SMITH` for teacher, or student roll number).
   - Enter the current active **Login Code** (see Step 7 below).
   - Click **Save Configurations**. The app will test the connection, sync the database, and begin background polling!

---

## 🔑 Step 7: Managing Monthly Login Codes (Admin Tasks)

To keep score submission secure and prevent leakages, credentials expire monthly.

### How Admin Resets Login Codes
The Admin can regenerate fresh codes for all active users at the beginning of each calendar month:
1. Open the local Server Admin Panel (or send a POST request to `/auth/admin/reset-codes` on the server).
2. The server invalidates all previous codes and generates random 6-character, high-entropy unique codes (e.g. `T-589A`, `S-90B1`).
3. These codes are valid until **the last second of the current calendar month** (`23:59:59` of the last day).
4. The Admin prints or securely shares the unique code with each respective teacher or student.

### Auto-Reset Hook
The server has an integrated startup hook that checks the calendar month. If a request is received in a new month (e.g. June) but codes are marked for an older month (e.g. May), the server will automatically invalidate them and prompt the user to request a fresh code from the Admin.
