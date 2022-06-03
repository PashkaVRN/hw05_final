from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


handler404 = 'core.views.page_not_found'
handler403 = 'core.views.permission_denied'
handler500 = 'core.views.server_error'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('auth/', include('django.contrib.auth.urls')),
    path('', include('posts.urls', namespace='posts')),
    path('about/', include('about.urls', namespace='about')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
