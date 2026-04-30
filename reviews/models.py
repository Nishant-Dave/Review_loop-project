from django.db import models

class Cafe(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    google_review_link = models.URLField()
    logo = models.ImageField(upload_to='cafe_logos/', null=True, blank=True)


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
