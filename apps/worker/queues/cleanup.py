from celery_app import celery

@celery.task
def daily_cleanup():
    print("Running system cleanups and archiving data...")
    return True
