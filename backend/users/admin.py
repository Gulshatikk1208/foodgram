from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Follow

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name')
    search_fields = ('username', 'email')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительная информация', {'fields': ['avatar']}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide'),
            'fields': (
                'email',
                'username',
                'first_name',
                'last_name',
                'password1',
                'password2'
            )
        }),
    )


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')
