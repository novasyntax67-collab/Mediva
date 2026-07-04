from celery_app import celery

@celery.task
def send_email_notification(recipient: str, subject: str, body: str):
    print(f"Sending email notification to {recipient} with subject: {subject}")
    return True
