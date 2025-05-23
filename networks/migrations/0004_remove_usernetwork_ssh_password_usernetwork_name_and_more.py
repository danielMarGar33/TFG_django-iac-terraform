# Generated by Django 5.1.6 on 2025-03-24 19:17

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0003_usernetwork_ssh_password'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usernetwork',
            name='ssh_password',
        ),
        migrations.AddField(
            model_name='usernetwork',
            name='name',
            field=models.CharField(default=django.utils.timezone.now, max_length=50),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='usernetwork',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='networks', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='SSH_password',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ssh_password', models.CharField(blank=True, max_length=50)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ssh_passwords', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
