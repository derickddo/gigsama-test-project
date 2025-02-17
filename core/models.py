from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django_cryptography.fields import encrypt
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


# Create your models here.
class CustomUser(AbstractUser):
    USER_ROLES = (
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
    )
    role = models.CharField(max_length=10, choices=USER_ROLES, default='patient')
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)
    
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'username']
    
    
    def __str__(self):
        return self.full_name

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)



class Doctor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=100)

    def __str__(self):
        return self.user.full_name

class Patient(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='patient_profile')
    assigned_doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, related_name='patients')

    def __str__(self):
        return self.user.full_name
    

class DoctorNote(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='notes')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='notes')
    note = encrypt(models.TextField())
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'Note for {self.patient.user.full_name} by {self.doctor.user.full_name}'
    

class ActionableStep(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='actionable_steps')
    note = models.ForeignKey(DoctorNote, on_delete=models.CASCADE, related_name='steps')
    step_type = models.CharField(choices=[('checklist', 'Checklist'), ('plan', 'Plan')], max_length=10)
    actionable_step = models.CharField(max_length=400, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)  # Only for 'plan' steps
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.step_type} - {self.actionable_step}"

        

class Reminder(models.Model):
    step = models.ForeignKey(ActionableStep, on_delete=models.CASCADE, related_name='reminders')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='reminders', null=True, blank=True)
    reminder_content = models.TextField()
    reminder_date = models.DateTimeField()
    sent = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Reminder for {self.step.patient.user.full_name} - {self.step.step_type}"
    
    
