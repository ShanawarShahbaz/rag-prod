"""
Cloud Scheduler for Google Cloud Run
Runs job application system on schedule in production
"""

import os
import json
from datetime import datetime
import pytz
from flask import Flask, request
from job_application_system import JobApplicationSystem
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
KSA_TIMEZONE = pytz.timezone('Asia/Riyadh')
SCHEDULED_TIME = "07:00"  # 7:00 AM


class CloudJobApplicationSystem(JobApplicationSystem):
    """Extended system for cloud deployment"""

    def __init__(self):
        super().__init__()
        self.cloud_mode = True
        logger.info("🌥️  Cloud Job Application System Initialized")

    def run_cycle_cloud(self):
        """Run cycle optimized for Cloud Run"""
        try:
            logger.info("=" * 70)
            logger.info("🚀 CLOUD JOB APPLICATION CYCLE STARTED")
            logger.info(f"⏰ Time: {datetime.now(KSA_TIMEZONE)}")
            logger.info("=" * 70)

            # Load CVs
            self.load_cv_templates()

            # Run the job application cycle
            result = self.run_daily_cycle()

            logger.info("=" * 70)
            logger.info("✅ CLOUD CYCLE COMPLETED SUCCESSFULLY")
            logger.info("=" * 70)

            return {
                "status": "success",
                "timestamp": datetime.now(KSA_TIMEZONE).isoformat(),
                "jobs_found": result.get("jobs_found", 0),
                "applications_submitted": result.get("applications_submitted", 0),
                "new_opportunities": result.get("new_opportunities", 0)
            }

        except Exception as e:
            logger.error(f"❌ CLOUD CYCLE ERROR: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now(KSA_TIMEZONE).isoformat()
            }


# Initialize system
system = CloudJobApplicationSystem()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint (required for Cloud Run)"""
    return json.dumps({
        "status": "healthy",
        "timestamp": datetime.now(KSA_TIMEZONE).isoformat(),
        "timezone": "Asia/Riyadh"
    }), 200


@app.route('/run', methods=['POST'])
def run_job_cycle():
    """
    Cloud Scheduler calls this endpoint daily at 7:00 AM

    To set up in Google Cloud Console:
    1. Go to Cloud Scheduler
    2. Create Job
    3. Frequency: 0 7 * * * (7 AM UTC)
    4. Timezone: Asia/Riyadh
    5. URL: https://your-cloud-run-url.run.app/run
    6. Auth header: Add OIDC token
    """

    # Verify request is from Cloud Scheduler
    auth_header = request.headers.get('Authorization', '')

    logger.info(f"📍 /run endpoint called")
    logger.info(f"   Time: {datetime.now(KSA_TIMEZONE)}")

    # Run the job application cycle
    result = system.run_cycle_cloud()

    return json.dumps(result), 200 if result["status"] == "success" else 500


@app.route('/status', methods=['GET'])
def status():
    """Get current system status"""
    return json.dumps({
        "status": "running",
        "current_time_ksa": datetime.now(KSA_TIMEZONE).isoformat(),
        "scheduled_time": SCHEDULED_TIME,
        "timezone": "Asia/Riyadh",
        "cv_templates_available": bool(system.cv_customizer.cv_templates)
    }), 200


@app.route('/test', methods=['GET'])
def test_run():
    """Test run (manual trigger)"""
    logger.info("🧪 TEST RUN TRIGGERED")
    result = system.run_cycle_cloud()
    return json.dumps(result), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return json.dumps({
        "service": "AI/LLM Job Application System",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "run": "/run (POST)",
            "test": "/test (GET)"
        },
        "current_time_ksa": datetime.now(KSA_TIMEZONE).isoformat()
    }), 200


@app.errorhandler(404)
def not_found(e):
    return json.dumps({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}", exc_info=True)
    return json.dumps({"error": "Internal server error"}), 500


if __name__ == '__main__':
    # Get port from environment or default to 8080
    port = int(os.environ.get('PORT', 8080))

    logger.info(f"🌥️  Cloud Job Application System Starting")
    logger.info(f"   Port: {port}")
    logger.info(f"   Timezone: Asia/Riyadh")
    logger.info(f"   Health Check: GET /health")
    logger.info(f"   Run Job Cycle: POST /run")
    logger.info(f"   Test: GET /test")

    # Start Flask server
    app.run(host='0.0.0.0', port=port, debug=False)
