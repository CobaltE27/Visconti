# Generated by Django 5.1.4 on 2025-05-21 22:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='ready',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='host',
            name='log',
            field=models.TextField(default='<span><strong>Match opened.</strong></span>'),
        ),
    ]
