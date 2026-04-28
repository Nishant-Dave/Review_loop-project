from django.contrib import admin
from .models import Cafe, Feedback

@admin.register(Cafe)
class CafeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('cafe', 'rating', 'issue', 'comment', 'created_at')
    list_filter = ('rating', 'issue')
    ordering = ('-created_at',)
