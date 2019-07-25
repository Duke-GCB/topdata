from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

urlpatterns = [
    path('tracks/', include('tracks.urls')),
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='tracks-index', permanent=False))
]
