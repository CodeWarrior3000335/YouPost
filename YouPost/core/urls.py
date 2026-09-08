"""
urls.py 

URL routing configuration.

Maps application endpoints to view functions, handling navigation for
core features such as user authentication, profiles, posts, interactions,
and content management.
"""

# Django Import
from django.urls import path

# Local Import
from . import views

urlpatterns = [
    # Home page route
    path('', views.index, name="index"),

    # Reporting and banning user routes
    path('banned', views.banned, name="banned"),
    path('report', views.report, name="report"),

    # Comment routes
    path("upload_comment", views.upload_comment, name="upload_comment"),
    path("delete_comment", views.delete_comment, name="delete_comment"),
    path("edit_comment", views.edit_comment, name="edit_comment"),

    # Post routes
    path('delete_post', views.delete_post, name="delete_post"),
    path("upload", views.upload, name="upload"),
    path('download-post/<uuid:post_id>/', views.download_post, name='download_post'),

    # Follow and search routes
    path("follow", views.follow, name="follow"),
    path("search", views.search, name="search"),

    # User information routes
    path("profile/<str:pk>", views.profile, name="profile"),
    path('settings', views.settings, name="settings"),

    # Like and dislike routes
    path("like-post", views.like_post, name="like-post"),
    path("dislike-post", views.dislike_post, name="dislike-post"),

    # Authentication routes
    path("signup", views.signup, name="signup"),
    path("signin", views.signin, name="signin"),
    path("logout", views.logout, name="logout"),
]
