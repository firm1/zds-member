# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('member', '0002_auto_20150601_1144'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profile',
            options={'verbose_name': 'Profil', 'verbose_name_plural': 'Profils', 'permissions': (('moderation', 'Moderate membre'), ('show_ip', "Show member's Ip Adress"))},
        ),
        migrations.RemoveField(
            model_name='profile',
            name='sdz_tutorial',
        ),
        migrations.AlterField(
            model_name='profile',
            name='avatar_url',
            field=models.CharField(max_length=2000, null=True, verbose_name=b'Avatar url', blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='biography',
            field=models.TextField(verbose_name=b'Biography', blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='hover_or_click',
            field=models.BooleanField(default=False, verbose_name=b'Hover or clic ?'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='last_ip_address',
            field=models.CharField(max_length=39, null=True, verbose_name=b'IP Adress', blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='show_email',
            field=models.BooleanField(default=False, verbose_name=b'Show email adress on public'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='show_sign',
            field=models.BooleanField(default=True, verbose_name=b'Show signs'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='sign',
            field=models.TextField(max_length=250, verbose_name=b'Sign', blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='site',
            field=models.CharField(max_length=2000, verbose_name=b'Web site', blank=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(related_name='profile', verbose_name=b'User', to=settings.AUTH_USER_MODEL),
        ),
    ]
