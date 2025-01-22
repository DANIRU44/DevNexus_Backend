# Generated by Django 5.1.3 on 2025-01-22 13:00

import shortuuid.main
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group', '0009_alter_group_group_uuid'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name='usertag',
            old_name='user',
            new_name='username',
        ),
        migrations.AlterField(
            model_name='group',
            name='group_uuid',
            field=models.CharField(default=shortuuid.main.ShortUUID.uuid, max_length=128, unique=True),
        ),
        migrations.AlterUniqueTogether(
            name='usertag',
            unique_together={('username', 'tag')},
        ),
    ]
