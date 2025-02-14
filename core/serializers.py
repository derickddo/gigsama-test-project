from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import CustomUser, Doctor, Patient, ActionableStep, Reminder
import random

class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True) # To hide password in response

    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'password', 'role']

    def create(self, validated_data):
        # Hash the password before saving
        validated_data['password'] = make_password(validated_data['password'])
        
        # validate email as the email is an email
        if not '@' in validated_data['email']:
            raise serializers.ValidationError({'email': 'Invalid email address'})
        
        # get the first part of the email before the @ symbol and check it exists as a username
        username = validated_data['email'].split('@')[0]
        if CustomUser.objects.filter(username=username).exists():
            # add a random number to the username
            username = f"{username}{int(random.random())}"
        validated_data['username'] = username
        
        user = CustomUser.objects.create(**validated_data)

        # Create the profile based on the role
        if validated_data['role'] == 'doctor':
            Doctor.objects.create(user=user)
        elif validated_data['role'] == 'patient':
            Patient.objects.create(user=user)

        return user
    

    
    


# view all users serializer
class UserSerializer(serializers.ModelSerializer):
    assigned_doctor = serializers.SerializerMethodField() # Dynamically include assigned_doctor
    assigned_patients = serializers.SerializerMethodField() # Dynamically include assigned_patients
        
    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'role','assigned_doctor', 'assigned_patients']
        
    def get_assigned_doctor(self, obj):
        """Returns the doctor assigned to the user (if they are a patient)."""
        if hasattr(obj, 'patient_profile') and obj.patient_profile.assigned_doctor:
            return obj.patient_profile.assigned_doctor.user.full_name
        return None

    def get_assigned_patients(self, obj):
        """Returns the list of patients assigned to the user (if they are a doctor)."""
        if hasattr(obj, 'doctor_profile'):
            return [patient.user.full_name for patient in obj.doctor_profile.patients.all()]
        return []
    
    def to_representation(self, instance):
        """Dynamically include assigned_doctor or assigned_patients based on the role."""
        data = super().to_representation(instance)

        if instance.role == "patient":
            data.pop("assigned_patients", None)  # Remove assigned_patients for patients
        elif instance.role == "doctor":
            data.pop("assigned_doctor", None)  # Remove assigned_doctor for doctors
        return data


# Patient serializer
class PatientSerializer(serializers.ModelSerializer):
    assigned_doctor = serializers.SerializerMethodField() # Dynamically include assigned_doctor
    user_role = serializers.CharField(source='user.role') # Dynamically include user_role
    email = serializers.CharField(source='user.email') # Dynamically include email
    full_name = serializers.CharField(source='user.full_name') # Dynamically include full_name
    actionable_steps = serializers.SerializerMethodField() # Dynamically include actionable_steps
    
    class Meta:
        model = Patient
        fields = ['assigned_doctor', 'user_role', 'email', 'full_name', 'actionable_steps']
        
    def get_assigned_doctor(self, obj):
        """Returns the doctor assigned to the patient."""
        if obj.assigned_doctor:
            return obj.assigned_doctor.user.full_name
        return None
    
    def get_actionable_steps(self, obj):
        """Returns the list of actionable steps for the patient."""
        return ActionableStepSerializer(obj.actionable_steps.all(), many=True).data


# Doctor serializer
class DoctorSerializer(serializers.ModelSerializer):
    specialization = serializers.CharField(source='doctor_profile.specialization') # Dynamically include specialization
    user_role = serializers.CharField(source='user.role') # Dynamically include user_role
    email = serializers.CharField(source='user.email') # Dynamically include email
    full_name = serializers.CharField(source='user.full_name') # Dynamically include full_name
    
    class Meta:
        model = Doctor
        fields = ['specialization', 'user_role', 'email', 'full_name']
        
    def to_representation(self, instance):
        """Dynamically include specialization based on the role."""
        data = super().to_representation(instance)

        if instance.user.role == "patient":
            data.pop("specialization", None)  # Remove specialization for patients
        

# actionable steps serializer
class ActionableStepSerializer(serializers.ModelSerializer):
    doctor_note = serializers.CharField(source='note.note') # Dynamically include doctor_note
       
    class Meta:
        model = ActionableStep
        fields = ['actionable_step', 'due_date', 'step_type', 'completed', 'doctor_note']

   
# reminder serializer
class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = ['reminder_content', 'reminder_date']
        
 
        
# patient with reminders serializer to their actionable steps
class PatientWithRemindersSerializer(serializers.ModelSerializer):
    actionable_steps = serializers.SerializerMethodField() # Dynamically include actionable_steps
    reminders = serializers.SerializerMethodField() # Dynamically include reminders
    email = serializers.CharField(source='user.email') # Dynamically include email
    full_name = serializers.CharField(source='user.full_name') # Dynamically include full_name
    
    
    class Meta:
        model = Patient
        fields = ['email', 'full_name', 'actionable_steps', 'reminders']
        
    def get_actionable_steps(self, obj):
        """Returns the list of actionable steps for the patient."""
        return ActionableStepSerializer(obj.actionable_steps.all(), many=True).data
    
    def get_reminders(self, obj):
        """Returns the list of reminders for the patient."""
        return ReminderSerializer(obj.reminders.all(), many=True).data
        