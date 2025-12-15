"""
Models for task OCR processing.
"""
import uuid
from django.db import models
from django.utils import timezone


class ProcessingJob(models.Model):
    """
    Represents an image processing job for OCR extraction.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    # Transaction ID (public-facing identifier)
    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    # Image information
    image_path = models.CharField(max_length=500)
    original_filename = models.CharField(max_length=255)
    image_size = models.IntegerField(help_text='Size in bytes')

    # Processing status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    # Celery task tracking
    celery_task_id = models.CharField(max_length=255, blank=True, null=True)

    # Error tracking
    error_message = models.TextField(blank=True, null=True)
    error_traceback = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # OCR metadata
    ocr_confidence = models.FloatField(null=True, blank=True)
    processing_duration = models.FloatField(
        null=True,
        blank=True,
        help_text='Duration in seconds'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Job {self.transaction_id} - {self.status}"

    def mark_processing(self, celery_task_id=None):
        """Mark job as processing."""
        self.status = 'processing'
        self.started_at = timezone.now()
        if celery_task_id:
            self.celery_task_id = celery_task_id
        self.save(update_fields=['status', 'started_at', 'celery_task_id', 'updated_at'])

    def mark_completed(self, ocr_confidence=None):
        """Mark job as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if self.started_at:
            self.processing_duration = (self.completed_at - self.started_at).total_seconds()
        if ocr_confidence:
            self.ocr_confidence = ocr_confidence
        self.save(update_fields=[
            'status', 'completed_at', 'processing_duration',
            'ocr_confidence', 'updated_at'
        ])

    def mark_failed(self, error_message, error_traceback=None):
        """Mark job as failed."""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.error_traceback = error_traceback
        if self.started_at:
            self.processing_duration = (self.completed_at - self.started_at).total_seconds()
        self.save(update_fields=[
            'status', 'completed_at', 'error_message',
            'error_traceback', 'processing_duration', 'updated_at'
        ])


class ExtractedTask(models.Model):
    """
    Represents a task extracted from handwritten notes via OCR.
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    # Link to processing job
    job = models.ForeignKey(
        ProcessingJob,
        on_delete=models.CASCADE,
        related_name='extracted_tasks'
    )

    # Task details
    task_name = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    assignee = models.CharField(max_length=255, blank=True, null=True)
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    # Position in the original image
    position_index = models.IntegerField(
        default=0,
        help_text='Order of appearance in the original image'
    )

    # OCR metadata for this specific task
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        help_text='OCR confidence for this task'
    )

    # Bounding box coordinates (if available from OCR)
    bbox_x = models.IntegerField(null=True, blank=True)
    bbox_y = models.IntegerField(null=True, blank=True)
    bbox_width = models.IntegerField(null=True, blank=True)
    bbox_height = models.IntegerField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['job', 'position_index']
        indexes = [
            models.Index(fields=['job', 'position_index']),
        ]

    def __str__(self):
        return f"{self.task_name} (Job: {self.job.transaction_id})"
