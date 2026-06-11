from django.urls import path
from .views import (
    ProjectPublicListView,
    ProjectCreateView,
    ProjectDetailView,
    MyProjectListView,
    PendingProjectListView,
    ProjectAuditView,
    ProjectStartView,
    ProjectUpdateUsedAmountView,
    DonationCreateView,
    MyDonationListView,
    DonationDetailView,
    PaymentCallbackView,
    SimulatePaymentView,
    DonationRefundView,
    DonationRefundPreviewView,
    ProjectDonationListView,
    RefundRequestCreateView,
    MyRefundRequestListView,
    RefundRequestListView,
    RefundRequestReviewView
)

urlpatterns = [
    path('public/', ProjectPublicListView.as_view(), name='project_public_list'),
    path('create/', ProjectCreateView.as_view(), name='project_create'),
    path('my/', MyProjectListView.as_view(), name='project_my_list'),
    path('pending/', PendingProjectListView.as_view(), name='project_pending_list'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project_detail'),
    path('<int:pk>/audit/', ProjectAuditView.as_view(), name='project_audit'),
    path('<int:pk>/start/', ProjectStartView.as_view(), name='project_start'),
    path('<int:pk>/used-amount/', ProjectUpdateUsedAmountView.as_view(), name='project_update_used_amount'),
    path('<int:project_id>/donations/', ProjectDonationListView.as_view(), name='project_donation_list'),

    path('donations/', DonationCreateView.as_view(), name='donation_create'),
    path('donations/my/', MyDonationListView.as_view(), name='donation_my_list'),
    path('donations/<int:pk>/', DonationDetailView.as_view(), name='donation_detail'),
    path('donations/<int:pk>/pay/', SimulatePaymentView.as_view(), name='donation_pay'),
    path('donations/<int:pk>/refund/', DonationRefundView.as_view(), name='donation_refund'),
    path('donations/<int:pk>/refund-preview/', DonationRefundPreviewView.as_view(), name='donation_refund_preview'),
    path('donations/callback/', PaymentCallbackView.as_view(), name='donation_callback'),

    path('refunds/', RefundRequestCreateView.as_view(), name='refund_request_create'),
    path('refunds/my/', MyRefundRequestListView.as_view(), name='my_refund_request_list'),
    path('refunds/pending/', RefundRequestListView.as_view(), name='refund_request_list'),
    path('refunds/<int:pk>/review/', RefundRequestReviewView.as_view(), name='refund_request_review'),
]
