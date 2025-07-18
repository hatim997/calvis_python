# Generated by Django 5.2 on 2025-05-04 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Client's full name or primary contact name if company.", max_length=200)),
                ('company_name', models.CharField(blank=True, help_text='Company name, if applicable.', max_length=200, null=True)),
                ('contact_person', models.CharField(blank=True, help_text='Specific contact person at the company (if different from name).', max_length=150, null=True)),
                ('email', models.EmailField(help_text='Primary email address for the client.', max_length=254, unique=True)),
                ('phone', models.CharField(help_text='Primary phone number for the client.', max_length=30)),
                ('address', models.TextField(blank=True, help_text='Billing or primary address for the client.', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['company_name', 'name'],
            },
        ),
    ]
