from django.utils import timezone
from django.db import models
from django.conf import settings   
from .managers import SoftDeleteManager


# TimeStampedModel for common timestamp fields
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


# SoftDeletableModel for soft deletion functionality
class SoftDeletableModel(TimeStampedModel):
    objects = SoftDeleteManager()   # excludes deleted
    all_objects = models.Manager()  # includes deleted

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        self.deleted_at = timezone.now()

        if user:
            self.deleted_by = user  

        self.save()