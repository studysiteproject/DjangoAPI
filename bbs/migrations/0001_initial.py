# Generated by Django 3.2.6 on 2021-09-08 10:21

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Board',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=126, verbose_name='제목')),
                ('content', models.TextField(verbose_name='내용')),
                ('author', models.CharField(max_length=16, verbose_name='작성자')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='작성일')),
            ],
        ),
    ]
