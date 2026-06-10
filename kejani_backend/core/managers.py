from django.db import models



class SoftDeletableModel(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)



        
