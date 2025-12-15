"""
API views for task OCR processing.
"""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404

from .models import ProcessingJob
from .serializers import (
    ImageUploadSerializer,
    ProcessingJobSerializer,
    JobStatusSerializer,
)
from .tasks import process_task_image

logger = logging.getLogger(__name__)


class ImageUploadView(APIView):
    """
    API endpoint to upload task image for OCR processing.

    POST /api/upload
    - Accepts: multipart/form-data with 'image' field
    - Returns: transaction_id
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        """Handle image upload."""
        serializer = ImageUploadSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        image_file = serializer.validated_data['image']

        try:
            # Save image to MinIO/S3
            file_path = default_storage.save(
                f"uploads/{image_file.name}",
                image_file
            )

            # Create processing job record
            job = ProcessingJob.objects.create(
                image_path=file_path,
                original_filename=image_file.name,
                image_size=image_file.size,
                status='pending'
            )

            # Trigger async OCR processing
            task = process_task_image.delay(job.id)
            job.celery_task_id = task.id
            job.save(update_fields=['celery_task_id'])

            logger.info(
                f"Image uploaded successfully. Job: {job.transaction_id}, "
                f"Task: {task.id}"
            )

            return Response({
                'transaction_id': str(job.transaction_id),
                'status': job.status,
                'message': 'Image uploaded successfully. Processing started.'
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error uploading image: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to upload image. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class JobStatusView(APIView):
    """
    API endpoint to check processing job status.

    GET /api/status/{transaction_id}
    - Returns: job status and results if completed
    """

    def get(self, request, transaction_id):
        """Get job status and results."""
        job = get_object_or_404(
            ProcessingJob,
            transaction_id=transaction_id
        )

        # If job is completed, return full details
        if job.status == 'completed':
            serializer = ProcessingJobSerializer(job)
        else:
            # Otherwise, return lightweight status
            serializer = JobStatusSerializer(job)

        return Response(serializer.data)


class JobDetailView(APIView):
    """
    API endpoint to get full job details.

    GET /api/jobs/{transaction_id}
    - Returns: complete job information with extracted tasks
    """

    def get(self, request, transaction_id):
        """Get complete job details."""
        job = get_object_or_404(
            ProcessingJob,
            transaction_id=transaction_id
        )

        serializer = ProcessingJobSerializer(job)
        return Response(serializer.data)
