# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slowish', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SlowishContainer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'A name for this container.', max_length=255)),
                ('account', models.ForeignKey(to='slowish.SlowishAccount')),
            ],
            options={
                'verbose_name': 'Slowish Container',
                'verbose_name_plural': 'Slowish Containers',
            },
        ),
        migrations.AlterUniqueTogether(
            name='slowishcontainer',
            unique_together=set([('account', 'name')]),
        ),
    ]
