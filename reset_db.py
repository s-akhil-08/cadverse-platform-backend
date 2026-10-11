import os
import django
from django.db import connection

print("🔄 Starting DB reset script...")

# Since settings.py is in myproject/
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

try:
    print("⚙️ Setting up Django...")
    django.setup()
    print("✅ Django setup complete.")

    with connection.cursor() as cursor:
        print("🚨 Dropping schema...")
        cursor.execute("DROP SCHEMA public CASCADE;")
        print("🛠 Creating schema...")
        cursor.execute("CREATE SCHEMA public;")
        print("✅ Database schema reset successfully.")
except Exception as e:
    print("❌ Error during DB reset:", e)
