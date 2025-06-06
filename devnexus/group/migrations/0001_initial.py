# Generated by Django 5.1.3 on 2025-04-26 14:31

import django.db.models.deletion
import shortuuid.main
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('group_uuid', models.CharField(default=shortuuid.main.ShortUUID.uuid, max_length=128, unique=True)),
                ('icon', models.ImageField(blank=True, upload_to='group_icons/')),
                ('description', models.TextField(blank=True, max_length=200)),
                ('admin', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('members', models.ManyToManyField(related_name='group_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Группы',
                'verbose_name_plural': 'Группы',
                'db_table': 'group',
            },
        ),
        migrations.CreateModel(
            name='ColumnBoard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('color', models.CharField(max_length=20)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='columns', to='group.group', to_field='group_uuid')),
            ],
        ),
        migrations.CreateModel(
            name='CardTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(editable=False, max_length=6)),
                ('name', models.CharField(max_length=50)),
                ('color', models.CharField(max_length=20)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='available_card_tags', to='group.group', to_field='group_uuid')),
            ],
        ),
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(editable=False, max_length=6, unique=True)),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, max_length=700)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('start_date', models.DateTimeField(blank=True, null=True)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('assignee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('tags', models.ManyToManyField(related_name='card_tags', to='group.cardtag')),
                ('column', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cards', to='group.columnboard')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='group.group')),
            ],
            options={
                'verbose_name': 'Карточка',
                'verbose_name_plural': 'Карточки',
                'db_table': 'card',
            },
        ),
        migrations.CreateModel(
            name='GroupTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(editable=False, max_length=6)),
                ('name', models.CharField(max_length=50)),
                ('color', models.CharField(max_length=20)),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='available_tags', to='group.group', to_field='group_uuid')),
            ],
        ),
        migrations.CreateModel(
            name='UserTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='group.grouptag')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='columnboard',
            constraint=models.UniqueConstraint(fields=('name', 'group'), name='unique_column_name_per_group'),
        ),
        migrations.AlterUniqueTogether(
            name='cardtag',
            unique_together={('name', 'color', 'group')},
        ),
        migrations.AlterUniqueTogether(
            name='grouptag',
            unique_together={('name', 'color', 'group')},
        ),
        migrations.AlterUniqueTogether(
            name='usertag',
            unique_together={('user', 'tag')},
        ),
    ]
