from django.contrib import admin
from django.utils.html import format_html
from .models import Cafe, Feedback

@admin.register(Cafe)
class CafeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'logo_preview')
    readonly_fields = ('logo_preview',)
    fields = ('name', 'slug', 'google_review_link', 'logo', 'logo_preview')
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 50px; border-radius: 5px;"/>', obj.logo.url)
        return "-"
    logo_preview.short_description = 'Logo Preview'


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('cafe', 'rating', 'is_positive', 'issue', 'comment', 'created_at')
    list_filter = ('rating', 'is_positive', 'issue')
    ordering = ('-created_at',)
