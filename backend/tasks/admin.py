"""
Django admin configuration for task OCR processing.
"""
from django.contrib import admin
from .models import ProcessingJob, ExtractedTask


@admin.register(ProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    """Admin interface for ProcessingJob."""
    list_display = [
        'transaction_id',
        'status',
        'original_filename',
        'created_at',
        'processing_duration',
        'task_count',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['transaction_id', 'original_filename']
    readonly_fields = [
        'transaction_id',
        'created_at',
        'updated_at',
        'processing_duration',
    ]
    fieldsets = (
        ('Job Information', {
            'fields': ('transaction_id', 'status', 'celery_task_id')
        }),
        ('Image Details', {
            'fields': ('image_path', 'original_filename', 'image_size')
        }),
        ('Processing Info', {
            'fields': (
                'created_at',
                'updated_at',
                'started_at',
                'completed_at',
                'processing_duration',
                'ocr_confidence',
            )
        }),
        ('Error Information', {
            'fields': ('error_message', 'error_traceback'),
            'classes': ('collapse',)
        }),
    )

    def task_count(self, obj):
        """Display count of extracted tasks."""
        return obj.extracted_tasks.count()
    task_count.short_description = 'Tasks'


@admin.register(ExtractedTask)
class ExtractedTaskAdmin(admin.ModelAdmin):
    """Admin interface for ExtractedTask."""
    list_display = [
        'task_name',
        'job',
        'assignee',
        'priority',
        'due_date',
        'confidence_score',
    ]
    list_filter = ['priority', 'created_at']
    search_fields = ['task_name', 'description', 'assignee']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Task Information', {
            'fields': (
                'job',
                'task_name',
                'description',
                'assignee',
                'due_date',
                'priority',
            )
        }),
        ('OCR Metadata', {
            'fields': (
                'position_index',
                'confidence_score',
                'bbox_x',
                'bbox_y',
                'bbox_width',
                'bbox_height',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
