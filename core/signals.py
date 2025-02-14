from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime
from celery import shared_task
from .models import ActionableStep
from .tasks import send_reminder

@receiver(post_save, sender=ActionableStep)
def schedule_reminders(sender, instance, **kwargs):
    """Schedule a reminder when a new actionable step is added."""
    if not instance.completed:  # Ensure it's an active task
        send_reminder.apply_async((instance.patient.id,), eta=instance.due_date)
