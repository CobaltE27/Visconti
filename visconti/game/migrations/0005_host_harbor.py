# Generated by Django 5.1.4 on 2025-06-25 05:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0004_player_ai'),
    ]

    operations = [
        migrations.AddField(
            model_name='host',
            name='harbor',
            field=models.CharField(default='', max_length=500),
        ),
    ]
