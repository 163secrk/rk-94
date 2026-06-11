from django.urls import path
from .views import (
    ProjectPublicListView,
    ProjectCreateView,
    ProjectDetailView,
    MyProjectListView,
    PendingProjectListView,
    ProjectAuditView
)

urlpatterns = [
    path('public/', ProjectPublicListView.as_view(), name='project_public_list'),
    path('create/', ProjectCreateView.as_view(), name='project_create'),
    path('my/', MyProjectListView.as_view(), name='project_my_list'),
    path('pending/', PendingProjectListView.as_view(), name='project_pending_list'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project_detail'),
    path('<int:pk>/audit/', ProjectAuditView.as_view(), name='project_audit'),
]
