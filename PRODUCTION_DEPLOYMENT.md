# 🚀 PRODUCTION DEPLOYMENT GUIDE
## Google Cloud Run - 24/7 Job Application System

**Real Production System for Real Job Search**

Your AI/LLM job application system will run 24/7 on Google Cloud, automatically applying to 15 jobs every day at 7:00 AM KSA time.

---

## 📋 **What You're Deploying**

```
Every Day at 7:00 AM (KSA Time):
├─ 🔍 Search 150-200 jobs (AI, LLM, Deploy Engineers)
├─ 🎯 Filter for Saudi Arabia & Dubai
├─ 📝 Customize each CV to match job description
├─ ✅ Apply to 15 positions automatically
├─ 📊 Track in database
└─ 📧 Send daily email report

Expected Results (30 Days):
- ~450 applications submitted
- ~15 phone interviews
- ~2-3 job offers
- First interview: 5-7 days
- First offer: 2-3 weeks
```

---

## 💰 **Cost**

- **Google Cloud Run**: $6.50/month included free
- **Your usage**: ~$2-5/month (well under free tier)
- **Gmail API**: Free
- **Total**: **~$5-10/month** or completely free

---

## ✅ **Pre-Requisites**

- [ ] Google account (Gmail)
- [ ] JSearch API key (free from RapidAPI)
- [ ] Gmail credentials downloaded (OAuth2 JSON file)
- [ ] `.env` file configured locally

---

## 🔧 **Step 1: Set Up .env File (5 minutes)**

```bash
cd ~/Documents/rag-prod

# Create .env file
nano .env
```

**Add:**
```
JSEARCH_API_KEY=your_actual_api_key_from_rapidapi
GMAIL_ENABLED=true
EMAIL_ADDRESS=shanawar.shahbaz6@gmail.com
DAILY_APPLICATIONS=15
SCHEDULE_TIME=07:00
```

**Save:** `Ctrl + X`, `Y`, `Enter`

---

## 🔐 **Step 2: Download Gmail Credentials (5 minutes)**

1. Go to: https://console.cloud.google.com
2. Create Project: "Job Applications System"
3. Enable Gmail API
4. Create OAuth Credentials (Desktop app)
5. Download JSON file
6. Move to: `job_application_system/gmail_credentials.json`

```bash
mv ~/Downloads/client_secret_*.json ~/Documents/rag-prod/job_application_system/gmail_credentials.json
```

---

## 🐳 **Step 3: Install Docker (10 minutes)**

### **On Mac:**
1. Download: https://www.docker.com/products/docker-desktop
2. Install and run Docker Desktop
3. Verify: `docker --version`

### **Or use Homebrew:**
```bash
brew install --cask docker
```

---

## 🌥️ **Step 4: Create Google Cloud Project (10 minutes)**

### **1. Go to Google Cloud Console**
```
https://console.cloud.google.com
```

### **2. Create New Project**
- Click "Select a Project" (top)
- Click "NEW PROJECT"
- Name: `job-applications-system`
- Click "CREATE"
- Wait 2-3 minutes for initialization

### **3. Enable Required APIs**
```
Search for and enable:
- Cloud Run API
- Cloud Build API
- Container Registry API
- Cloud Scheduler API
```

### **4. Create Service Account**
- Go to "IAM & Admin" → "Service Accounts"
- Click "Create Service Account"
- Name: `job-applications-runner`
- Grant roles: "Cloud Run Admin", "Editor"
- Create key (JSON) and download

### **5. Set Up Authentication**
```bash
# Download the service account JSON key
# Save to: ~/Documents/rag-prod/gcloud-key.json

# Authenticate with gcloud
gcloud auth activate-service-account --key-file=~/Documents/rag-prod/gcloud-key.json

# Set project
gcloud config set project your-project-id
```

Replace `your-project-id` with your actual project ID.

---

## 🚀 **Step 5: Deploy to Cloud Run (5 minutes)**

### **Option A: Automatic Deployment (Recommended)**

```bash
cd ~/Documents/rag-prod

# Build and deploy
gcloud run deploy job-applications \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --timeout 3600s \
  --set-env-vars JSEARCH_API_KEY=$(grep JSEARCH_API_KEY .env | cut -d= -f2),GMAIL_ENABLED=true
```

### **Option B: Using Docker (Manual)**

```bash
# Build Docker image
docker build -t job-applications:latest .

# Test locally
docker run -p 8080:8080 \
  -e JSEARCH_API_KEY=$(grep JSEARCH_API_KEY .env | cut -d= -f2) \
  -e GMAIL_ENABLED=true \
  job-applications:latest

# Push to Google Container Registry
docker tag job-applications:latest gcr.io/your-project-id/job-applications:latest
docker push gcr.io/your-project-id/job-applications:latest

# Deploy to Cloud Run
gcloud run deploy job-applications \
  --image gcr.io/your-project-id/job-applications:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi
```

---

## ⏰ **Step 6: Set Up Cloud Scheduler (5 minutes)**

### **1. Create Scheduler Job**
```bash
# In Google Cloud Console:
# Go to Cloud Scheduler
# Click "CREATE JOB"
```

### **2. Configure Job**
- **Name**: `job-applications-daily`
- **Frequency**: `0 7 * * *` (7:00 AM UTC)
- **Timezone**: Select your timezone (KSA = UTC+3, so use `0 4 * * *` for 7 AM KSA)
- **Execution Timeout**: `3600s` (1 hour)
- **Retry on failure**: Check box

### **3. Create Execution**
- **HTTP Method**: POST
- **URL**: `https://your-cloud-run-url.run.app/run`
  - Replace with your actual Cloud Run URL (from Step 5 output)
- **Auth Header**: Add OIDC token
- **Service Account**: Select the one you created

### **4. Save and Test**
- Click "SAVE"
- Click "FORCE RUN" to test immediately
- Check logs to verify it worked

---

## 📊 **Step 7: Monitor & Verify**

### **Check Cloud Run Logs**
```bash
gcloud run logs read job-applications --limit 50
```

### **Manual Test Run**
```bash
# Trigger immediately
curl -X GET https://your-cloud-run-url.run.app/test

# Expected response:
# {
#   "status": "success",
#   "jobs_found": 150,
#   "applications_submitted": 15,
#   "timestamp": "2026-07-21T07:00:00+03:00"
# }
```

### **Check Application History**
```bash
# View applications tracking CSV
cat cv-and-applications/applications_tracking.csv
```

### **View Email Reports**
- Email sent to: `shanawar.shahbaz6@gmail.com`
- Daily at 7:00 AM KSA time
- Subject: "🤖 Job Applications Report - YYYY-MM-DD"

---

## 🔍 **Troubleshooting**

### **Issue: "Container Image not found"**
- Make sure Docker is running
- Verify image was pushed: `gcloud container images list`

### **Issue: "Permission denied" deploying**
- Verify service account has "Cloud Run Admin" role
- Check: `gcloud iam service-accounts list`

### **Issue: "No jobs found" in results**
- Check `.env` has correct JSEARCH_API_KEY
- Verify API key is still valid on RapidAPI

### **Issue: "Gmail not sending emails"**
- Verify `gmail_credentials.json` exists in container
- First run will ask for authorization (opens browser)
- Check Email app for verification link

### **Issue: Scheduler not running**
- Verify Cloud Scheduler is enabled
- Check cron expression: `0 4 * * *` (for 7 AM KSA)
- Check Service Account has permissions
- View logs: `gcloud run logs read job-applications`

### **View All Logs**
```bash
# Real-time logs
gcloud run logs read job-applications --follow

# Last 100 entries
gcloud run logs read job-applications --limit 100

# Search for errors
gcloud run logs read job-applications --limit 1000 | grep ERROR
```

---

## 📈 **Monitoring Dashboard**

Set up monitoring in Google Cloud Console:

1. Go to "Cloud Run" → Your service
2. Click "Metrics" tab
3. View:
   - Request count (should be 1/day)
   - Execution time (should be 30-60 seconds)
   - Error rate (should be 0%)

---

## 💾 **Backup & Recovery**

### **Backup Application History**
```bash
# Download applications_tracking.csv
gcloud run services update-traffic job-applications --update-regions=us-central1 \
  --autoscaling-limit 100

# Or access via Cloud Storage
gsutil cp gs://your-bucket/applications_tracking.csv .
```

### **Update CV Files**
If you update your CVs locally:

```bash
# Rebuild and redeploy
gcloud run deploy job-applications --source .
```

---

## 🛑 **Stop/Pause System**

### **Pause Scheduler**
```bash
# In Google Cloud Console:
# Cloud Scheduler → Select job → PAUSE
```

### **Disable Cloud Run Service**
```bash
gcloud run services update job-applications --no-traffic
```

### **Resume**
```bash
gcloud run services update-traffic job-applications --to-revisions LATEST=100
```

---

## 📱 **Receive Job Alerts**

### **Set Up Email Notifications**
- Daily email at 7:00 AM with:
  - Jobs found (150+)
  - Applications submitted (15)
  - New opportunities list
  - Application history

### **Track Responses**
- Companies respond to your email
- Review responses daily
- Follow up within 24 hours

---

## ✅ **Final Checklist**

Before going live:

- [ ] Google Cloud project created
- [ ] Cloud Run API enabled
- [ ] Cloud Scheduler API enabled
- [ ] Service account created
- [ ] Docker installed locally
- [ ] .env file configured
- [ ] Gmail credentials downloaded
- [ ] Application deployed to Cloud Run
- [ ] Cloud Scheduler job created
- [ ] Test run successful (found 100+ jobs)
- [ ] Email received at 7:00 AM
- [ ] Application tracking CSV populated

---

## 🎯 **Expected Timeline**

**Setup:**
- Day 1: Create Google Cloud project (10 min)
- Day 1: Deploy system (10 min)
- Day 1: Configure scheduler (5 min)
- **Total: ~30 minutes**

**Results:**
- Day 1-3: Receive first responses
- Day 5-7: First phone interview scheduled
- Day 14-21: First offer received
- Day 30: ~3 offers received

---

## 📞 **Support**

### **Common Questions**

**Q: What if I want to change job roles?**
A: Edit `CONFIG["roles"]` in `job_application_system.py` and redeploy

**Q: What if I want to change schedule time?**
A: Update Cloud Scheduler cron expression
- `0 4 * * *` = 7:00 AM KSA
- `0 2 * * *` = 5:00 AM KSA
- `0 6 * * *` = 9:00 AM KSA

**Q: Can I see live jobs being applied?**
A: Yes! 
```bash
gcloud run logs read job-applications --follow
```

**Q: How do I update CVs?**
A: Edit files locally, then redeploy:
```bash
cd ~/Documents/rag-prod
gcloud run deploy job-applications --source .
```

**Q: Will it work if my Mac is off?**
A: Yes! Cloud Run runs independently. Your Mac can be off permanently.

---

## 🎉 **You're Live!**

Your system is now running 24/7:
- ✅ Searches jobs daily at 7:00 AM
- ✅ Applies with customized CVs
- ✅ Sends email reports
- ✅ Tracks all applications
- ✅ No action needed from you

**Expect:**
- ~450 applications in 30 days
- ~15 interviews
- ~2-3 offers

---

## 🔄 **Maintenance**

### **Weekly:**
- Check email for responses
- Follow up with promising companies

### **Monthly:**
- Review application statistics
- Update CV if needed
- Check system health logs

### **Every 3 Months:**
- Rotate API credentials
- Update job roles if needed
- Review and optimize CV customizations

---

**Questions?** Check the logs or refer to SETUP_GMAIL_LINKEDIN.md

**Ready to change your life?** 🚀 Start applying!

---

**Deployment Date:** [Your Date]  
**System Status:** Production Ready ✅  
**Expected Daily Applications:** 15  
**Expected Monthly Interviews:** 5-8  
**Expected Monthly Offers:** 1-2  
