"""
URL configuration for feedback_loop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from reviews.views import cafe_view, thank_you_view, home_view, analytics_dashboard_view, download_qr_poster_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home_view'),
    path('cafe/<slug:slug>/', cafe_view, name='cafe_view'),
    path('cafe/<slug:slug>/download-qr-poster/', download_qr_poster_view, name='download_qr_poster'),
    path('thank-you/', thank_you_view, name='thank_you_view'),
    path('analytics/', analytics_dashboard_view, name='analytics_dashboard_view'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
