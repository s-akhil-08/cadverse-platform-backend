# from django.core.management.base import BaseCommand
# from django.utils.timezone import now, timedelta
# from api.models import TempUser

# class Command(BaseCommand):
#     help = 'Cleans up temporary user records older than 24 hours'

#     def handle(self, *args, **kwargs):
#         threshold = now() - timedelta(hours=24)
#         old_temp_users = TempUser.objects.filter(created_at__lt=threshold)
#         count = old_temp_users.count()
#         old_temp_users.delete()
#         self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} old temporary user records.'))




from django.core.management.base import BaseCommand
from django.utils.timezone import now, timedelta
from api.models import TempUser

class Command(BaseCommand):
    help = 'Cleans up temporary user records older than 24 hours'

    def handle(self, *args, **kwargs):
        threshold = now() - timedelta(hours=24)
        old_temp_users = TempUser.objects.filter(created_at__lt=threshold)
        count = old_temp_users.count()
        old_temp_users.delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} old temporary user records.'))