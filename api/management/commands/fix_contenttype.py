# api/management/commands/fix_contenttype.py

from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Correct way to remove the 'name' field from Django's model cache
        ContentType._meta._expire_cache()
        
        # Force rebuild fields without 'name'
        fields = []
        for field in ContentType._meta.local_fields:
            if field.name != 'name':
                fields.append(field)
        ContentType._meta.local_fields = fields
        
        # Rebuild virtual fields too
        ContentType._meta._field_cache = None
        ContentType._meta._field_name_cache = None
        
        self.stdout.write(self.style.SUCCESS("ContentType model fixed — 'name' field removed from cache"))