from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

# from api.views import redirect_to_recipe


def test_view(request):
    print("TEST VIEW CALLED!")
    return HttpResponse("Test works!")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('test-simple/', test_view),
    # path('s/<int:pk>/', redirect_to_recipe, name='recipe-short-link'),
]
