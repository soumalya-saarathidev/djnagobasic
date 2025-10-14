from django.db import models
from .user import KeycloakUser


class AuthAuditLog(models.Model):
    user = models.ForeignKey(KeycloakUser, on_delete=models.SET_NULL, null=True)
    event_type = models.CharField(max_length=50)
    resource = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=True)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auth_audit_logs'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['event_type']),
        ]


