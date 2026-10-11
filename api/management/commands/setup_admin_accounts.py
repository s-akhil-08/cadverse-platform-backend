from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from api.models import EmployeeProfile

User = get_user_model()


class Command(BaseCommand):
    help = "Creates or resets the Master Admin (Full Write Access) and Demo Admin (Strictly Read-Only) accounts."

    def add_arguments(self, parser):
        parser.add_argument('--master-email', default='master_admin@cadverse.com', help='Email for Master Superuser')
        parser.add_argument('--master-password', default='MasterAdmin@2026', help='Password for Master Superuser')
        parser.add_argument('--demo-email', default='demo_admin@cadverse.com', help='Email for Demo Admin (Read-Only)')
        parser.add_argument('--demo-password', default='DemoAdmin@123', help='Password for Demo Admin (Read-Only)')

    def handle(self, *args, **options):
        master_email = options['master_email'].lower().strip()
        master_password = options['master_password']
        demo_email = options['demo_email'].lower().strip()
        demo_password = options['demo_password']

        # 1. Setup Master Superuser (Full Write/Delete Access)
        master_user, created = User.objects.get_or_create(
            email=master_email,
            defaults={
                'name': 'Master Administrator',
                'mobile': '+10000000000',
                'is_staff': True,
                'is_superuser': True,
                'is_verified': True,
                'is_active': True,
            }
        )
        master_user.set_password(master_password)
        master_user.is_staff = True
        master_user.is_superuser = True
        master_user.is_verified = True
        master_user.is_active = True
        master_user.save()

        action_text = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"[OK] {action_text} Master Superuser: {master_email} (Full Access)"))

        # 2. Setup Demo Admin (Strict Read-Only)
        demo_user, d_created = User.objects.get_or_create(
            email=demo_email,
            defaults={
                'name': 'Public Demo Admin',
                'mobile': '+10000000001',
                'is_staff': True,
                'is_superuser': False,
                'is_verified': True,
                'is_active': True,
            }
        )
        demo_user.set_password(demo_password)
        demo_user.is_staff = True
        demo_user.is_superuser = False
        demo_user.is_verified = True
        demo_user.is_active = True
        demo_user.save()

        # Connect all model content types to demo user's EmployeeProfile so they can view all panels
        profile, _ = EmployeeProfile.objects.get_or_create(user=demo_user)
        api_content_types = ContentType.objects.filter(app_label='api')
        profile.visible_models.set(api_content_types)

        d_action_text = "Created" if d_created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"[OK] {d_action_text} Demo Admin: {demo_email} (Strictly Read-Only)"))
        self.stdout.write(self.style.SUCCESS("All admin roles and permissions are successfully configured!"))
