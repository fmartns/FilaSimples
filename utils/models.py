from django.db import models
from accounts.models import User

class logs(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    log_type = models.CharField(max_length=100, null=True, blank=True)
    message = models.TextField()
    module = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    field = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100, null=True, blank=True)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.timestamp}: {self.message} - User: {self.user if self.user else 'Unknown'}"
