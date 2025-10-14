from django.db import models
from .role import Role


class Permission(models.Model):
    module = models.CharField(max_length=100)
    action = models.CharField(max_length=20, choices=[
        ('view', 'View Only'),
        ('edit', 'Edit Access'),
    ])
    resource_type = models.CharField(max_length=100, blank=True)
    roles = models.ManyToManyField(Role, related_name='permissions', blank=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'auth_permissions'
        unique_together = ['module', 'action', 'resource_type']

    def __str__(self) -> str:
        return f"{self.module}:{self.action}:{self.resource_type or '*'}"


