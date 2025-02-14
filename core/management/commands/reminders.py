from django.core.management.base import BaseCommand
from core.models import ActionableStep, Reminder
from datetime import timedelta
from django.utils.timezone import now
import time
import logging

# Configure logging
logger = logging.getLogger(__name__)

def send_reminder(step_id):
    """
    Send a reminder for an actionable step.

    Args:
        step_id (int): The ID of the actionable step.
    """
    try:
        step = ActionableStep.objects.get(id=step_id)
        if not step.completed:
            # Send the reminder (replace with email/SMS logic)
            logger.info(f"Reminder sent for {step.patient}")
            if step.step_type != 'due_date':
                print(f"""Reminder sent for {step.patient}
                    {step.step_type}: {step.actionable_step} due on {step.due_date}
                """)
                
                # get reminder if exists update else create
                reminder_content = f"{step.step_type}: {step.actionable_step} due on {step.due_date}"
                reminder, created = Reminder.objects.update_or_create(
                    step=step,
                    defaults={
                        'reminder_content': reminder_content,
                        'reminder_date': step.due_date
                    },
                    patient=step.patient 
                )
                
            # Log the reminder in the database or external system if needed
            # Example: step.reminder_sent_at = now(); step.save()

    except ActionableStep.DoesNotExist:
        logger.error(f"ActionableStep with ID {step_id} does not exist.")
        
class Command(BaseCommand):
    help = 'Send reminders for actionable steps that are due.'

    def handle(self, *args, **options):
        self.stdout.write("Starting reminder service...")

        while True:
            try:
                # Query actionable steps that are due and not completed
                steps = ActionableStep.objects.filter(
                    completed=False
                )

                if steps.exists():
                    for step in steps:
                        # Send a reminder for each actionable step
                        send_reminder(step.id)
                        
                        # If the patient misses a check-in, reschedule the reminder for the next day
                        if now() > step.due_date:
                            new_due_date = step.due_date + timedelta(days=1)
                            # Update the due_date in the database to avoid duplicate reminders
                            step.due_date = new_due_date
                            step.save()
                            send_reminder(step.id)

                else:
                    self.stdout.write("No reminders to send at this time.")

                # Sleep for 2 seconds before checking again
                time.sleep(10)

            except Exception as e:
                # Log any unexpected errors
                logger.error(f"Error in reminder service: {e}")
                time.sleep(2)  # Avoid crashing the service on error