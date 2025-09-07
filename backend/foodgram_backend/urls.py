from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path


def test_shortlink_view(request, short_code):
    return HttpResponse(f'SHORTLINK TEST OK — {short_code}', status=200)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<str:short_code>/', test_shortlink_view),
]
