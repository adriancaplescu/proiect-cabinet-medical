from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cont/', include('django.contrib.auth.urls')),  # login, logout
    path('', include('cabinet.urls')),
]
