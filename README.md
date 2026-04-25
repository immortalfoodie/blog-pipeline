# Dev.to Blog Auto-Publisher — Selenium + Jenkins Pipeline
### Experiment 6 | STL | T.E. AI & DS — Sem VI

---

## Project Structure

```
blog-pipeline/
├── selenium/
│   └── devto_poster.py     ← Main Selenium script
├── Jenkinsfile              ← Jenkins pipeline definition
├── requirements.txt         ← Python packages
└── README.md
```

---

## How It Works (Pipeline Flow)

```
Jenkins (scheduler/trigger)
        │
        ▼
  Gemini AI API  ──►  Generate blog title + body
        │
        ▼
  Selenium (Chrome)
        │
        ├─► Log in to Dev.to
        ├─► Open New Post editor
        ├─► Fill Title + Body
        └─► Preview (optional) ──► Publish
```

---

## Step 1 — Prerequisites (Install Once)

```bash
# Python 3.8+
pip install selenium requests

# Google Chrome browser
# ChromeDriver (must match your Chrome version)
# Download: https://chromedriver.chromium.org/downloads
```

---

## Step 2 — Set Your Credentials

**Option A: Environment variables (recommended)**
```bash
export DEVTO_EMAIL="you@example.com"
export DEVTO_PASSWORD="yourpassword"
export GEMINI_API_KEY="your-gemini-api-key"
export BLOG_TOPIC="5 cool Python tricks for data scientists"
```

**Option B: Edit `devto_poster.py` directly**
Change the defaults at the top of the file under `# CONFIG`.

### Get a Gemini API Key
1. Go to https://aistudio.google.com/app/apikey
2. Create a new key (free tier available)
3. Copy and paste it into `GEMINI_API_KEY`

---

## Step 3 — Run Locally (Test First)

```bash
cd blog-pipeline

# Direct publish (no browser UI needed)
python selenium/devto_poster.py --mode auto

# Preview first, then approve manually
python selenium/devto_poster.py --mode preview

# Run headless (no browser window, for servers)
python selenium/devto_poster.py --mode auto --headless
```

---

## Step 4 — Set Up Jenkins

### 4a. Install Jenkins
```bash
# Ubuntu/Debian
sudo apt install jenkins

# Or use Docker
docker run -p 8080:8080 jenkins/jenkins:lts
```
Open: http://localhost:8080

### 4b. Install Jenkins Plugins
Go to **Manage Jenkins → Plugins** and install:
- Git Plugin
- Pipeline Plugin
- Credentials Binding Plugin

### 4c. Add Credentials in Jenkins
Go to **Manage Jenkins → Credentials → (global) → Add Credentials**

Add these 3 "Secret text" credentials:

| ID               | Value                  |
|------------------|------------------------|
| DEVTO_EMAIL      | your Dev.to email       |
| DEVTO_PASSWORD   | your Dev.to password    |
| GEMINI_API_KEY   | your Gemini API key     |

### 4d. Create a Pipeline Job
1. Click **New Item**
2. Name it: `DevTo-Blog-Publisher`
3. Select **Pipeline** → OK
4. Under **Pipeline**, choose **Pipeline script from SCM**
5. Set SCM = Git, add your repo URL
6. Script path = `Jenkinsfile`
7. Click **Save**

### 4e. Run On-Demand
Click **Build with Parameters** → Set topic & mode → **Build**

### 4f. Scheduled Daily Posts
The `Jenkinsfile` already has:
```groovy
triggers { cron('0 9 * * *') }
```
This runs **every day at 9:00 AM**. Change it to any cron schedule you want.

---

## Modes Explained

| Mode      | What Happens                                           |
|-----------|--------------------------------------------------------|
| `auto`    | AI generates → Selenium logs in → publishes directly  |
| `preview` | AI generates → opens browser → YOU approve → publish  |

---

## Common Issues

| Problem                        | Fix                                              |
|-------------------------------|--------------------------------------------------|
| ChromeDriver version mismatch | Match driver version to your Chrome version      |
| Login fails                   | Check email/password; Dev.to may need captcha    |
| Gemini returns empty content  | Check API key; try a different BLOG_TOPIC        |
| Jenkins can't find Chrome     | Install Chrome on the Jenkins machine            |

---

## Experiment Checklist

- [x] Selenium logs into Dev.to  
- [x] AI (Gemini) generates blog content  
- [x] Preview option with manual approval  
- [x] Direct publish option  
- [x] Jenkins on-demand runs  
- [x] Jenkins scheduled daily posting (cron)  
- [x] No blog platform APIs used for posting
