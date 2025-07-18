# Generated by Django 5.2 on 2025-05-06 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='item',
            name='length',
        ),
        migrations.AddField(
            model_name='item',
            name='depth',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Depth dimension (optional).', max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='dimension_unit',
            field=models.CharField(choices=[('CM', 'Centimeters'), ('IN', 'Inches')], default='CM', help_text='Units for the dimensions provided (Depth x Width x Height).', max_length=2),
        ),
        migrations.AlterField(
            model_name='item',
            name='height',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Height dimension (optional).', max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='width',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Width dimension (optional).', max_digits=10, null=True),
        ),
    ]
