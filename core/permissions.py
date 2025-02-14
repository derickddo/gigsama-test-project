from rest_framework import permissions

# permission to view all doctors if the authenticate user is a patient
class IsPatient(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'patient'
    
# permission to view all patients if the authenticate user is a doctor
class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'doctor'
    