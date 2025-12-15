"""
Serializers for task OCR processing API.
"""
from rest_framework import serializers
from .models import ProcessingJob, ExtractedTask


class ExtractedTaskSerializer(serializers.ModelSerializer):
    """Serializer for extracted tasks."""

    class Meta:
        model = ExtractedTask
        fields = [
            'id',
            'task_name',
            'description',
            'assignee',
            'due_date',
            'priority',
            'position_index',
            'confidence_score',
            'bbox_x',
            'bbox_y',
            'bbox_width',
            'bbox_height',
            'created_at',
        ]


class ProcessingJobSerializer(serializers.ModelSerializer):
    """Serializer for processing jobs."""
    extracted_tasks = ExtractedTaskSerializer(many=True, read_only=True)

    class Meta:
        model = ProcessingJob
        fields = [
            'transaction_id',
            'status',
            'original_filename',
            'image_size',
            'created_at',
            'updated_at',
            'started_at',
            'completed_at',
            'processing_duration',
            'ocr_confidence',
            'error_message',
            'extracted_tasks',
        ]
        read_only_fields = [
            'transaction_id',
            'status',
            'created_at',
            'updated_at',
            'started_at',
            'completed_at',
            'processing_duration',
            'ocr_confidence',
            'error_message',
        ]


class JobStatusSerializer(serializers.ModelSerializer):
    """Lightweight serializer for job status checks."""
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = ProcessingJob
        fields = [
            'transaction_id',
            'status',
            'created_at',
            'completed_at',
            'processing_duration',
            'task_count',
            'error_message',
        ]

    def get_task_count(self, obj):
        """Get count of extracted tasks."""
        return obj.extracted_tasks.count()


class ImageUploadSerializer(serializers.Serializer):
    """Serializer for image upload."""
    image = serializers.ImageField(
        required=True,
        help_text='Image file of handwritten task notes'
    )

    def validate_image(self, value):
        """Validate image file."""
        # Check file size (10MB max)
        max_size = 10 * 1024 * 1024  # 10 MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f'Image file too large. Maximum size is {max_size / (1024*1024)}MB'
            )

        # Check content type - be flexible with content type detection
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'image/pjpeg']
        allowed_extensions = ['.jpg', '.jpeg', '.png']

        # Get file extension
        file_name = value.name.lower() if hasattr(value, 'name') else ''
        has_valid_extension = any(file_name.endswith(ext) for ext in allowed_extensions)

        # Accept if either content type OR extension is valid
        if value.content_type not in allowed_types and not has_valid_extension:
            raise serializers.ValidationError(
                f'Invalid file type. Allowed types: JPEG, PNG. '
                f'Received content-type: {value.content_type}'
            )

        return value
