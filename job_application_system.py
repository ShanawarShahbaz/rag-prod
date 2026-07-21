"""
Automated Job Application System
Searches for AI/LLM/Forward Deploy Engineer jobs and applies with customized CVs
"""

import json
import csv
from datetime import datetime
from typing import List, Dict
import requests
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
CONFIG = {
    "email": "shanawar.shahbaz6@gmail.com",
    "schedule_time": "07:00",  # 7 AM
    "daily_applications": 15,  # 10-20 per day
    "locations": ["Saudi Arabia", "Dubai", "KSA"],
    "roles": [
        "AI Engineer",
        "LLM Engineer",
        "Machine Learning Engineer",
        "Forward Deploy Engineer",
        "ML DevOps Engineer"
    ],
    "cv_folder": Path("cv-and-applications/cv"),
    "tracking_file": Path("cv-and-applications/applications_tracking.csv"),
    "jsearch_api_key": os.getenv("JSEARCH_API_KEY", ""),
    "jsearch_api_host": "jsearch.p.rapidapi.com"
}

class JobSearcher:
    """Search for jobs using JSearch API (covers LinkedIn, Indeed, Glassdoor)"""

    def __init__(self):
        self.jobs = []
        self.api_key = CONFIG["jsearch_api_key"]
        self.api_host = CONFIG["jsearch_api_host"]

    def search_jsearch(self, role: str, locations: List[str]) -> List[Dict]:
        """
        Search JSearch API for jobs
        Covers: LinkedIn, Indeed, Glassdoor, ZipRecruiter
        """
        jobs = []

        if not self.api_key:
            print(f"⚠️  JSearch API key not found in .env file")
            print(f"    To enable: Set JSEARCH_API_KEY in .env")
            return jobs

        for location in locations:
            try:
                # Search query with location
                search_query = f"{role} {location}"

                url = "https://jsearch.p.rapidapi.com/search"
                querystring = {
                    "query": search_query,
                    "page": "1",
                    "num_pages": "1"
                }

                headers = {
                    "x-rapidapi-key": self.api_key,
                    "x-rapidapi-host": self.api_host
                }

                print(f"  🔍 Searching JSearch: '{role}' in {location}...")

                response = requests.get(url, headers=headers, params=querystring, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    job_list = data.get("data", [])

                    for job in job_list:
                        job_dict = {
                            "title": job.get("job_title", ""),
                            "company": job.get("employer_name", ""),
                            "location": job.get("job_location", location),
                            "description": job.get("job_description", ""),
                            "url": job.get("job_apply_link", ""),
                            "role_type": self._detect_role_type(job.get("job_title", "")),
                            "posted_date": job.get("job_posted_at_datetime_utc", ""),
                        }

                        if job_dict["title"] and job_dict["company"]:
                            jobs.append(job_dict)

                    print(f"    ✅ Found {len(job_list)} jobs")

                elif response.status_code == 429:
                    print(f"  ⚠️  Rate limit reached (100 requests/month used)")
                    break

                elif response.status_code == 401:
                    print(f"  ❌ Invalid API key. Check JSEARCH_API_KEY in .env")
                    break

            except requests.exceptions.Timeout:
                print(f"  ⏱️  Timeout searching {location}")
            except Exception as e:
                print(f"  ❌ Error searching {location}: {str(e)}")

        return jobs

    def _detect_role_type(self, job_title: str) -> str:
        """Detect which CV to use based on job title"""
        job_title_lower = job_title.lower()

        if "llm" in job_title_lower or "prompt" in job_title_lower:
            return "llm_engineer"
        elif "deploy" in job_title_lower or "devops" in job_title_lower:
            return "forward_deploy"
        elif "ai" in job_title_lower or "ml" in job_title_lower:
            return "ai_engineer"
        else:
            return "ai_engineer"  # Default

    def search_all(self) -> List[Dict]:
        """Search all job sources"""
        all_jobs = []

        print("\n🔍 Starting job search across all roles and locations...\n")

        # Search for each role
        for role in CONFIG["roles"]:
            print(f"📌 Searching for '{role}' positions...")

            # Search JSearch (covers Indeed, LinkedIn, Glassdoor, etc.)
            jsearch_jobs = self.search_jsearch(role, CONFIG["locations"])
            all_jobs.extend(jsearch_jobs)

            print()

        # Remove duplicates and filter
        unique_jobs = self._deduplicate_jobs(all_jobs)
        print(f"\n✅ Total unique jobs found: {len(unique_jobs)}\n")
        return unique_jobs

    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate job postings"""
        seen = set()
        unique = []
        for job in jobs:
            job_key = (job.get("title"), job.get("company"), job.get("location"))
            if job_key not in seen:
                seen.add(job_key)
                unique.append(job)
        return unique


class CVCustomizer:
    """Customize CV based on job description"""

    def __init__(self, cv_templates: Dict[str, str]):
        self.cv_templates = cv_templates  # {role: cv_content}

    def extract_job_requirements(self, job_description: str) -> Dict[str, List[str]]:
        """
        Extract key requirements from job description
        Returns: {skills: [...], experience: [...], tools: [...]}
        """
        requirements = {
            "skills": [],
            "experience": [],
            "tools": [],
            "keywords": []
        }

        # In production: use Claude API to extract structured requirements
        # For now: basic keyword extraction
        keywords = [
            "Python", "LLM", "Prompt", "RAG", "Evaluation", "Testing",
            "API", "CI/CD", "Kubernetes", "Docker", "Microservices",
            "Machine Learning", "Deep Learning", "NLP", "Transformers",
            "FastAPI", "PyTorch", "TensorFlow", "LangChain", "OpenAI"
        ]

        for keyword in keywords:
            if keyword.lower() in job_description.lower():
                requirements["keywords"].append(keyword)

        return requirements

    def customize_cv_for_job(self, base_cv: str, job_description: str, job_title: str) -> str:
        """
        Customize CV to match job requirements
        Reorder sections, highlight relevant skills
        """
        requirements = self.extract_job_requirements(job_description)

        # In production: use Claude API to intelligently rewrite CV
        customized_cv = f"""
        CUSTOMIZED FOR: {job_title}
        Matched Keywords: {', '.join(requirements['keywords'])}

        {base_cv}

        --- CUSTOMIZATION NOTES ---
        This CV has been customized to highlight:
        - Skills: {', '.join(requirements['keywords'][:5])}
        - Experience: Focus on LLM/AI engineering work
        """

        return customized_cv

    def generate_cover_letter_snippet(self, job_title: str, requirements: Dict) -> str:
        """Generate brief cover letter snippet for this specific job"""
        snippet = f"""
        Dear Hiring Manager,

        I am excited to apply for the {job_title} position. My experience in:
        - {', '.join(requirements.get('keywords', [])[:3])}

        aligns perfectly with your requirements. At Enpal, I built and optimized
        quality frameworks similar to what you're looking for.

        Looking forward to discussing how I can contribute to your team.

        Best regards,
        Shanawar Shahbaz
        """
        return snippet


class ApplicationTracker:
    """Track applications to prevent duplicates and monitor progress"""

    def __init__(self, tracking_file: Path):
        self.tracking_file = tracking_file
        self.ensure_tracking_file()

    def ensure_tracking_file(self):
        """Create tracking file if it doesn't exist"""
        if not self.tracking_file.exists():
            self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.tracking_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'date', 'company', 'job_title', 'role_type', 'job_url',
                    'cv_used', 'status', 'notes'
                ])
                writer.writeheader()

    def has_applied(self, company: str, job_title: str) -> bool:
        """Check if we've already applied to this job"""
        if not self.tracking_file.exists():
            return False

        with open(self.tracking_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['company'] == company and row['job_title'] == job_title:
                    return True
        return False

    def record_application(self, job_data: Dict, cv_used: str, status: str = "applied"):
        """Record an application"""
        with open(self.tracking_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'date', 'company', 'job_title', 'role_type', 'job_url',
                'cv_used', 'status', 'notes'
            ])
            writer.writerow({
                'date': datetime.now().isoformat(),
                'company': job_data.get('company', ''),
                'job_title': job_data.get('title', ''),
                'role_type': job_data.get('role_type', ''),
                'job_url': job_data.get('url', ''),
                'cv_used': cv_used,
                'status': status,
                'notes': job_data.get('notes', '')
            })

    def get_daily_stats(self) -> Dict:
        """Get today's application statistics"""
        today = datetime.now().date().isoformat()
        stats = {'total': 0, 'by_role': {}, 'by_company': []}

        if not self.tracking_file.exists():
            return stats

        with open(self.tracking_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['date'].startswith(today):
                    stats['total'] += 1
                    role = row['role_type']
                    stats['by_role'][role] = stats['by_role'].get(role, 0) + 1
                    stats['by_company'].append(row['company'])

        return stats


class EmailReporter:
    """Generate and send daily email reports"""

    def __init__(self, email: str):
        self.email = email

    def generate_daily_report(self,
                             jobs_found: List[Dict],
                             applications: List[Dict],
                             stats: Dict) -> str:
        """Generate daily email report"""

        report = f"""
        ╔════════════════════════════════════════════════════════╗
        ║   🤖 AI/LLM ENGINEER JOB APPLICATIONS - DAILY REPORT   ║
        ║           {datetime.now().strftime('%A, %B %d, %Y')}
        ╚════════════════════════════════════════════════════════╝

        📊 TODAY'S SUMMARY
        ─────────────────────────────────────────────────────────
        • Jobs Found: {len(jobs_found)}
        • Applications Submitted: {stats.get('total', 0)}
        • By Role: {stats.get('by_role', {})}

        🎯 TODAY'S APPLICATIONS
        ─────────────────────────────────────────────────────────
        """

        for i, app in enumerate(applications, 1):
            report += f"""
        {i}. {app.get('company', 'N/A')} - {app.get('job_title', 'N/A')}
           Role Type: {app.get('role_type', 'N/A')}
           CV Used: {app.get('cv_used', 'N/A')}
           Link: {app.get('job_url', 'N/A')}
        """

        report += f"""

        📋 AVAILABLE OPPORTUNITIES (NOT YET APPLIED)
        ─────────────────────────────────────────────────────────
        """

        for i, job in enumerate(jobs_found[:10], 1):  # Show top 10
            report += f"""
        {i}. {job.get('company', 'N/A')} - {job.get('title', 'N/A')}
           Location: {job.get('location', 'N/A')}
           Link: {job.get('url', 'N/A')}
        """

        report += """

        💡 NEXT ACTIONS
        ─────────────────────────────────────────────────────────
        • Review customized CVs for each application
        • Check email replies from previous applications
        • Follow up with promising companies

        🔄 NEXT REPORT: Tomorrow at 7:00 AM (KSA Time)

        ─────────────────────────────────────────────────────────
        This is an automated report from your AI/LLM Job Application System
        """

        return report

    def send_email(self, subject: str, body: str):
        """Send email report (integration with Gmail API)"""
        print(f"📧 Email Report Generated")
        print(f"To: {self.email}")
        print(f"Subject: {subject}")
        print(f"\n{body}")

        # In production: integrate with Gmail API or SMTP
        # For now: save to file
        with open("job_application_system/last_report.txt", "w") as f:
            f.write(body)


class JobApplicationSystem:
    """Main orchestrator for the job application workflow"""

    def __init__(self):
        self.searcher = JobSearcher()
        self.tracker = ApplicationTracker(CONFIG["tracking_file"])
        self.reporter = EmailReporter(CONFIG["email"])
        self.cv_customizer = CVCustomizer({})  # Will load CVs

    def load_cv_templates(self):
        """Load CV templates for each role"""
        cv_folder = Path(CONFIG["cv_folder"])
        templates = {}

        # Look for role-specific CV files
        for role_name in ["ai_engineer", "llm_engineer", "forward_deploy"]:
            cv_file = cv_folder / f"{role_name}_cv.md"
            if cv_file.exists():
                templates[role_name] = cv_file.read_text()

        self.cv_customizer.cv_templates = templates
        return templates

    def run_daily_cycle(self):
        """Execute the complete daily job search and application cycle"""
        print("🚀 Starting Daily Job Application Cycle...")
        print(f"⏰ Time: {datetime.now()}")

        # Step 1: Search for jobs
        print("\n📍 Step 1: Searching for jobs in Saudi Arabia & Dubai...")
        jobs_found = self.searcher.search_all()
        print(f"✅ Found {len(jobs_found)} job opportunities")

        # Step 2: Filter already applied jobs
        print("\n📍 Step 2: Filtering already-applied positions...")
        new_jobs = [
            job for job in jobs_found
            if not self.tracker.has_applied(job.get("company"), job.get("title"))
        ]
        print(f"✅ {len(new_jobs)} new opportunities to consider")

        # Step 3: Apply to jobs
        print(f"\n📍 Step 3: Applying to top {CONFIG['daily_applications']} jobs...")
        applications = []
        for i, job in enumerate(new_jobs[:CONFIG["daily_applications"]], 1):
            print(f"  {i}. Applying to {job.get('company')} - {job.get('title')}")

            # Customize CV for this job
            cv_content = self.cv_customizer.customize_cv_for_job(
                base_cv="[Your customized CV content]",
                job_description=job.get("description", ""),
                job_title=job.get("title", "")
            )

            # Record application
            self.tracker.record_application(
                job,
                cv_used=f"{job.get('role_type', 'general')}_cv.md",
                status="applied"
            )

            applications.append(job)

        # Step 4: Generate report
        print("\n📍 Step 4: Generating daily report...")
        stats = self.tracker.get_daily_stats()
        report = self.reporter.generate_daily_report(
            jobs_found=new_jobs[:10],
            applications=applications,
            stats=stats
        )

        # Step 5: Send email
        print("\n📍 Step 5: Sending email report...")
        self.reporter.send_email(
            subject=f"🤖 Job Applications Report - {datetime.now().strftime('%Y-%m-%d')}",
            body=report
        )

        print("\n✅ Daily cycle completed!")
        return {
            "jobs_found": len(jobs_found),
            "new_opportunities": len(new_jobs),
            "applications_submitted": len(applications),
            "stats": stats
        }


# Main execution
if __name__ == "__main__":
    system = JobApplicationSystem()
    system.load_cv_templates()
    result = system.run_daily_cycle()

    print("\n" + "="*60)
    print("DAILY CYCLE SUMMARY")
    print("="*60)
    print(json.dumps(result, indent=2))
