# Generated by Django 4.2.1 on 2023-05-26 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_alter_task_freq'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='description',
            field=models.TextField(default='', max_length=300),
        ),
    ]