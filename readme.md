# Project Documentation

## Authentication
I used **Token-Based Authentication** because it provides a stateless, scalable, and secure way to authenticate users. Each authenticated user receives a unique token, which they must include in their requests. This method allows:
- Secure API access.
- Easier integration.
- Reduced server load since there are no session-based authentications.

## Password Encryption
I used **PBKDF2 (Password-Based Key Derivation Function 2)**, which is Django's default password hashing algorithm. PBKDF2 is widely trusted because:
- It applies multiple iterations to slow down brute-force attacks.
- It includes a cryptographic salt to defend against rainbow table attacks.
- It is built into Django and follows best security practices.

## Note Encryption
For encrypting sensitive notes, I used **django-cryptography 5** because:
- It provides automatic encryption and decryption of model fields.
- It integrates well with Django ORM.
- It supports modern encryption standards like AES.
- It simplifies data protection without requiring complex configurations.

## Data Storage
I used **SQLite** for data storage because:
- It comes as the default database with Django.
- It requires no setup, making development and testing faster.
- It is lightweight and suitable for small to medium-scale applications.
- It ensures easy portability since the database is a single file.


## Scheduling Strategy

The system includes a background task that **automatically sends reminders** for due actionable steps. The scheduling logic is implemented as a **Django management command** and follows these key principles:

- **Periodic Execution**: The script runs every **10 seconds**, querying pending actionable steps and sending reminders.
- **Rescheduling Missed Reminders**: If a reminder is missed (i.e., the due date has passed), the system **reschedules it for the next day**.
- **Error Handling**: Any unexpected errors are **logged** to prevent the service from crashing.
- **Database Updates**: If a reminder **already exists**, it is **updated** instead of creating a duplicate entry.

## Implementation

The `Command` class continuously fetches due actionable steps and invokes the `send_reminder` function:

```python
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
    """
    try:
        step = ActionableStep.objects.get(id=step_id)
        if not step.completed:
            # Log reminder action
            logger.info(f"Reminder sent for {step.patient}")

            # Ensure the reminder content is meaningful
            reminder_content = f"{step.step_type}: {step.actionable_step} due on {step.due_date}"
            
            # Update or create a reminder
            reminder, created = Reminder.objects.update_or_create(
                step=step,
                patient=step.patient,
                defaults={'reminder_content': reminder_content, 'reminder_date': step.due_date}
            )
            
    except ActionableStep.DoesNotExist:
        logger.error(f"ActionableStep with ID {step_id} does not exist.")

class Command(BaseCommand):
    help = 'Send reminders for actionable steps that are due.'

    def handle(self, *args, **options):
        self.stdout.write("Starting reminder service...")

        while True:
            try:
                steps = ActionableStep.objects.filter(completed=False)

                if steps.exists():
                    for step in steps:
                        send_reminder(step.id)

                        if now() > step.due_date:
                            step.due_date += timedelta(days=1)
                            step.save()
                            send_reminder(step.id)

                else:
                    self.stdout.write("No reminders to send at this time.")

                time.sleep(10)

            except Exception as e:
                logger.error(f"Error in reminder service: {e}")
                time.sleep(2)
```

## Tech stack Used
Django
Django Rest Framework

## Endpoint and Output

``` POST http://127.0.0.1:8000/api/signup ```
```
{
	"response": "Successfully registered a new user.",
	"email": "daniel@gmail.com",
	"full_name": "Daniel Ansah",
	"role": "doctor",
	"token": "1acdaa01ab130297c0d5f8b64f0ee67eeca9cd58"
}
```

``` POST http://127.0.0.1:8000/api/signin```
```
{
	"token": "7f2c038b0e6828f81be098c6317be5272f349d84" # token for making other request
}
```



```GET http://127.0.0.1:8000/api/users```

```
HEADER : {
    Content-Type: "application/json"
    Token: "*******"
}
```


```
[
	{
		"email": "admin@gmail.com",
		"full_name": "admin",
		"role": "patient",
		"assigned_doctor": null
	},
	{
		"email": "derick@gmail.com",
		"full_name": "James Danso Okyere",
		"role": "patient",
		"assigned_doctor": null
	},
	{
		"email": "john@gmail.com",
		"full_name": "John Okyere",
		"role": "doctor",
		"assigned_patients": []
	}
]
```


#### Select a doctor
``` POST http://127.0.0.1:8000/api/doctors ```

```
HEADER : {
    Content-Type: "application/json"
    Token: "*******"
}
```

###### Data Input
```
{
    "doctor_id": 4
}
```

##### Data Output
```
{
	"email": "derick@gmail.com",
	"full_name": "James Danso Okyere",
	"role": "patient",
	"assigned_doctor": "John Okyere",
	"response": "Doctor assigned successfully"
}
```

### Get doctors and their patients
```GET http://127.0.0.1:8000/api/doctors```

```
HEADER : {
    Content-Type: "application/json"
    Token: "*******"
}
```

```
[
	{
		"email": "john@gmail.com",
		"full_name": "John Okyere",
		"role": "doctor",
		"assigned_patients": [
			"James Danso Okyere"
		]
	}
]
```

### Get patients and their assigned doctor with actionable steps, doctor note an reminders if any
If the user making this request has a role of doctor and has been assigned with a patient or patients, notes given to these patients would be decrypted and shown, but
if not you would be forbidden to make the request or shows "No patients found"
Although the note are encrypted and stored in the database.

```GET http://127.0.0.1:8000/api/patients```
```
HEADER : {
    Content-Type: "application/json"
    Token: "*******"
}
```

```
[
	{
		"assigned_doctor": "John Okyere",
		"user_role": "patient",
		"email": "derick@gmail.com",
		"full_name": "James Danso Okyere",
		"actionable_steps": [
			{
				"actionable_step": "1. Buy a thermometer.",
				"due_date": "2025-02-21T00:00:00Z",
				"step_type": "checklist",
				"completed": false,
				"doctor_note": "Patient should take amoxicillin daily for 7 days and buy a thermometer."
			},
			{
				"actionable_step": "1. Take amoxicillin daily for 7 days.",
				"due_date": "2025-02-21T00:00:00Z",
				"step_type": "plan",
				"completed": false,
				"doctor_note": "Patient should take amoxicillin daily for 7 days and buy a thermometer."
			},
			{
				"actionable_step": "21 Feb 2025",
				"due_date": "2025-02-21T00:00:00Z",
				"step_type": "due_date",
				"completed": false,
				"doctor_note": "Patient should take amoxicillin daily for 7 days and buy a thermometer."
			}
		]
	}
]
```

### Send Note by doctor and actionable steps produce by an LLM (Gemini)

```POST http://127.0.0.1:8000/api/patients```
```
HEADER : {
    Content-Type: "application/json"
    Token: "*******"
}
```
#### Data Input
```
{
    "patient_id": 3,
    "notes": "Patient should take amoxicillin daily for 7 days and buy a thermometer."
}
```

#### Data Output
```
[
	{
		"actionable_step": "1. Buy a thermometer.",
		"due_date": "2025-02-21T00:00:00Z",
		"step_type": "checklist",
		"completed": false,
		"doctor_note": "Patient should take amoxicillin daily for 7 days and buy a thermometer."
	},
	{
		"actionable_step": "1. Take amoxicillin daily for 7 days.",
		"due_date": "2025-02-21T00:00:00Z",
		"step_type": "plan",
		"completed": false,
		"doctor_note": "Patient should take amoxicillin daily for 7 days and buy a thermometer."
	},
	{
		"actionable_step": "21 Feb 2025",
		"due_date": "2025-02-21T00:00:00Z",
		"step_type": "due_date",
		"completed": false,
		"doctor_note": "Patient should take amoxicillin daily for 7 days and buy a thermometer."
	}
]
```
