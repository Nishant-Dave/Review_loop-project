import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.db import models
from django.conf import settings

class Cafe(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    google_review_link = models.URLField()
    logo = models.ImageField(upload_to='cafe_logos/', null=True, blank=True)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True)


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if not self.qr_code:
            base_url = settings.SITE_BASE_URL.rstrip('/')
            url = f"{base_url}/cafe/{self.slug}/"
            img = qrcode.make(url)
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            
            file_name = f'qr_{self.slug}.png'
            self.qr_code.save(file_name, ContentFile(buffer.getvalue()), save=False)
            super().save(update_fields=['qr_code'])

    def __str__(self):
        return self.name

class Feedback(models.Model):
    cafe = models.ForeignKey(Cafe, on_delete=models.CASCADE)
    rating = models.IntegerField()
    is_positive = models.BooleanField(default=False)
    issue = models.CharField(max_length=255, null=True, blank=True)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.is_positive = self.rating >= 4
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Feedback for {self.cafe.name} - {self.rating} stars"
