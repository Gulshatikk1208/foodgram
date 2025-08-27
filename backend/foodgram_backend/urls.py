from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<int:pk>/', RedirectView.as_view(
        url='https://foodgram-app.duckdns.org/recipes/%(pk)s/',
        permanent=True
    ), name='recipe-short-link'),
]
