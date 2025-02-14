from django.urls import path
from .views import (
    UserSignupView, 
    UserListView,
    DoctorListViewAndSelectView,
    PatientListAndActionView,
    PatientWithActionableStepsAndRemindersView
)
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('signup', UserSignupView.as_view(), name='signup'),
    path('signin', obtain_auth_token, name='signin'),
    path('users', UserListView.as_view(), name='users'),
    path('doctors', DoctorListViewAndSelectView.as_view(), name='doctors'),
    path('patients', PatientListAndActionView.as_view(), name='patients'),
    path('patients/get-patient', PatientWithActionableStepsAndRemindersView.as_view(), name='patient'), 
]
