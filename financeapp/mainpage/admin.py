from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'full_name', 'is_admin', 'is_superuser', 'is_active')
    list_filter = ('is_admin', 'is_superuser', 'is_active')  # ✅ fixed here
    search_fields = ('username', 'email')
    ordering = ('username',)
    fieldsets = (
        (None, {'fields': ('username', 'email', 'full_name', 'password')}),
        ('Permissions', {
            'fields': ('is_admin', 'is_superuser', 'is_active', 'groups', 'user_permissions')
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'full_name', 'password1', 'password2'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)