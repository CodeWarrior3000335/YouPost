from django.contrib import admin
from .models import Profile, Post, LikePost, DislikePost, FollowersCount, Comment, Report, Ban

# Register your models here.
admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(DislikePost)
admin.site.register(LikePost)
admin.site.register(FollowersCount)
admin.site.register(Comment)
admin.site.register(Report)
admin.site.register(Ban)