"""
Celery tasks for OCR processing of handwritten task notes.
"""
import logging
import traceback
from datetime import datetime
from io import BytesIO
from PIL import Image

from celery import shared_task
from django.conf import settings
from django.core.files.storage import default_storage

from .models import ProcessingJob, ExtractedTask
from .ocr_service import get_ocr_service

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_task_image(self, job_id):
    """
    Process uploaded image to extract handwritten tasks using OCR.

    Args:
        job_id: ID of the ProcessingJob

    Returns:
        dict: Processing results
    """
    job = None
    try:
        # Get the job
        job = ProcessingJob.objects.get(id=job_id)
        logger.info(f"Starting OCR processing for job {job.transaction_id}")

        # Mark as processing
        job.mark_processing(celery_task_id=self.request.id)

        # Download image from storage
        image_file = default_storage.open(job.image_path, 'rb')
        image_data = image_file.read()
        image_file.close()

        # Open image with PIL
        image = Image.open(BytesIO(image_data))

        # Get singleton OCR service instance (model loaded only once)
        ocr_service = get_ocr_service(
            confidence_threshold=settings.OCR_CONFIDENCE_THRESHOLD
        )

        # Perform OCR extraction
        logger.info(f"Running OCR on image for job {job.transaction_id}")
        ocr_results = ocr_service.extract_tasks(image)

        # Save extracted tasks to database
        tasks_created = 0
        total_confidence = 0

        for idx, task_data in enumerate(ocr_results.get('tasks', [])):
            ExtractedTask.objects.create(
                job=job,
                task_name=task_data.get('name', ''),
                description=task_data.get('description', ''),
                assignee=task_data.get('assignee', ''),
                due_date=task_data.get('due_date'),
                priority=task_data.get('priority', 'medium'),
                position_index=idx,
                confidence_score=task_data.get('confidence'),
                bbox_x=task_data.get('bbox', {}).get('x'),
                bbox_y=task_data.get('bbox', {}).get('y'),
                bbox_width=task_data.get('bbox', {}).get('width'),
                bbox_height=task_data.get('bbox', {}).get('height'),
            )
            tasks_created += 1

            if task_data.get('confidence'):
                total_confidence += task_data['confidence']

        # Calculate average confidence
        avg_confidence = (
            total_confidence / tasks_created if tasks_created > 0 else 0
        )

        # Mark job as completed
        job.mark_completed(ocr_confidence=avg_confidence)

        logger.info(
            f"OCR processing completed for job {job.transaction_id}. "
            f"Extracted {tasks_created} tasks with avg confidence {avg_confidence:.2f}"
        )

        return {
            'status': 'completed',
            'job_id': job.id,
            'transaction_id': str(job.transaction_id),
            'tasks_extracted': tasks_created,
            'average_confidence': avg_confidence,
        }

    except ProcessingJob.DoesNotExist:
        logger.error(f"ProcessingJob {job_id} not found")
        raise

    except Exception as e:
        error_msg = f"OCR processing failed: {str(e)}"
        error_trace = traceback.format_exc()
        logger.error(f"{error_msg}\n{error_trace}")

        if job:
            job.mark_failed(error_msg, error_trace)

        # Retry if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task (attempt {self.request.retries + 1})")
            raise self.retry(exc=e, countdown=60)  # Retry after 60 seconds

        return {
            'status': 'failed',
            'error': error_msg,
        }


@shared_task
def cleanup_old_jobs(days=30):
    """
    Cleanup old completed/failed jobs.

    Args:
        days: Delete jobs older than this many days
    """
    from django.utils import timezone
    from datetime import timedelta

    cutoff_date = timezone.now() - timedelta(days=days)

    # Find old jobs
    old_jobs = ProcessingJob.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['completed', 'failed']
    )

    count = old_jobs.count()
    logger.info(f"Cleaning up {count} jobs older than {days} days")

    # Delete associated images from storage
    for job in old_jobs:
        try:
            if default_storage.exists(job.image_path):
                default_storage.delete(job.image_path)
        except Exception as e:
            logger.warning(f"Failed to delete image {job.image_path}: {e}")

    # Delete job records (cascades to ExtractedTask)
    deleted_count, _ = old_jobs.delete()

    logger.info(f"Deleted {deleted_count} old jobs")

    return {
        'deleted_count': deleted_count,
        'cutoff_date': cutoff_date.isoformat(),
    }
