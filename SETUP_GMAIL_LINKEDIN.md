# 🔧 Gmail & LinkedIn Setup Guide

This guide walks you through configuring Gmail and LinkedIn job search integration.

---

## 📧 **Gmail Configuration (Email Reports)**

### **Step 1: Create Google Cloud Project**

1. **Visit Google Cloud Console:**
   ```
   https://console.cloud.google.com
   ```

2. **Create New Project:**
   - Click "Select a Project" (top left)
   - Click "NEW PROJECT"
   - Name: `Job Application System`
   - Click "CREATE"
   - Wait for initialization (2-3 minutes)

3. **Enable Gmail API:**
   - In the search bar, type "Gmail API"
   - Click "Gmail API" from results
   - Click "ENABLE"

### **Step 2: Create OAuth 2.0 Credentials**

1. **Go to Credentials:**
   - Left sidebar → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"

2. **Configure OAuth Consent Screen (if prompted):**
   - User Type: Select "External"
   - App name: `Job Application System`
   - User support email: `shanawar.shahbaz6@gmail.com`
   - Developer contact: `shanawar.shahbaz6@gmail.com`
   - Scopes: Accept defaults
   - Click "SAVE AND CONTINUE" → "SAVE AND CONTINUE" → "BACK TO DASHBOARD"

3. **Create OAuth Credentials:**
   - Go back to "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop application"
   - Name: `Job Application System`
   - Click "CREATE"

### **Step 3: Download & Configure Credentials**

1. **Download the JSON file:**
   - Next to your newly created credential, click the download icon (↓)
   - Save the file

2. **Move to correct location:**
   ```bash
   mv ~/Downloads/client_secret_*.json job_application_system/gmail_credentials.json
   ```

3. **Verify file location:**
   ```bash
   ls -la job_application_system/gmail_credentials.json
   ```

### **Step 4: Activate Gmail Integration**

When you first run the system:

```bash
python job_scheduler.py --mode once
```

The system will:
1. Detect the credentials file
2. Open your browser for authentication
3. Ask you to sign in with your Google account
4. Create a token file (`gmail_token.json`)
5. Send your first email report ✅

**After first run, emails will be sent automatically every day.**

---

## 💼 **LinkedIn Configuration (Job Search)**

### **Option 1: JSearch API (Recommended ⭐)**

JSearch API searches across **LinkedIn, Indeed, Glassdoor, ZipRecruiter** and more.

**Advantages:**
- ✅ One API covers multiple job boards
- ✅ Includes LinkedIn jobs
- ✅ Free tier: 100 requests/month (sufficient for daily use)
- ✅ Easy setup, no approval needed

#### **Step 1: Get JSearch API Key**

1. **Visit RapidAPI:**
   ```
   https://rapidapi.com/laimoon/api/jsearch1
   ```

2. **Subscribe to Free Plan:**
   - Click "Subscribe to Test"
   - Select the free plan
   - Confirm

3. **Copy API Key:**
   - Go to "API Key" section
   - Copy your API key (looks like: `abc123xyz...`)

#### **Step 2: Add to .env File**

1. **Create .env file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env:**
   ```bash
   nano .env
   ```
   Or using your editor, replace:
   ```
   JSEARCH_API_KEY=your_jsearch_api_key_here
   ```
   With your actual key:
   ```
   JSEARCH_API_KEY=abc123xyz789...
   ```

3. **Save and exit**

4. **Verify installation:**
   ```bash
   pip install python-dotenv
   ```

#### **Step 3: Test Job Search**

```bash
python job_scheduler.py --mode once
```

You should see:
```
🔍 Starting job search across all roles and locations...

📌 Searching for 'AI Engineer' positions...
  🔍 Searching JSearch: 'AI Engineer' in Saudi Arabia...
    ✅ Found 25 jobs
  🔍 Searching JSearch: 'AI Engineer' in Dubai...
    ✅ Found 18 jobs
  ...

✅ Total unique jobs found: 156
```

---

### **Option 2: LinkedIn Official API (Advanced)**

If you want to use LinkedIn's official API:

1. **Apply for LinkedIn Official API:**
   ```
   https://business.linkedin.com/en-us/talent-solutions/career-pages/api
   ```

2. **Requirements:**
   - LinkedIn Business account
   - Company/HR account status
   - API approval process (2-4 weeks)
   - Monthly fee

3. **Use only if:**
   - You need direct LinkedIn access
   - You're managing recruitment at scale
   - You have LinkedIn approval

---

## 🔑 **Environment Variables Setup**

### **Full .env Configuration:**

```bash
# Job Search - JSearch API
JSEARCH_API_KEY=your_api_key_here

# Gmail Setup
GMAIL_ENABLED=true

# Job Application Settings
DAILY_APPLICATIONS=15
SCHEDULE_TIME=07:00
EMAIL_ADDRESS=shanawar.shahbaz6@gmail.com
```

### **How .env Works:**

The system automatically loads these variables from `.env` on startup:

```python
from dotenv import load_dotenv
import os

load_dotenv()  # Loads .env file
api_key = os.getenv("JSEARCH_API_KEY")
```

---

## 📊 **Verify Everything Works**

### **Test 1: Gmail Setup**
```bash
python job_scheduler.py --mode once
# Should see: "✅ Email sent successfully to shanawar.shahbaz6@gmail.com"
# Or: "📧 Email saved to file: job_application_system/emails/email_*.html"
```

### **Test 2: Job Search with LinkedIn/Indeed**
```bash
python job_scheduler.py --mode once
# Should see: "✅ Found X jobs" for each role and location
```

### **Test 3: Full System**
```bash
python job_scheduler.py --mode once
# Should see:
# ✅ Jobs Found: 150+
# ✅ Applications Submitted: 15
# ✅ Email Report Generated
```

---

## 🔐 **Security Best Practices**

### **Protect Your Credentials:**

1. **Never commit .env file:**
   ```bash
   # Already in .gitignore:
   echo ".env" >> .gitignore
   git add .gitignore && git commit -m "Update .gitignore"
   ```

2. **Never share credentials:**
   - Don't paste API keys in emails
   - Don't commit `gmail_credentials.json`
   - Don't share `.env` file

3. **Rotate credentials periodically:**
   ```bash
   # Every 3 months: Regenerate Gmail credentials
   # Delete old gmail_token.json and re-authenticate
   ```

4. **Use environment variables in production:**
   ```bash
   # On servers, set via environment, not files:
   export JSEARCH_API_KEY="your_key"
   python job_scheduler.py --mode schedule
   ```

---

## ⚠️ **Troubleshooting**

### **Issue: "JSearch API key not found"**
**Solution:**
- Check `.env` file exists: `ls -la .env`
- Verify API key is set: `grep JSEARCH_API_KEY .env`
- Make sure there are no extra spaces around `=`

### **Issue: "Invalid API key" or "401 Unauthorized"**
**Solution:**
- Go back to RapidAPI
- Check your API key is correct
- Copy again and update `.env`
- Try: `python job_scheduler.py --mode once`

### **Issue: "Gmail credentials not found"**
**Solution:**
- Check file exists: `ls -la job_application_system/gmail_credentials.json`
- If not, re-download from Google Cloud Console
- Run system again: `python job_scheduler.py --mode once`

### **Issue: "Rate limit reached (100 requests/month)"**
**Solution:**
- JSearch free tier = 100 requests/month
- That's ~3 per day, sufficient for daily use
- Upgrade to paid plan if you need more
- Or wait for reset (next month)

### **Issue: No jobs found even with API key**
**Solution:**
- Check jobs exist for your search terms
- Test manually on Indeed/LinkedIn
- Try different role names
- Check internet connection
- Review logs: `tail -f job_application_system/scheduler.log`

---

## 📈 **Daily Job Search Examples**

### **What gets searched:**
```
Roles:
  - AI Engineer
  - LLM Engineer
  - Machine Learning Engineer
  - Forward Deploy Engineer
  - ML DevOps Engineer

Locations:
  - Saudi Arabia
  - Dubai
  - KSA

Expected Results Per Day:
  - 100-200 jobs found
  - 15 applications submitted
  - Customized CVs for each role match
```

### **Sample Results:**
```
✅ Found AI Engineer in Saudi Arabia (25 jobs)
✅ Found LLM Engineer in Dubai (18 jobs)
✅ Found ML DevOps in KSA (12 jobs)
✅ Found Forward Deploy in Saudi Arabia (20 jobs)
...

Total: 156 jobs found
New opportunities: 142 (excluding previously applied)
Applications submitted: 15

Email Report Sent: shanawar.shahbaz6@gmail.com
```

---

## ✅ **Final Checklist**

Before starting daily automation:

- [ ] Gmail credentials downloaded and placed in `job_application_system/`
- [ ] .env file created with JSEARCH_API_KEY
- [ ] Test run completed: `python job_scheduler.py --mode once`
- [ ] Email report received or saved to file
- [ ] At least 50+ jobs found in test run
- [ ] No error messages in output
- [ ] applications_tracking.csv populated with test apps
- [ ] Ready to run: `python job_scheduler.py --mode schedule`

---

## 🚀 **Start Daily Automation**

Once everything is configured:

```bash
# Option 1: Run in background (simple)
python job_scheduler.py --mode schedule &

# Option 2: Run in tmux (better)
tmux new-session -d -s job-applications
tmux send-keys -t job-applications 'cd /home/user/rag-prod && python job_scheduler.py --mode schedule' Enter

# Option 3: Run as systemd service (production)
sudo systemctl enable job-applications
sudo systemctl start job-applications
```

---

## 📞 **Next Steps**

1. ✅ Get JSearch API key (5 minutes)
2. ✅ Create .env file (2 minutes)
3. ✅ Download Gmail credentials (5 minutes)
4. ✅ Test: `python job_scheduler.py --mode once` (1 minute)
5. ✅ Start scheduler: `python job_scheduler.py --mode schedule` (1 minute)

**Total setup time: ~15 minutes**

**System then runs completely automatically every day at 7:00 AM KSA time!** 🎉

---

**Questions?** Check the logs:
```bash
tail -f job_application_system/scheduler.log
```

**All systems go!** 🚀
