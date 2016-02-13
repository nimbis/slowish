# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import slowish.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SlowishAccount',
            fields=[
                ('id', models.IntegerField(help_text=b"Also known as Account # within rackspace, eg. '123456'.", serialize=False, primary_key=True)),
            ],
            options={
                'verbose_name': 'Slowish Account',
                'verbose_name_plural': 'Slowish Accounts',
            },
        ),
        migrations.CreateModel(
            name='SlowishUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(help_text=b"A username, eg. 'first.last'.", max_length=255)),
                ('password', models.CharField(help_text=b'Password associated with this username.', max_length=255)),
                ('token', models.CharField(default=slowish.models.generate_token, help_text=b'Generated token to allow authorized uses of the API.', max_length=255)),
                ('account', models.ForeignKey(to='slowish.SlowishAccount')),
            ],
            options={
                'verbose_name': 'Slowish User',
                'verbose_name_plural': 'Slowish Users',
            },
        ),
        migrations.AlterUniqueTogether(
            name='slowishuser',
            unique_together=set([('account', 'username')]),
        ),
    ]
