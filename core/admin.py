from django.contrib import admin
from .models import CustomUser, Doctor, Patient, DoctorNote, ActionableStep, Reminder

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Doctor)
admin.site.register(Patient)
admin.site.register(DoctorNote)
admin.site.register(ActionableStep)
admin.site.register(Reminder)


