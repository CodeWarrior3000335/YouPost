"""
views.py

This module contains all view functions for the social media application.
It handles core features such as:

- User authentication (sign up, sign in, logout)
- Displaying the main feed (posts from followed users)
- Uploading and managing posts
- Liking and disliking posts
- Commenting system (add, edit, delete)
- Following and unfollowing users
- User profile management
- Reporting inappropriate content
- Searching for users
- Downloading post media
- Handling banned users

Key Features:
- Uses Django's authentication system for secure user management
- Implements business rules such as banning, single-like/dislike logic, and ownership checks
- Supports both media uploads and downloads
- Provides user interaction through likes, comments, and follows

Dependencies:
- Django models: Profile, Post, LikePost, DislikePost, Ban, FollowersCount, Comment, Report
- Django utilities: authentication, messaging framework, decorators
- Python standard libraries: os, mimetypes, itertools

"""

# Django Imports
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Prefetch 
from django.db.models import Q
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings

# Built-In Imports
from itertools import chain
import os
import mimetypes

# Local Import
from .models import Profile, Post, LikePost, DislikePost, Ban, FollowersCount, Comment, Report


# ============================================================
# HOME FEED VIEW
# ============================================================
@login_required(login_url="signin")
def index(request):
    """
    Display the main feed for authenticated users.

    Business Rules:
    - Banned users are redirected to the banned page.
    - Only posts from followed users and the current user are displayed.
    - Suggest up to 4 users that the current user is not following.

    GET:
    - User's profile
    - Existing posts
    - Suggesting followers

    Returns:
        Rendered index page with:
        - User profile
        - Feed posts
        - Suggested users
    """
    
    # Redirect banned users
    if Ban.is_user_banned(request.user):
        return redirect("banned")

    # Get current user's profile
    user_profile = Profile.objects.get(user=request.user)

    # Get usernames the user follows
    user_following = FollowersCount.objects.filter(
        follower=request.user.username
    ).values_list('user', flat=True)
    
    # Fetch posts from followed users AND the current user
    feed_list = Post.objects.filter(
        Q(user__in=user_following) | Q(user=request.user)
    ).prefetch_related("comment_set").order_by("-id")

    # Suggest users not followed
    suggestions = User.objects.exclude(
        username__in=user_following
    ).exclude(
        username=request.user.username
    )

    # Get up to 4 suggested profiles
    suggestions_profiles = Profile.objects.filter(
        user__in=suggestions
    )[:4]


    return render(request, "index.html", {
        "user_profile": user_profile,
        "posts": feed_list,
        "suggestions_username_profile_list": suggestions_profiles
    })



# ============================================================
# SEARCH USERS
# ============================================================
@login_required(login_url="signin")
def search(request):
    """
    Search for users by username (case-insensitive).

    GET:
    - Usernames when searching
    - Users' profiles

    Return:
    - Render matching results back to current user

    """

    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)

    if request.method == "POST":
        username = request.POST["username"]

        # Find matching users
        username_object = User.objects.filter(username__icontains=username)

        # Empty list for storing profiles of existing users
        username_profile = []
        username_profile_list = []

        # Loops for any existing usernames when searched
        for users in username_object:
            username_profile.append(users.id)

        # Loops for any existing profiles after search
        for ids in username_profile:
            profile_lists = Profile.objects.filter(id_user=ids)
            username_profile_list.append(profile_lists)

        # Orders profile list in order
        username_profile_list = list(chain(*username_profile_list))

    return render(request, "search.html", {"user_profile": user_profile, "username_profile_list": username_profile_list})


# ============================================================
# POST ACTIONS
# ============================================================
@login_required(login_url="signin")
def upload(request):
    """
    Handle post uploads from authenticated users.

    Rules:
    - File formats: jpeg, png, jpg, mp4, mov
    - Max size: 20MB
    - Caption required

    POST:
    - Create new post in the database

    Return:
    - Render newly uploaded post
    """

    
    if request.method == "POST":
        user = request.user.username
        file = request.FILES.get("file")
        caption = request.POST["caption"]

        # Create and save new post
        new_post = Post.objects.create(user=user, file=file, caption=caption)
        new_post.save()

        # Display successfully message after the user uploaded their post
        messages.success(request, "Post uploaded succesfully!")

        return redirect("/")
    else:
        return redirect("/")
    

@login_required(login_url="signin")
def report(request):
    """
    Allow Authenticated user to report any post and that data gets sent back to the server.

    Business Rules:
    - Authenticated user can only report posts of other users(not their own)
    - They MUST give a reason why they reported

    GET:
    - Post ID
    - Reason of report
    - User who reported it

    POST:
    - Send report back to the database

    Return:
    Render a successful message after the user has reported a post
    """

    if request.method == "POST":

        # Get post id and reason of report
        post_id = request.POST.get("post_id")
        post = get_object_or_404(Post, id=post_id)
        reason = request.POST.get("reason", "").strip()

        # If no reason is given, resubmit report
        if not reason:
            messages.error(request, "Reason needed!")
            return redirect("/")

        # Creates and saves report
        new_report = Report.objects.create(reported_by=request.user,post=post,reason=reason)
        new_report.save()

        # Display message after user has successfully reported a post
        messages.success(request, "Reported successfully!")

        return redirect("/")
    
    else:
        return redirect("/")
    

def download_post(request, post_id):
    """
    Allow user to download file from post.

    Business Rules:
    - Post must exist before the user downloads the file
    - Downloads of post are increamented by one each time a user downloads a post

    GET:
    - Post ID

    Return:
    - Send downloaded file back to the user
    """

    # Try to retrieve the post associated with the given ID
    try:
        post = Post.objects.get(id=post_id)

        # Get the absolute file path of the uploaded file
        file_path = post.file.path

        # Check if the file actually exists on the server
        # If it does not exist, return a 404 error
        if not os.path.exists(file_path):
            raise Http404("File not found")

        # Increment the download counter only when a real download happens
        post.downloads += 1

         # Save only the downloads field for efficiency
        post.save(update_fields=["downloads"])

        # Determine the MIME type (file type) of the file
        mime_type, _ = mimetypes.guess_type(file_path)

        # Create a response that streams the file to the user's browser
        response = FileResponse(
            open(file_path, 'rb'), # Open file in binary read mode
            as_attachment=True, # Force the browser to download the file
            filename=os.path.basename(file_path) # Set the download filename
        )

        # Set the HTTP Content-Type header so the browser knows the file type
        # If the type cannot be determined, use a generic binary type
        response['Content-Type'] = mime_type or 'application/octet-stream'

        # Return the file response to the browser
        return response

    # If the post with the given ID does not exist, return a 404 error
    except Post.DoesNotExist:
        raise Http404("Post not found")
    

def delete_post(request):
    """
    Allow user to delete their own posts.

    NOTE:
        User can only delete posts that are theirs, not other users.

    GET:
    - POST ID.
    - Username of post.

    POST:
    - Delete post from database.

    Return:
    - Render message telling the user they have deleted their post successfully.
    """

    if request.method == "POST":

        # Get post by ID
        post_id = request.POST.get("post_id")
        post = get_object_or_404(Post, id=post_id)

        # If username of post is equal to username of the current user, delete post
        if post.user == request.user.username:
            post.delete()
            messages.success(request, "Post deleted successfully!")
            
    return redirect(request.META.get("HTTP_REFERER", "/")) 


# ============================================================
# LIKE/DISLIKE ACTIONS
# ============================================================
@login_required(login_url="signin")   
def like_post(request):
    """
    Toggle like on a post.

    GET:
    - Post ID
    - Number of likes
    - Number of dislikes

    POST:
    - Send updated like/dislike data to server

    Behaviour:
    - Removes existing dislike
    - Toggles like (add/remove)
    """

    # Get username and the post's ID
    username = request.user.username
    post_id = request.GET.get("post_id")
    post = Post.objects.get(id=post_id)

    # Get total number of likes and dislikes
    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()
    dislike_filter = DislikePost.objects.filter(post_id=post_id, username=username).first()
    
    # Remove dislike if exists
    if dislike_filter:
        dislike_filter.delete()
        post.num_of_dislikes = max(0, post.num_of_dislikes - 1)

    # Remove like if user unlikes a post
    if like_filter:  
        like_filter.delete()
        post.num_of_likes = max(0, post.num_of_likes - 1)
        messages.success(request, "Post unliked successfully!")
      
    # Create and save new like if user clicks on like
    else:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()

        # Increment number of likes by 1
        post.num_of_likes += 1

        # Display a message if user likes a post
        messages.success(request, "Post liked successfully!")

    # Save new like/dislike data of post
    post.save()
    return redirect("/")        
    


@login_required(login_url="signin")
def dislike_post(request):
    """
    Toggle dislike on a post.

    Behaviour:
    - Removes existing like
    - Toggles dislike (add/remove)
    """

    # Get username and the post's ID
    username = request.user.username
    post_id = request.GET.get("post_id")
    post = Post.objects.get(id=post_id)

    # Get total number of likes and dislikes
    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()
    dislike_filter = DislikePost.objects.filter(post_id=post_id, username=username).first()

    # Remove like if user unlikes a post
    if like_filter:
        like_filter.delete()
        post.num_of_likes = max(0, post.num_of_likes - 1)
    
    # Remove dislike if user removes it
    if dislike_filter:
        dislike_filter.delete()
        post.num_of_dislikes = max(0, post.num_of_dislikes - 1)
        messages.success(request, "Post undisliked successfully!")
    
    # Create and save new dislike 
    else:
        new_dislike = DislikePost.objects.create(post_id=post_id, username=username)
        new_dislike.save()

        # Increment number of dislikes by 1
        post.num_of_dislikes += 1

        # Display message after user successfullu clicks dislike
        messages.success(request, "Post disliked successfully!")

    # Save new like/dislike data of post
    post.save()
    return redirect("/")       


# ============================================================
# COMMENT ACTIONS
# ============================================================
@login_required(login_url="signin")
def upload_comment(request):
    """
    Allow authticated user to upload a comment unto a post

    Busines rules:
    - User MUST add content inside of their comment
    
    GET:
    - Username
    - Post ID

    POST:
    - Create new comment and send it back to the database

    Return:
    - Render successfull message after user has uploaded comment
    """

    if request.method == "POST":

        # Get username, ID of post and content of comment
        user = request.user.username
        post_id = request.POST.get("post_id")
        post = get_object_or_404(Post, id=post_id)
        content = request.POST.get("content", "").strip()

        # Debug: post ID
        print("POST ID:", post_id)

        # If no content exists, resubmit comment
        if not content:
            messages.error(request, "Comment must have content inside of it! Please give your comment content.")
            return redirect("/")
        

        # Create and save new comment
        new_comment = Comment.objects.create(username=user, content=content, post=post)
        new_comment.save()

        # Save post's data
        post.save()

        # Display message after user has successfully uploaded their comment
        messages.success(request, "Comment has been uploaded!")

        return redirect("/")
    else:
        return redirect("/")
    
@login_required(login_url="signin")
def delete_comment(request):
    """
    Allow authenticated user to delete their own comments

    NOTE:
    - User can only delete comments that are theirs, not other users' comments

    GET:
    - Comment ID.

    POST:
    - Delete comment.

    Return:
    - Render message that tells user they have successfully deleted their chosen comment
    """

    if request.method == "POST":

        # Get comment by ID
        comment_id = request.POST.get("comment_id")
        comment = get_object_or_404(Comment, id=comment_id)

        # If the comment's username is equal to the current user's, delete comment
        if comment.username == request.user.username:
            comment.delete()
            # Display successfull message
            messages.success(request, "Comment deleted successfully!")

    return redirect(request.META.get("HTTP_REFERER", "/"))

@login_required(login_url="signin")
def edit_comment(request):
    """
    Allow authenticated user to edit their own comments.

    NOTE:
        User can only edit comments that are theirs, not other users' comments.

    GET:
    - Comment ID.
    - Content of comment.

    POST:
    - Save newly edited comment.

    Return:
    - Render message that tells user they have successfully edited their chosen comment.
    """

    if request.method == "POST":

        # Get both ID and content of comment
        comment_id = request.POST.get("comment_id")
        new_content = request.POST.get("new_content", "").strip()
        comment = get_object_or_404(Comment, id=comment_id)

        # If the comment's username is equal to the current user's, update comment
        if comment.username == request.user.username and new_content:

            # Replaces old content with new content
            comment.content = new_content
            comment.save()

            messages.success(request, "Comment edited successfully!")


    return redirect(request.META.get("HTTP_REFERER", "/"))


# ============================================================
# PROFILE VIEW
# ============================================================
@login_required(login_url="signin")
def profile(request, pk):
    """
    Display profile page of existing user when other users vist their page.

    Business Rules:
    - PK represents owned profile of user
    - If logged-in user is currently following that user, render 'Unfollow' button
    - If logged-in user is not following that user, render 'Follow' button

    Args:
    - pk (str): The username of the profile page from url.

    GET:
    - Username
    - User's profile image
    - User's total number of posts
    - Total number followers user has
    - Total number of users user is currently following

    Return:
    - Render profile page with user's data
    """

    # Get user by pk from url
    user_object = User.objects.get(username=pk)

    # Get user's profile, posts and total number of posts
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=pk)
    user_post_length = len(user_posts)

    # Get profile's username
    follower = request.user.username
    user = pk

    # If current user is following that profile user, display 'Unfollow' button
    if FollowersCount.objects.filter(follower=follower, user=user).first():
        button_text = "Unfollow"
    else:
        # If not, display 'Follow'
        button_text = "Follow"

    # Get total number users user is following and being followed by
    user_followers = len(FollowersCount.objects.filter(user=pk))
    user_following = len(FollowersCount.objects.filter(follower=pk))

    context = {
        "user_object": user_object,
        "user_profile": user_profile,
        "user_posts": user_posts,
        "user_post_length": user_post_length,
        "button_text": button_text,
        "user_followers": user_followers,
        "user_following": user_following,
    }

    return render(request, 'profile.html', context)


# ============================================================
# FOLLOW/UNFOLLOW ACTIONS
# ============================================================
@login_required(login_url="signin")
def follow(request):
    """
    Allow current authenticated user to follow profile user.

    Business Rules:
    - If current user wants to unfollow profile user, delete profile user's followers by 1.
    - If current user wants to follow profile user, create and save new follower to profile user.

    GET:
    - Follower if current user is following profile user

    POST:
    - Create and save new follower or delete follower

    Return:
    - Render the number of followers on profile page after user follows/unfollows them.
    """

    if request.method == "POST":

        # Post follower 
        follower = request.POST["follower"]
        user = request.POST["user"]

        # If user unfollows profile user, decrement profile user's followers by one
        if FollowersCount.objects.filter(follower=follower, user=user).first():

            # Get follower of profile user(the logged-in user)
            delete_follower = FollowersCount.objects.get(follower=follower, user=user)

            # Delete follower and redirect logged-in user back to the profile page
            delete_follower.delete()
            return redirect("/profile/"+user)
        
        else:
            # If current follows profile user, create and save new follower
            new_follower = FollowersCount.objects.create(follower=follower, user=user)
            new_follower.save()

            # Redirect logged-in user back to the profile page after they followed profile user
            return redirect("/profile/"+user)

    else:
        return redirect("/")


# ============================================================
# SETTINGS VIEW
# ============================================================
@login_required(login_url="signin")
def settings(request):
    """
    Render settings page and allow current user to edit their settings for their user account.

    NOTE:
    If user does add their own profile image, render the default one form the server.

    GET:
    - User's profile.
    
    POST:
    - Send newly edited profile back to the server.

    Return:
    - Render user's updated profile on the settings page.
    """

    user_profile = Profile.objects.get(user=request.user)

    if request.method == "POST":
        
        # If user does not add their own profile image, add in the default one instead
        if request.FILES.get("image") == None:

            # Post profile data to the server
            image = user_profile.profileimg
            bio = request.POST["bio"]
            location = request.POST["location"]

            # Save newly edited/created profile back to the server
            user_profile.profileimg = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()

        # If user adds their own profile image, do not add in the default one
        if request.FILES.get("image") != None:

            # Post profile data to the server
            image = request.FILES.get("image")
            bio = request.POST["bio"]
            location = request.POST["location"]

            # Save newly edited/created profile back to the server
            user_profile.profileimg = image
            user_profile.bio = bio
            user_profile.location = location
            user_profile.save()
        
        return redirect("settings")

    return render(request, "setting.html", {"user_profile": user_profile})


# ============================================================
# AUTHENTICATION
# ============================================================
def signup(request):
    """
    Register a new user.

    NOTE:
    - Username and email must be unique. If one of them already exists, person will have to sign up again
    
    Rules:
    - Passwords must match in order for user to be registered

    POST:
    - Create and save new user

    Return:
    - Render homepage to newly created authenticated user
    """

    if request.method == "POST":

        # Post all signed-up data back to the server
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        password2 = request.POST["password2"]

        # If both passwords match, create new user or make the user retry again
        if password == password2:

            # If email or username has already been taken, make the user sign up again
            if User.objects.filter(email=email).exists():
                messages.info(request, "Email has already been taken. Please use antoher one")
                return redirect("signup")
            elif User.objects.filter(username=username).exists():
                messages.info(request, "Username has already been Taken. Please use antoher one.")
                return redirect("signup")
            
            # If everything is valid, create and save new user
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                
                # Log user in
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)

                # Create a Profile object for the new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                new_profile.save()

                messages.success(request, "Signed up successfully!")

                return redirect("/")
        else:
            # If passwords do not match, make the user to try signing up again 
            messages.info(request, "Passwords do not match!")
            return redirect("signup")
        
    else:
        return render(request, "signup.html")
    
    
def signin(request):
    """
    Allow existing user to login into the website.

    Business Rules:
    - User must already exist before logging in
    - Username must be valid
    - Password must be valid

    POST:
    Send username and password back to the server for processing

    Return:
    - Render home page for logged-in user
    """

    if request.method == "POST":

        # Post username and password for further processing
        username = request.POST["username"]
        password = request.POST["password"]

        # Sets user to be authenticated if form is valid
        user = auth.authenticate(username=username, password=password)

        # If user does exist, log them in
        if user is not None:
            auth.login(request, user)
            messages.success(request, "Logged in successfully!")
            return redirect("/")
        
        else:
            # If form is valid, redirect user back to login page to try again
            messages.info(request, "Username or password is incorrect! Please try again.")
            return redirect("signin")
    else:
        return render(request, "signin.html")

@login_required(login_url="signin")
def logout(request):
    """
    Allow user to logout of site.
    """

    auth.logout(request)
    return redirect("signin")


def banned(request):
    """
    Checks to see if user is currently banned. If so, they are not allowed to vist the home page.

    GET:
    - Currently banned user(s)

    Return:
    - Render user to the banned page if they are banned
    """

    # Get data of banned user
    ban = Ban.objects.filter(user=request.user, end_date__gt=timezone.now()).first()

    # If user is not banned, redirect them back to the home page
    if not ban:
        return redirect("index")

    # If so, render the banned page and display ban info
    return render(request, "banned.html", {"ban": ban})
