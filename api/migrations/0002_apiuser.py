from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
        ("authtoken", "0004_alter_tokenproxy_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="APIUser",
            fields=[],
            options={
                "verbose_name": "API User",
                "verbose_name_plural": "API Users",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("authtoken.token",),
        ),
    ]
