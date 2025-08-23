from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'api'

router = DefaultRouter()
router.register('users', views.MyUserViewSet, basename='users')
router.register('tags', views.TagViewSet, basename='tags')
router.register('recipes', views.RecipeViewSet, basename='recipes')
router.register('ingredients', views.IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),
    path('s/<int:pk>/', RedirectView.as_view(
        pattern_name='recipe-detail'
    ), name='recipe-short-link'),
    path('auth/', include('djoser.urls.authtoken')),
]
