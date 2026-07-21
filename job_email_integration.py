"""
Email Integration for Job Application System
Sends daily reports via Gmail API
"""

import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import logging

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google.auth.oauthlib.flow import InstalledAppFlow
    from google.api_client import build
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False

logger = logging.getLogger(__name__)

# Gmail API Scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
CREDENTIALS_FILE = 'job_application_system/gmail_credentials.json'
TOKEN_FILE = 'job_application_system/gmail_token.json'


class EmailClient:
    """Gmail email client for sending reports"""

    def __init__(self):
        self.service = None
        self.initialized = False

        if GMAIL_API_AVAILABLE:
            self._initialize_gmail()
        else:
            logger.warning("Gmail API not available. Install: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")

    def _initialize_gmail(self):
        """Initialize Gmail API service"""
        try:
            # Check if token exists
            if Path(TOKEN_FILE).exists():
                self.service = self._build_service_from_token()
                self.initialized = True
                logger.info("✅ Gmail API initialized (existing token)")
                return

            # Check if credentials file exists
            if not Path(CREDENTIALS_FILE).exists():
                logger.warning(f"Gmail credentials not found at {CREDENTIALS_FILE}")
                logger.info("To set up Gmail:")
                logger.info("1. Go to: https://console.cloud.google.com")
                logger.info("2. Create OAuth 2.0 credentials (Desktop app)")
                logger.info("3. Download JSON and save as: job_application_system/gmail_credentials.json")
                return

            # Create new token from credentials
            self.service = self._build_service_from_credentials()
            self.initialized = True
            logger.info("✅ Gmail API initialized (new token created)")

        except Exception as e:
            logger.error(f"Failed to initialize Gmail API: {e}")

    def _build_service_from_token(self):
        """Build Gmail service from existing token"""
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        # Refresh token if expired
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed credentials
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

        return build('gmail', 'v1', credentials=creds)

    def _build_service_from_credentials(self):
        """Build Gmail service from credentials file"""
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)

        # Save token for reuse
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

        return build('gmail', 'v1', credentials=creds)

    def send_email(self, to: str, subject: str, body: str, is_html: bool = True):
        """Send email via Gmail API"""
        if not self.initialized:
            logger.warning("Gmail not initialized. Saving email to file instead.")
            return self._save_email_to_file(to, subject, body)

        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['subject'] = subject

            # Add HTML content
            if is_html:
                msg_body = MIMEText(body, 'html')
            else:
                msg_body = MIMEText(body, 'plain')

            message.attach(msg_body)

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Send via Gmail API
            send_message = {'raw': raw_message}
            self.service.users().messages().send(userId='me', body=send_message).execute()

            logger.info(f"✅ Email sent successfully to {to}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            # Fallback: save to file
            return self._save_email_to_file(to, subject, body)

    def _save_email_to_file(self, to: str, subject: str, body: str):
        """Save email to file (fallback when Gmail not available)"""
        try:
            email_dir = Path('job_application_system/emails')
            email_dir.mkdir(parents=True, exist_ok=True)

            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = email_dir / f"email_{timestamp}.html"

            email_content = f"""
            <html>
            <head><title>Email Report</title></head>
            <body>
            <p><strong>To:</strong> {to}</p>
            <p><strong>Subject:</strong> {subject}</p>
            <p><strong>Date:</strong> {datetime.now().isoformat()}</p>
            <hr>
            {body}
            </body>
            </html>
            """

            with open(filename, 'w') as f:
                f.write(email_content)

            logger.info(f"📧 Email saved to file: {filename}")
            print(f"\n📧 Email Report (saved to: {filename}):")
            print("=" * 70)
            print(body)
            print("=" * 70)

            return True

        except Exception as e:
            logger.error(f"Failed to save email to file: {e}")
            return False


class EmailReporter:
    """Generate and send formatted email reports"""

    def __init__(self, email_client: EmailClient):
        self.client = email_client

    def send_daily_report(self, to: str, jobs_summary: dict):
        """Send formatted daily report"""
        subject = f"🤖 AI/LLM Job Applications Report - {jobs_summary.get('date', 'Today')}"

        body = self._format_html_report(jobs_summary)

        return self.client.send_email(to, subject, body, is_html=True)

    def _format_html_report(self, jobs_summary: dict) -> str:
        """Format report as HTML email"""
        jobs_found = jobs_summary.get('jobs_found', 0)
        applications_submitted = jobs_summary.get('applications_submitted', 0)
        new_opportunities = jobs_summary.get('new_opportunities', 0)
        date = jobs_summary.get('date', 'Today')

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .header {{ background: #667eea; color: white; padding: 20px; text-align: center; }}
                .summary {{ background: #f0f4ff; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .stat {{ display: inline-block; margin: 10px 20px; }}
                .stat-number {{ font-size: 24px; font-weight: bold; color: #667eea; }}
                .stat-label {{ font-size: 12px; color: #666; }}
                .section {{ margin: 20px 0; }}
                .section-title {{ font-size: 16px; font-weight: bold; color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 5px; }}
                .job-item {{ background: #f9f9f9; padding: 10px; margin: 10px 0; border-left: 3px solid #667eea; }}
                .job-title {{ font-weight: bold; }}
                .job-company {{ color: #666; }}
                .footer {{ color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🤖 AI/LLM Engineer Job Applications</h2>
                <p>Daily Report - {date}</p>
            </div>

            <div class="summary">
                <div class="stat">
                    <div class="stat-number">{jobs_found}</div>
                    <div class="stat-label">Jobs Found</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{new_opportunities}</div>
                    <div class="stat-label">New Opportunities</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{applications_submitted}</div>
                    <div class="stat-label">Applications Submitted</div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">📋 Today's Applications</div>
                <p>
                    {applications_submitted} applications have been submitted today with
                    customized CVs for each position.
                </p>
                <p>Check your email for updates on responses and next steps.</p>
            </div>

            <div class="section">
                <div class="section-title">🎯 Coming Up</div>
                <ul>
                    <li>Tomorrow at 7:00 AM: Next batch of job searches and applications</li>
                    <li>Follow up on pending applications</li>
                    <li>Review any email responses from companies</li>
                </ul>
            </div>

            <div class="footer">
                <p>This is an automated report from your AI/LLM Job Application System</p>
                <p>Next report: Tomorrow at 7:00 AM (KSA Time)</p>
            </div>
        </body>
        </html>
        """
        return html


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Initialize email client
    client = EmailClient()

    # Create reporter
    reporter = EmailReporter(client)

    # Send sample report
    sample_data = {
        'date': 'July 21, 2026',
        'jobs_found': 25,
        'new_opportunities': 18,
        'applications_submitted': 15
    }

    reporter.send_daily_report('shanawar.shahbaz6@gmail.com', sample_data)
