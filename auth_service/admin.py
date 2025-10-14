from django.contrib import admin
from .models import KeycloakUser, Role, Permission, Group, GroupRole, AuthAuditLog


@admin.register(KeycloakUser)
class KeycloakUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'user_type', 'is_active')
    search_fields = ('username', 'email')


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'keycloak_role_id', 'is_system_role')
    search_fields = ('name', 'keycloak_role_id')


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('module', 'action', 'resource_type')
    list_filter = ('module', 'action')


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(GroupRole)
class GroupRoleAdmin(admin.ModelAdmin):
    list_display = ('group', 'role')
    list_filter = ('group', 'role')


@admin.register(AuthAuditLog)
class AuthAuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'success', 'timestamp')
    list_filter = ('event_type', 'success')
    search_fields = ('resource',)


