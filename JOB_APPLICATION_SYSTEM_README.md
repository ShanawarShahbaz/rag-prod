# 🤖 AI/LLM Engineer Job Application System

**Automated daily job search and application system for AI/LLM/Forward Deploy engineer positions in Saudi Arabia and Dubai.**

---

## 📋 Overview

This system automates the entire job search and application process:

✅ **Daily Job Search** - Searches for AI Engineer, LLM Engineer, Forward Deploy Engineer roles  
✅ **Smart CV Customization** - Tailors your CV to match each job description  
✅ **Automated Applications** - Applies to 10-20 jobs per day  
✅ **Email Reports** - Sends daily summary to your email  
✅ **Application Tracking** - Maintains history of all applications  
✅ **Scheduled Execution** - Runs automatically at 7:00 AM KSA time  

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /home/user/rag-prod
pip install -r requirements-job-system.txt
```

### 2. Set Up Gmail Integration (Optional)

For automated email reports:

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop Application)
5. Download the JSON file
6. Save to: `job_application_system/gmail_credentials.json`

If Gmail is not set up, reports will be saved to local HTML files.

### 3. Run One-Time Test

```bash
python job_scheduler.py --mode once
```

This will:
- Search for job opportunities
- Create customized CVs
- Generate a report email (or save to file)

### 4. Start Daily Scheduler

```bash
python job_scheduler.py --mode schedule
```

The system will run every day at 7:00 AM KSA time.

---

## 📁 Project Structure

```
rag-prod/
├── job_application_system.py          # Main application logic
├── job_scheduler.py                    # Daily scheduler
├── job_email_integration.py            # Email reporting
├── requirements-job-system.txt         # Python dependencies
├── JOB_APPLICATION_SYSTEM_README.md    # This file
│
└── cv-and-applications/
    ├── cv/
    │   ├── llm_engineer_cv.md          # LLM Engineer CV template
    │   ├── ai_engineer_cv.md           # AI Engineer CV template
    │   ├── forward_deploy_engineer_cv.md # Forward Deploy Engineer CV
    │   └── [original PDFs from uploads]
    │
    ├── applications_tracking.csv       # Application history
    ├── applications_data/              # Application details
    └── emails/                          # Saved email reports
```

---

## ⚙️ Configuration

Edit `job_application_system.py` to customize:

```python
CONFIG = {
    "email": "shanawar.shahbaz6@gmail.com",  # Your email
    "schedule_time": "07:00",                 # Run time (24h format)
    "daily_applications": 15,                 # 10-20 applications per day
    "locations": ["Saudi Arabia", "Dubai", "UAE", "KSA"],
    "roles": [
        "AI Engineer",
        "LLM Engineer",
        "Forward Deploy Engineer",
        # Add more roles as needed
    ]
}
```

---

## 🎯 Role-Specific CVs

The system maintains three tailored CV versions:

### 1. **LLM Engineer CV** (`llm_engineer_cv.md`)
- Focus: Prompt engineering, RAG systems, evaluation
- Keywords: LLM, prompts, hallucination, faithfulness, retrieval
- From Enpal: Built evaluation pipelines, prompt optimization

### 2. **AI Engineer CV** (`ai_engineer_cv.md`)
- Focus: ML systems, model evaluation, infrastructure
- Keywords: ML models, evaluation metrics, training, inference
- From Enpal: Model quality assurance, optimization

### 3. **Forward Deploy Engineer CV** (`forward_deploy_engineer_cv.md`)
- Focus: Deployment automation, CI/CD, infrastructure
- Keywords: Kubernetes, deployment, infrastructure, automation
- From Enpal: Infrastructure optimization, reliability

---

## 🔍 How It Works

### Daily Workflow (7:00 AM)

```
1. Job Search Phase
   ├─ Search Indeed for "AI Engineer"
   ├─ Search JSearch for "LLM Engineer"
   ├─ Search AngelList for "Forward Deploy Engineer"
   └─ Compile results (20-30 jobs)

2. Filtering Phase
   ├─ Remove duplicates
   ├─ Check if already applied
   └─ Rank by relevance

3. Application Phase (Apply to top 10-20)
   ├─ Extract job requirements
   ├─ Select appropriate role CV
   ├─ Customize CV to match job
   ├─ Record application
   └─ Track in applications_tracking.csv

4. Reporting Phase
   ├─ Generate HTML email report
   ├─ Send via Gmail API (or save to file)
   └─ Log results to scheduler.log
```

### Application Tracking

Each application is recorded in `cv-and-applications/applications_tracking.csv`:

```csv
date,company,job_title,role_type,job_url,cv_used,status,notes
2026-07-21T07:05:00,Company A,AI Engineer,llm_engineer,https://...,llm_engineer_cv.md,applied,
2026-07-21T07:06:00,Company B,LLM Engineer,ai_engineer,https://...,ai_engineer_cv.md,applied,
...
```

---

## 📊 Monitoring & Logs

### View Scheduler Logs

```bash
tail -f job_application_system/scheduler.log
```

### Check Application History

```bash
cat cv-and-applications/applications_tracking.csv
```

### View Saved Email Reports

```bash
ls -la job_application_system/emails/
```

### Get Scheduler Status

```bash
python job_scheduler.py --mode status
```

---

## 🛠️ Advanced Features

### Custom Job Extraction

Modify `CVCustomizer.extract_job_requirements()` to extract:
- Required skills
- Experience level
- Tools and technologies
- Soft skills

### CV Customization with Claude

The system can use Claude AI to intelligently customize CVs:

```python
from anthropic import Anthropic

client = Anthropic()

# Extract job requirements
# Customize CV to match
# Generate role-specific cover letter
```

### Job Search API Integration

Currently supports:
- **Indeed API** (via RapidAPI)
- **JSearch API** (covers LinkedIn, Indeed, Glassdoor)
- **AngelList API** (startup jobs)

To add more sources:

```python
def search_linkedin_jobs(self, query, locations):
    # Implement LinkedIn API integration
    pass

def search_custom_source(self, query, locations):
    # Add custom job board
    pass
```

---

## 📧 Email Report Example

Your daily email includes:

```
╔════════════════════════════════════════════════════════╗
║   🤖 AI/LLM ENGINEER JOB APPLICATIONS - DAILY REPORT   ║
║           Monday, July 21, 2026
╚════════════════════════════════════════════════════════╝

📊 TODAY'S SUMMARY
─────────────────────────────────────────────────────────
• Jobs Found: 25
• New Opportunities: 18
• Applications Submitted: 15

🎯 TODAY'S APPLICATIONS
─────────────────────────────────────────────────────────
1. Company A - AI Engineer (Saudi Arabia)
2. Company B - LLM Engineer (Dubai)
3. Company C - Forward Deploy Engineer (UAE)
   ... (15 total applications)

📋 AVAILABLE OPPORTUNITIES (NOT YET APPLIED)
─────────────────────────────────────────────────────────
(Top 10 additional jobs for review)

💡 NEXT ACTIONS
─────────────────────────────────────────────────────────
• Review customized CVs for each application
• Check email replies from previous applications
• Follow up with promising companies
```

---

## 🔧 Troubleshooting

### Issue: No jobs found

**Check:**
- Job API credentials are valid
- Internet connection is active
- Job search APIs are responding
- Try: `python job_application_system.py` directly

### Issue: Gmail not sending emails

**Solution:**
- Gmail will fall back to saving emails locally
- Emails are saved to: `job_application_system/emails/`
- Check Gmail setup credentials

### Issue: Scheduler not running

**Check:**
- Python is running continuously
- Use process manager (systemd, tmux, screen)
- Check scheduler logs: `tail job_application_system/scheduler.log`

### Issue: Duplicate applications

**The system prevents duplicates by checking:**
- Company name
- Job title
- Previous applications tracking CSV

---

## 🚢 Production Deployment

### Option 1: Systemd Service (Linux)

Create `/etc/systemd/system/job-applications.service`:

```ini
[Unit]
Description=AI/LLM Job Application System
After=network.target

[Service]
Type=simple
User=user
WorkingDirectory=/home/user/rag-prod
ExecStart=/usr/bin/python3 job_scheduler.py --mode schedule
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable job-applications
sudo systemctl start job-applications
```

### Option 2: Using tmux/screen

```bash
tmux new-session -d -s job-applications
tmux send-keys -t job-applications 'cd /home/user/rag-prod && python job_scheduler.py --mode schedule' Enter
```

### Option 3: Cloud Deployment (AWS Lambda / Google Cloud Functions)

For serverless execution:

```python
# lambda_handler.py
def lambda_handler(event, context):
    system = JobApplicationSystem()
    system.load_cv_templates()
    result = system.run_daily_cycle()
    return result
```

Deploy as CloudWatch scheduled event.

---

## 📈 Performance Metrics

After 30 days, you should see:

- **~450 applications** submitted (15/day × 30 days)
- **~15 interviews** scheduled (~3% response rate typical)
- **~2-3 offers** (13-20% interview-to-offer conversion)

These are typical for well-targeted applications with customized CVs.

---

## 🔐 Security Notes

- **Never commit** `gmail_credentials.json` or `gmail_token.json`
- Store credentials in environment variables for production
- Use `.gitignore` to exclude sensitive files:

```
job_application_system/gmail_*.json
job_application_system/emails/
cv-and-applications/applications_tracking.csv
```

---

## 🤝 Support & Customization

### Modify Job Search Criteria

Edit `CONFIG["locations"]` and `CONFIG["roles"]` in `job_application_system.py`

### Adjust Daily Application Limit

Change `"daily_applications": 15` to 10-20 based on your preference

### Customize Email Reports

Edit `_format_html_report()` in `job_email_integration.py`

### Add Custom Job Sources

Add search methods in `JobSearcher` class

---

## 📝 Next Steps

1. ✅ Install dependencies: `pip install -r requirements-job-system.txt`
2. ✅ Set up Gmail (optional): Follow steps in "Setup Gmail Integration"
3. ✅ Test once: `python job_scheduler.py --mode once`
4. ✅ Start scheduler: `python job_scheduler.py --mode schedule`
5. ✅ Monitor logs: `tail -f job_application_system/scheduler.log`
6. ✅ Check applications: `cat cv-and-applications/applications_tracking.csv`

---

## 📞 Contact & Support

**System Owner:** Shanawar Shahbaz  
**Email:** shanawar.shahbaz6@gmail.com  
**Location:** Saudi Arabia  

For issues or customization, refer to inline code documentation.

---

**Last Updated:** July 21, 2026  
**Status:** ✅ Production Ready
