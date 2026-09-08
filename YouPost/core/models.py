"""
models.py

Django Models Module for Social Media Application

This module defines all database models used in the application, including
user profiles, posts, interactions (likes/dislikes), comments, reports,
followers, and user bans.

Models Overview:
- Profile: Stores additional user information such as bio, profile image, and location.
- Post: Represents user-generated content (images/videos) with captions and engagement metrics.
- LikePost / DislikePost: Track user interactions with posts.
- FollowersCount: Manages follower-following relationships between users.
- Comment: Stores user comments on posts.
- Report: Allows users to report posts with a reason.
- Ban: Handles temporary user bans and provides a utility method to check ban status.

Key Features:
- Uses UUIDs for unique identification of posts and comments.
- Enforces file size validation for uploaded media.
- Automatically deletes related objects using cascading relationships.
- Includes helper methods for checking file types and user ban status.

Dependencies:
- Django ORM for database interactions
- Custom file validation (`validate_file_size`)
- Python standard libraries (uuid, datetime, os)

This module is central to managing application data and enforcing
business rules related to user interactions and content moderation.

"""

# Django Imports
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

# Local Import
from .validators import validate_file_size

# Built-In Imports
import uuid
import os
from datetime import datetime

User = get_user_model()


# =================================
# PROFILE MODEL
# =================================
class Profile(models.Model):
    """
    Model representing additional user profile information.
    Each user has a corresponding profile.

    Key Features:
    - Stores user bio, profile image, and location
    - Automatically deleted when the associated user is deleted (CASCADE)
    - Provides a default profile image if none is uploaded
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    id_user = models.IntegerField()
    bio = models.TextField(blank=True)
    profileimg = models.ImageField(upload_to="profile_images", default="blank-profile.jpg") # If user does not add their own image, bring the default one
    location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        """Return username as string representation of profile."""
        return self.user.username


# =================================
# POST MODEL
# =================================   
class Post(models.Model):
    """
    Model representing a user post (image or video).

    Key Features:
    - Supports media uploads (image/video)
    - Enforces file size validation (max 20MB)
    - Tracks likes, dislikes, and downloads
    - Uses UUID for unique post identification
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4) # Every post should have an unique id
    user = models.CharField(max_length=100)
    file = models.FileField(upload_to="posts/", blank=True, null=True, validators=[validate_file_size]) # Max file size is 20 MB
    caption = models.TextField()
    created_at = models.DateTimeField(default=datetime.now)
    num_of_likes = models.IntegerField(default=0)
    num_of_dislikes = models.IntegerField(default=0)
    downloads = models.IntegerField(default=0)

    def is_image(self):
        """
        Check if uploaded file is an image.

        Returns:
            bool: True if file is .jpg, .jpeg, or .png
        """

        return os.path.splitext(self.file.name)[1].lower() in ['.jpg', '.jpeg', '.png']

    def is_video(self):
        """
        Check if uploaded file is a video.

        Returns:
            bool: True if file is .mp4 or .mov
        """

        return os.path.splitext(self.file.name)[1].lower() in ['.mp4', '.mov']

    def __str__(self):
        """Return username as string representation of post."""
        return self.user
    

# =================================
# LIKE AND DISLIKE MODELS
# =================================
class LikePost(models.Model):
    """
    Model representing a like on a post.

    Each user can like a post once.
    """

    post_id = models.CharField(max_length=500)
    username = models.CharField(max_length=100)

    def __str__(self):
        """Return username as representation."""
        return self.username
    
class DislikePost(models.Model):
    """
    Model representing a dislike on a post.

    Each user can dislike a post once.
    """

    post_id = models.CharField(max_length=500)
    username = models.CharField(max_length=100)

    def __str__(self):
        """Return username as representation."""
        return self.username
    

# =================================
# FOLLOWERS COUNT MODEL
# =================================
class FollowersCount(models.Model):
    """
    Model representing follower relationships between users.

    Stores:
    - follower : the person following
    - user : the person being followed
    """

    follower = models.CharField(max_length=100)
    user = models.CharField(max_length=100)

    def __str__(self):
        """Return followed user's username."""
        return self.user
    

# =================================
# COMMENT MODEL
# =================================
class Comment(models.Model):
    """
    Model representing a comment on a post.

    Key Features:
    - Linked to a specific post
    - Automatically deleted if the post is deleted
    - Requires content
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    username = models.CharField(max_length=100)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        """Return username as representation."""
        return self.username


# =================================
# REPORT MODEL
# =================================
class Report(models.Model):
    """
    Model representing a report made by a user on a post.

    Key Features:
    - Stores reason for report
    - Linked to both user and post
    - Automatically deleted if user or post is removed
    """

    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return readable report description."""
        return f"Report on {self.post} by {self.reported_by.username}"

# =================================
# BAN MODEL
# =================================
class Ban(models.Model):
    """
    Model representing a temporary ban on a user.

    Key Features:
    - Stores reason for ban
    - Tracks start and end dates
    - Provides helper method to check if a user is currently banned
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()

    @staticmethod
    def is_user_banned(user):
        """
        Check if a user is currently banned.

        Args:
            user (User): The user to check

        Returns:
            bool: True if user is banned, otherwise False
        """

        return Ban.objects.filter(
            user=user,
            end_date__gt=timezone.now()
        ).exists()

    def __str__(self):
        """Return readable ban description."""
        return f"{self.user.username} banned until {self.end_date}"
    