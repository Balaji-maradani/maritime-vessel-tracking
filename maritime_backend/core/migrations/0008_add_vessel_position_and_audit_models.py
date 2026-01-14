# Generated manually for voyage history and replay support

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_add_vessel_subscription_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='VesselPosition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.FloatField(help_text='Position latitude in decimal degrees', verbose_name='Latitude')),
                ('longitude', models.FloatField(help_text='Position longitude in decimal degrees', verbose_name='Longitude')),
                ('speed', models.FloatField(blank=True, help_text='Speed in knots', null=True, verbose_name='Speed')),
                ('heading', models.IntegerField(blank=True, help_text='Heading in degrees (0-359)', null=True, verbose_name='Heading')),
                ('timestamp', models.DateTimeField(db_index=True, help_text='When this position was recorded', verbose_name='Position Timestamp')),
                ('source', models.CharField(default='AIS', help_text='Source of position data (AIS, GPS, Manual, etc.)', max_length=50, verbose_name='Data Source')),
                ('accuracy', models.FloatField(blank=True, help_text='Position accuracy in meters', null=True, verbose_name='Position Accuracy')),
                ('is_interpolated', models.BooleanField(default=False, help_text='Whether this position was interpolated between actual readings', verbose_name='Is Interpolated')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('vessel', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='positions', to='core.vessel', verbose_name='Vessel')),
                ('voyage', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='positions', to='core.voyage', verbose_name='Voyage')),
            ],
            options={
                'verbose_name': 'Vessel Position',
                'verbose_name_plural': 'Vessel Positions',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='VoyageAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('VOYAGE_CREATED', 'Voyage Created'), ('VOYAGE_UPDATED', 'Voyage Updated'), ('VOYAGE_COMPLETED', 'Voyage Completed'), ('VOYAGE_CANCELLED', 'Voyage Cancelled'), ('POSITION_RECORDED', 'Position Recorded'), ('POSITION_UPDATED', 'Position Updated'), ('ROUTE_ACCESSED', 'Route Data Accessed'), ('REPLAY_STARTED', 'Voyage Replay Started'), ('REPLAY_COMPLETED', 'Voyage Replay Completed'), ('DATA_EXPORTED', 'Data Exported'), ('COMPLIANCE_CHECK', 'Compliance Check Performed'), ('ALERT_TRIGGERED', 'Alert Triggered'), ('USER_ACCESS', 'User Data Access'), ('SYSTEM_UPDATE', 'System Update'), ('DATA_RETENTION', 'Data Retention Action')], db_index=True, max_length=50, verbose_name='Action')),
                ('description', models.TextField(help_text='Detailed description of the action performed', verbose_name='Description')),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address of the user or system performing the action', null=True, verbose_name='IP Address')),
                ('user_agent', models.TextField(blank=True, help_text='User agent string for web requests', null=True, verbose_name='User Agent')),
                ('metadata', models.JSONField(default=dict, help_text='Additional metadata about the action', verbose_name='Metadata')),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Timestamp')),
                ('compliance_category', models.CharField(blank=True, help_text='Regulatory compliance category (SOLAS, MARPOL, etc.)', max_length=100, null=True, verbose_name='Compliance Category')),
                ('retention_date', models.DateTimeField(blank=True, help_text='Date when this log entry should be archived/deleted', null=True, verbose_name='Retention Date')),
                ('user', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL, verbose_name='User')),
                ('vessel', models.ForeignKey(db_index=True, on_delete=django.db.models.deletion.CASCADE, related_name='audit_logs', to='core.vessel', verbose_name='Vessel')),
                ('voyage', models.ForeignKey(blank=True, db_index=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='audit_logs', to='core.voyage', verbose_name='Voyage')),
            ],
            options={
                'verbose_name': 'Voyage Audit Log',
                'verbose_name_plural': 'Voyage Audit Logs',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='vesselposition',
            index=models.Index(fields=['vessel', 'timestamp'], name='core_vesselp_vessel__b8e8a5_idx'),
        ),
        migrations.AddIndex(
            model_name='vesselposition',
            index=models.Index(fields=['voyage', 'timestamp'], name='core_vesselp_voyage__c8f9b6_idx'),
        ),
        migrations.AddIndex(
            model_name='vesselposition',
            index=models.Index(fields=['timestamp'], name='core_vesselp_timesta_d7a2c3_idx'),
        ),
        migrations.AddIndex(
            model_name='vesselposition',
            index=models.Index(fields=['vessel', 'voyage'], name='core_vesselp_vessel__e9f0d4_idx'),
        ),
        migrations.AddIndex(
            model_name='voyageauditlog',
            index=models.Index(fields=['vessel', 'timestamp'], name='core_voyage_vessel__a1b2c3_idx'),
        ),
        migrations.AddIndex(
            model_name='voyageauditlog',
            index=models.Index(fields=['voyage', 'timestamp'], name='core_voyage_voyage__d4e5f6_idx'),
        ),
        migrations.AddIndex(
            model_name='voyageauditlog',
            index=models.Index(fields=['user', 'timestamp'], name='core_voyage_user_id_g7h8i9_idx'),
        ),
        migrations.AddIndex(
            model_name='voyageauditlog',
            index=models.Index(fields=['action', 'timestamp'], name='core_voyage_action_j0k1l2_idx'),
        ),
        migrations.AddIndex(
            model_name='voyageauditlog',
            index=models.Index(fields=['compliance_category', 'timestamp'], name='core_voyage_complia_m3n4o5_idx'),
        ),
        migrations.AddIndex(
            model_name='voyageauditlog',
            index=models.Index(fields=['retention_date'], name='core_voyage_retenti_p6q7r8_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='vesselposition',
            unique_together={('vessel', 'timestamp')},
        ),
    ]