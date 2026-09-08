"""
validators.py

Custom validation utilities.

Contains helper functions for validating uploaded files,
such as enforcing maximum file size limits.
"""

from django.core.exceptions import ValidationError

def validate_file_size(value):
    """
    Validate that the uploaded file does not exceed 20 MB.

    Args:
        value (File): Uploaded file object.

    Raises:
        ValidationError: If file size exceeds the allowed limit.
    """

    max_size_mb = 20  # maximum size in MB

    # If the file size is more than 20 MB, raise error to user
    if value.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"Video file size must be under {max_size_mb} MB")
