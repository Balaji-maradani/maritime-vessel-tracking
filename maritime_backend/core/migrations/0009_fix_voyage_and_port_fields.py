# Fix missing fields in Voyage and Port models

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_add_vessel_position_and_audit_models'),
    ]

    operations = [
        # Add missing fields to Voyage model
        migrations.AddField(
            model_name='voyage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='Created At'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='voyage',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated At'),
        ),
        
        # Remove duplicate last_update field from Port model (keep last_updated)
        migrations.RemoveField(
            model_name='port',
            name='last_update',
        ),
    ]