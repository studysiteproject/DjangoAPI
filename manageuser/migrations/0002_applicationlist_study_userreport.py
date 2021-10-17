# Generated by Django 3.2.6 on 2021-10-17 11:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manageuser', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Applicationlist',
            fields=[
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='user', serialize=False, to='manageuser.user')),
                ('permission', models.IntegerField(blank=True, null=True)),
                ('create_date', models.DateTimeField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'db_table': 'applicationlist',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Study',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=50)),
                ('maxman', models.IntegerField()),
                ('nowman', models.IntegerField(default=1, null=True)),
                ('create_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('description', models.TextField()),
                ('place', models.TextField()),
                ('warn_cnt', models.IntegerField(default=0, null=True)),
            ],
            options={
                'db_table': 'study',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='UserReport',
            fields=[
                ('reporter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='reporter', serialize=False, to='manageuser.user')),
                ('description', models.TextField()),
                ('create_date', models.DateTimeField(auto_now_add=True, null=True)),
            ],
            options={
                'db_table': 'user_report',
                'managed': False,
            },
        ),
    ]
