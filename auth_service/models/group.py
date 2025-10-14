from django.db import models
from .role import Role
from .user import KeycloakUser


class Group(models.Model):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    members = models.ManyToManyField(KeycloakUser, related_name='groups', blank=True)

    class Meta:
        db_table = 'auth_groups'

    def __str__(self) -> str:
        return self.name


class GroupRole(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

    class Meta:
        db_table = 'auth_group_roles'
        unique_together = ['group', 'role']

    def __str__(self) -> str:
        return f"{self.group.name}:{self.role.name}"


