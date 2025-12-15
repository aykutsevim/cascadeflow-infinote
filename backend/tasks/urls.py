"""
URL routing for tasks API.
"""
from django.urls import path
from .views import ImageUploadView, JobStatusView, JobDetailView

app_name = 'tasks'

urlpatterns = [
    # Upload image for OCR processing
    path('upload/', ImageUploadView.as_view(), name='upload'),

    # Check job status
    path('status/<uuid:transaction_id>/', JobStatusView.as_view(), name='status'),

    # Get full job details
    path('jobs/<uuid:transaction_id>/', JobDetailView.as_view(), name='job-detail'),
]
