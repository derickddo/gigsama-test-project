from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import CustomUser, Doctor, Patient, DoctorNote, ActionableStep
from rest_framework import status
from .serializers import UserSerializer, UserSignupSerializer, PatientSerializer, ActionableStepSerializer, PatientWithRemindersSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import check_password
from rest_framework.exceptions import ParseError, AuthenticationFailed
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login
from rest_framework.permissions import IsAuthenticated
from .permissions import IsPatient, IsDoctor
from .llm_utlis import extract_actionable_steps
from datetime import datetime


# Create your views here.
class UserSignupView(APIView):
    def post(self, request):
        serializer = UserSignupSerializer(data=request.data)
        data = {}
        if serializer.is_valid():
            user = serializer.save()
            token = Token.objects.get(user=user).key
            data['response'] = 'Successfully registered a new user.'
            data['email'] = user.email
            data['full_name'] = user.full_name
            data['role'] = user.role
            data['token'] = token
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class UserListView(APIView):
    def get(self, request):
        users = CustomUser.objects.all()
        serializer = UserSerializer(users, many=True)
        if users:
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'error': 'No users found'}, status=status.HTTP_404_NOT_FOUND)
            

# view to view all doctors if the authenticate user is a patient and select a doctor
class DoctorListViewAndSelectView(APIView):
    permission_classes = [IsPatient, IsAuthenticated]
    
    def get(self, request):
        doctors = CustomUser.objects.filter(role='doctor')
        serializer = UserSerializer(doctors, many=True)
        if doctors:
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'error': 'No doctors found'}, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request):
        doctor_id = request.data.get('doctor_id')
        patient_id = request.user.id
        
        patient = Patient.objects.get(user_id=patient_id)
        doctor = Doctor.objects.get(user_id=doctor_id)
        if not doctor:
            return Response({'error': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if not patient:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)
 
        patient.assigned_doctor = doctor
        patient.save()
        serializer = UserSerializer(patient.user)
        data = serializer.data
        data['success'] = 'Doctor assigned successfully'
        return Response(data, status=status.HTTP_200_OK)
    
    def patch (self, request):
        patient_id = request.user.id
        doctor_id = request.data.get('doctor_id')
        
        patient = Patient.objects.get(user_id=patient_id)
        doctor = Doctor.objects.get(user_id=doctor_id)
        
        if not doctor:
            return Response({'error': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if not patient:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # update the assigned doctor
        patient.assigned_doctor = doctor
        patient.save()
        serializer = UserSerializer(patient.user)
        data = serializer.data
        data['success'] = 'Doctor assignment updated successfully'
        return Response(data, status=status.HTTP_200_OK)
        
    
        
class PatientListAndActionView(APIView):
    permission_classes = [IsDoctor, IsAuthenticated]
    
    def get(self, request):
        # get all patients assigned to the doctor
        patients = Patient.objects.filter(assigned_doctor=request.user.doctor_profile)
        serializer = PatientSerializer(patients, many=True)
        if patients:
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'error': 'No patients found for this doctor'}, status=status.HTTP_404_NOT_FOUND)
    def post(self, request):
        # add notes to the patient
        patient_id = request.data.get('patient_id')
        notes = request.data.get('notes')
        
        patient = Patient.objects.get(user_id=patient_id)
        if not patient:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)
        doctor = Doctor.objects.get(user_id=request.user.id)
        note = DoctorNote.objects.create(doctor=doctor, patient=patient, note=notes)
        note.save()
        
        # remove old actionable steps
        ActionableStep.objects.filter(patient=patient).delete()
        # Generate new actionable steps from LLM
    
        new_steps = extract_actionable_steps(notes)
        print(new_steps)
        
        for step in new_steps:
            print(f"step_type: {step}")
            step_type = step
            due_date = new_steps['due_date'][0]
            # convert due date (21 Feb 2023) to a datetime object
            due_date = datetime.strptime(due_date, '%d %b %Y')
            
            print(f"due_date: {due_date}")
            step_note = new_steps[step][0]
            print(f"step_note: {step_note}")
            actionable_step = ActionableStep.objects.create(patient=patient, actionable_step=step_note, note=note, step_type=step_type, due_date=due_date) 
            actionable_step.save()
        
        # get all the actionable steps
        actionable_steps = ActionableStep.objects.filter(patient=patient)
        serializer = ActionableStepSerializer(actionable_steps, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
        
        
class PatientWithActionableStepsAndRemindersView(APIView):
    permission_classes = [IsPatient, IsAuthenticated]
    
    def get(self, request):
        try:
            patient = Patient.objects.get(user_id=request.user.id)
            serializer = PatientWithRemindersSerializer(patient, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)
    



