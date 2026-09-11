"""URL configuration for the core project."""
 
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
 
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.api.urls')),
    path('api/termine/', include('termine.api.urls')),
    path('api/forum/', include('forum.api.urls')),
]
 
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
 