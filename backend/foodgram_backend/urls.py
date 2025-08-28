from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import include, path

# from api.views import redirect_to_recipe


# Временная тестовая функция
def test_redirect_view(request, pk):
    print(f"TEST REDIRECT: pk={pk}")
    return HttpResponseRedirect('https://google.com')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('test-redirect/<int:pk>/', test_redirect_view)
    # path('s/<int:pk>/', redirect_to_recipe, name='recipe-short-link'),
]
