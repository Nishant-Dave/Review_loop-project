from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Cafe, Feedback

@admin.register(Cafe)
class CafeAdmin(admin.ModelAdmin):
    list_display = ('name', 'tagline', 'slug', 'logo_preview', 'qr_preview')
    readonly_fields = ('logo_preview', 'qr_preview')
    fields = ('name', 'tagline', 'slug', 'google_review_link', 'logo', 'logo_preview', 'qr_code', 'qr_preview')
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 50px; border-radius: 5px;"/>', obj.logo.url)
        return "-"
    logo_preview.short_description = 'Logo Preview'

    def qr_preview(self, obj):
        if obj.qr_code:
            return format_html(
                '<div>'
                '<img src="{0}" style="max-height: 150px; border-radius: 5px; display: block; margin-bottom: 12px;"/>'
                '<div style="display: flex; gap: 10px; align-items: center;">'
                '<a href="{0}" download="qr_{1}.png" style="display: inline-block; padding: 8px 16px; font-weight: bold; text-decoration: none; background-color: #4b5563; color: white; border-radius: 6px; font-size: 13px;">Download QR Code</a>'
                '<a href="/cafe/{1}/download-qr-poster/" style="display: inline-block; padding: 8px 16px; font-weight: bold; text-decoration: none; background-color: #10b981; color: white; border-radius: 6px; font-size: 13px;">📄 Download QR Poster</a>'
                '</div>'
                '</div>',
                obj.qr_code.url, obj.slug
            )
        return "-"
    qr_preview.short_description = 'QR Preview'


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'cafe', 
        'rating', 
        'is_positive', 
        'issue', 
        'comment_preview', 
        'customer_mobile_display', 
        'consent_display', 
        'formatted_date'
    )
    list_filter = ('rating', 'is_positive', 'issue', 'consent_to_contact')
    ordering = ('-created_at',)
    readonly_fields = ('formatted_date', 'is_positive')
    actions = ('regenerate_ai_replies',)

    @admin.action(description='Regenerate AI replies')
    def regenerate_ai_replies(self, request, queryset):
        from .services.ai_review_analysis import analyze_negative_feedback
        success_count = 0
        skipped_count = 0
        for feedback in queryset:
            if feedback.rating <= 3 and feedback.comment:
                try:
                    ai_data = analyze_negative_feedback(feedback)
                    feedback.ai_sentiment = ai_data.get('sentiment')
                    feedback.ai_emotion = ai_data.get('emotion')
                    feedback.ai_urgency = ai_data.get('urgency')
                    feedback.ai_reply_1 = ai_data.get('reply_1')
                    feedback.ai_reply_2 = ai_data.get('reply_2')
                    feedback.ai_reply_3 = ai_data.get('reply_3')
                    feedback.save()
                    success_count += 1
                except Exception as e:
                    self.message_user(request, f'Error generating replies for feedback #{feedback.id}: {e}', level='ERROR')
            else:
                skipped_count += 1
        self.message_user(request, f'Successfully regenerated AI replies for {success_count} feedback entries. (Skipped {skipped_count} positive or blank entries.)')

    fieldsets = (
        ('Feedback Details', {
            'fields': ('cafe', 'rating', 'is_positive', 'issue', 'comment', 'formatted_date')
        }),
        ('Customer Follow-up Contact', {
            'fields': ('customer_mobile', 'consent_to_contact'),
            'description': 'Optional contact info provided by the customer for personal follow-up.'
        }),
        ('AI Analysis & Replies', {
            'fields': ('ai_sentiment', 'ai_emotion', 'ai_urgency', 'ai_reply_1', 'ai_reply_2', 'ai_reply_3'),
            'description': 'AI generated sentiment analysis and response suggestions.'
        }),
    )

    def comment_preview(self, obj):
        if obj.comment:
            return obj.comment[:40] + '...' if len(obj.comment) > 40 else obj.comment
        return "-"
    comment_preview.short_description = 'Comment'

    def customer_mobile_display(self, obj):
        return obj.customer_mobile if obj.customer_mobile else "-"
    customer_mobile_display.short_description = 'Customer Mobile'

    def consent_display(self, obj):
        if obj.consent_to_contact:
            return format_html('<span style="color: #10b981; font-weight: bold;">✔ Consented</span>')
        return format_html('<span style="color: #9ca3af;">-</span>')
    consent_display.short_description = 'Contact Consent'
    
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
