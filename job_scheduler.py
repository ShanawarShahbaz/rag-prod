"""
Daily Job Application Scheduler
Runs job application cycle every day at 7:00 AM (KSA Time)
"""

import schedule
import time
from datetime import datetime
import pytz
from pathlib import Path
import sys
import logging

from job_application_system import JobApplicationSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_application_system/scheduler.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
KSA_TIMEZONE = pytz.timezone('Asia/Riyadh')
SCHEDULE_TIME = "07:00"  # 7:00 AM
LOG_DIR = Path("job_application_system")
LOG_DIR.mkdir(exist_ok=True)


class JobApplicationScheduler:
    """Manage daily job application scheduling"""

    def __init__(self):
        self.system = JobApplicationSystem()
        self.system.load_cv_templates()
        self.is_running = False

    def run_daily_job_cycle(self):
        """Execute the complete daily job application cycle"""
        try:
            logger.info("=" * 70)
            logger.info("🚀 STARTING DAILY JOB APPLICATION CYCLE")
            logger.info("=" * 70)

            # Run the job application system
            result = self.system.run_daily_cycle()

            logger.info("=" * 70)
            logger.info("✅ DAILY CYCLE COMPLETED SUCCESSFULLY")
            logger.info("=" * 70)
            logger.info(f"Jobs Found: {result['jobs_found']}")
            logger.info(f"New Opportunities: {result['new_opportunities']}")
            logger.info(f"Applications Submitted: {result['applications_submitted']}")

            return result

        except Exception as e:
            logger.error(f"❌ ERROR IN DAILY CYCLE: {str(e)}", exc_info=True)
            self._send_error_notification(str(e))
            return {"status": "error", "message": str(e)}

    def _send_error_notification(self, error_msg: str):
        """Send error notification email"""
        logger.warning(f"Error notification would be sent: {error_msg}")
        # In production: send email alert to user

    def schedule_jobs(self):
        """Schedule the daily job application cycle"""
        logger.info(f"📅 Scheduling job application cycle at {SCHEDULE_TIME} KSA Time")

        # Schedule job to run daily at specified time
        schedule.every().day.at(SCHEDULE_TIME).do(self.run_daily_job_cycle)

        logger.info("✅ Job scheduled successfully")

    def start_scheduler(self):
        """Start the scheduler loop"""
        self.is_running = True
        logger.info("🎯 Scheduler started. Waiting for scheduled time...")

        try:
            while self.is_running:
                # Run pending scheduled jobs
                schedule.run_pending()

                # Log current time and next run
                now = datetime.now(KSA_TIMEZONE)
                next_run = schedule.idle_seconds()

                if next_run and next_run > 0:
                    logger.debug(f"⏰ Current time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                    logger.debug(f"⏳ Next run in: {int(next_run)} seconds")

                # Sleep for 60 seconds before checking again
                time.sleep(60)

        except KeyboardInterrupt:
            logger.info("⏸️  Scheduler paused by user")
            self.is_running = False
        except Exception as e:
            logger.error(f"❌ SCHEDULER ERROR: {str(e)}", exc_info=True)
            self.is_running = False

    def run_once_immediately(self):
        """Run the job application cycle once immediately (for testing)"""
        logger.info("🔄 Running job application cycle immediately (manual trigger)")
        return self.run_daily_job_cycle()

    def get_status(self):
        """Get current scheduler status"""
        status = {
            "is_running": self.is_running,
            "scheduled_time": SCHEDULE_TIME,
            "timezone": str(KSA_TIMEZONE),
            "current_time": datetime.now(KSA_TIMEZONE).isoformat(),
            "jobs_in_queue": len(schedule.jobs),
            "next_run": schedule.next_run().isoformat() if schedule.jobs else None
        }
        return status


def run_scheduler():
    """Main function to run the scheduler"""
    scheduler = JobApplicationScheduler()

    # Schedule the daily job
    scheduler.schedule_jobs()

    # Print status
    status = scheduler.get_status()
    logger.info(f"Scheduler Status: {status}")

    # Start the scheduler loop
    scheduler.start_scheduler()


def run_once():
    """Run the job application cycle once (for testing)"""
    scheduler = JobApplicationScheduler()
    logger.info("🔄 Running job application cycle once...")
    result = scheduler.run_once_immediately()
    logger.info(f"Result: {result}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Job Application Scheduler")
    parser.add_argument(
        "--mode",
        choices=["schedule", "once", "status"],
        default="schedule",
        help="Run mode: schedule (continuous), once (single run), or status (check status)"
    )

    args = parser.parse_args()

    if args.mode == "once":
        run_once()
    elif args.mode == "status":
        scheduler = JobApplicationScheduler()
        status = scheduler.get_status()
        logger.info(f"Scheduler Status:\n{status}")
    else:
        run_scheduler()
