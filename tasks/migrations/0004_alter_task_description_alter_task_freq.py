# Generated by Django 4.2.1 on 2023-05-26 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_alter_task_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='description',
            field=models.TextField(blank=True, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='freq',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
