from django.urls import path
from .views import (
    ProjectPublicListView,
    ProjectCreateView,
    ProjectDetailView,
    MyProjectListView,
    PendingProjectListView,
    ProjectAuditView,
    DonationCreateView,
    MyDonationListView,
    DonationDetailView,
    PaymentCallbackView,
    SimulatePaymentView,
    DonationRefundView,
    ProjectDonationListView
)

urlpatterns = [
    path('public/', ProjectPublicListView.as_view(), name='project_public_list'),
    path('create/', ProjectCreateView.as_view(), name='project_create'),
    path('my/', MyProjectListView.as_view(), name='project_my_list'),
    path('pending/', PendingProjectListView.as_view(), name='project_pending_list'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project_detail'),
    path('<int:pk>/audit/', ProjectAuditView.as_view(), name='project_audit'),
    path('<int:project_id>/donations/', ProjectDonationListView.as_view(), name='project_donation_list'),

    path('donations/', DonationCreateView.as_view(), name='donation_create'),
    path('donations/my/', MyDonationListView.as_view(), name='donation_my_list'),
    path('donations/<int:pk>/', DonationDetailView.as_view(), name='donation_detail'),
    path('donations/<int:pk>/pay/', SimulatePaymentView.as_view(), name='donation_pay'),
    path('donations/<int:pk>/refund/', DonationRefundView.as_view(), name='donation_refund'),
    path('donations/callback/', PaymentCallbackView.as_view(), name='donation_callback'),
]
