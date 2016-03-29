# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slowish', '0002_add_container'),
    ]

    operations = [
        migrations.CreateModel(
            name='SlowishFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', models.CharField(help_text=b'Complete path of this file (within the container).', max_length=1024)),
                ('container', models.ForeignKey(to='slowish.SlowishContainer')),
            ],
            options={
                'verbose_name': 'Slowish File',
                'verbose_name_plural': 'Slowish Files',
            },
        ),
        migrations.AlterUniqueTogether(
            name='slowishfile',
            unique_together=set([('container', 'path')]),
        ),
    ]
