from django.db import models
from .user import KeycloakUser


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    keycloak_role_id = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    is_system_role = models.BooleanField(default=False)
    users = models.ManyToManyField(KeycloakUser, related_name='roles', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auth_roles'

    def __str__(self) -> str:
        return self.name


