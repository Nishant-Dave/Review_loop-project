from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
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
    list_display = ('cafe', 'rating', 'is_positive', 'issue', 'comment', 'formatted_date')
    list_filter = ('rating', 'is_positive', 'issue')
    ordering = ('-created_at',)
    
    def formatted_date(self, obj):
        now = timezone.now().date()
        obj_date = timezone.localtime(obj.created_at).date()
        
        if obj_date == now:
            return f"Today, {timezone.localtime(obj.created_at).strftime('%H:%M')}"
        elif obj_date == now - timezone.timedelta(days=1):
            return f"Yesterday, {timezone.localtime(obj.created_at).strftime('%H:%M')}"
        else:
            return timezone.localtime(obj.created_at).strftime('%b %d, %Y')
            
    formatted_date.short_description = 'Date'
    formatted_date.admin_order_field = 'created_at'
