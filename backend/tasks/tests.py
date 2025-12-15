"""
Tests for task OCR processing.
"""
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from PIL import Image
from io import BytesIO
import uuid

from .models import ProcessingJob, ExtractedTask


class ProcessingJobModelTest(TestCase):
    """Tests for ProcessingJob model."""

    def test_create_job(self):
        """Test creating a processing job."""
        job = ProcessingJob.objects.create(
            image_path='test/path.jpg',
            original_filename='test.jpg',
            image_size=1024
        )
        self.assertIsNotNone(job.transaction_id)
        self.assertEqual(job.status, 'pending')
        self.assertIsNotNone(job.created_at)

    def test_mark_processing(self):
        """Test marking job as processing."""
        job = ProcessingJob.objects.create(
            image_path='test/path.jpg',
            original_filename='test.jpg',
            image_size=1024
        )
        task_id = str(uuid.uuid4())
        job.mark_processing(celery_task_id=task_id)

        job.refresh_from_db()
        self.assertEqual(job.status, 'processing')
        self.assertEqual(job.celery_task_id, task_id)
        self.assertIsNotNone(job.started_at)

    def test_mark_completed(self):
        """Test marking job as completed."""
        job = ProcessingJob.objects.create(
            image_path='test/path.jpg',
            original_filename='test.jpg',
            image_size=1024
        )
        job.mark_processing()
        job.mark_completed(ocr_confidence=0.85)

        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertIsNotNone(job.completed_at)
        self.assertEqual(job.ocr_confidence, 0.85)
        self.assertIsNotNone(job.processing_duration)

    def test_mark_failed(self):
        """Test marking job as failed."""
        job = ProcessingJob.objects.create(
            image_path='test/path.jpg',
            original_filename='test.jpg',
            image_size=1024
        )
        job.mark_processing()
        job.mark_failed('Test error', 'Test traceback')

        job.refresh_from_db()
        self.assertEqual(job.status, 'failed')
        self.assertEqual(job.error_message, 'Test error')
        self.assertIsNotNone(job.completed_at)


class ExtractedTaskModelTest(TestCase):
    """Tests for ExtractedTask model."""

    def setUp(self):
        """Set up test job."""
        self.job = ProcessingJob.objects.create(
            image_path='test/path.jpg',
            original_filename='test.jpg',
            image_size=1024
        )

    def test_create_task(self):
        """Test creating an extracted task."""
        task = ExtractedTask.objects.create(
            job=self.job,
            task_name='Test Task',
            description='Test description',
            assignee='John Doe',
            priority='high',
            position_index=0,
            confidence_score=0.9
        )
        self.assertEqual(task.task_name, 'Test Task')
        self.assertEqual(task.job, self.job)
        self.assertIsNotNone(task.created_at)


class ImageUploadAPITest(APITestCase):
    """Tests for image upload API."""

    def create_test_image(self):
        """Create a test image file."""
        file = BytesIO()
        image = Image.new('RGB', (800, 600), color='white')
        image.save(file, 'JPEG')
        file.seek(0)
        return SimpleUploadedFile(
            'test.jpg',
            file.read(),
            content_type='image/jpeg'
        )

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_upload_image_success(self):
        """Test successful image upload."""
        image = self.create_test_image()
        response = self.client.post(
            '/api/upload/',
            {'image': image},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('transaction_id', response.data)
        self.assertIn('status', response.data)

        # Verify job was created
        job = ProcessingJob.objects.get(
            transaction_id=response.data['transaction_id']
        )
        self.assertIsNotNone(job)

    def test_upload_without_image(self):
        """Test upload without image."""
        response = self.client.post('/api/upload/', {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_invalid_file_type(self):
        """Test upload with invalid file type."""
        file = SimpleUploadedFile(
            'test.txt',
            b'test content',
            content_type='text/plain'
        )
        response = self.client.post(
            '/api/upload/',
            {'image': file},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class JobStatusAPITest(APITestCase):
    """Tests for job status API."""

    def setUp(self):
        """Set up test job."""
        self.job = ProcessingJob.objects.create(
            image_path='test/path.jpg',
            original_filename='test.jpg',
            image_size=1024
        )

    def test_get_job_status_pending(self):
        """Test getting pending job status."""
        response = self.client.get(
            f'/api/status/{self.job.transaction_id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'pending')

    def test_get_job_status_completed(self):
        """Test getting completed job status."""
        self.job.mark_processing()
        self.job.mark_completed()

        # Create test task
        ExtractedTask.objects.create(
            job=self.job,
            task_name='Test Task',
            position_index=0
        )

        response = self.client.get(
            f'/api/status/{self.job.transaction_id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')
        self.assertIn('extracted_tasks', response.data)

    def test_get_nonexistent_job(self):
        """Test getting status of nonexistent job."""
        fake_id = uuid.uuid4()
        response = self.client.get(f'/api/status/{fake_id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
