from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.utils.timezone import now
import logging
from finx.views import generate_recurring_invoices

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def start_scheduler():
    global scheduler

    if not scheduler.running:
        scheduler.add_job(
            generate_recurring_invoices,
            trigger=IntervalTrigger(minutes=1),
            id="generate_recurring_invoices",
            replace_existing=True
        )
        scheduler.start()
        logger.info(f"🔄 Invoice Scheduler Started (Runs every 1 minute) at {now()}")
    else:
        logger.info("✅ Scheduler is already running.")
