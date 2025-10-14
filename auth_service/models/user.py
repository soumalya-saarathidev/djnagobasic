from django.db import models


class KeycloakUser(models.Model):
    keycloak_id = models.UUIDField(unique=True, db_index=True)
    employee = models.OneToOneField('core.Employee', on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)
    user_type = models.CharField(max_length=20, choices=[
        ('internal', 'Internal Employee'),
        ('external', 'External User')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'auth_keycloak_users'
        indexes = [
            models.Index(fields=['keycloak_id']),
            models.Index(fields=['email']),
        ]

    def __str__(self) -> str:
        return self.username


