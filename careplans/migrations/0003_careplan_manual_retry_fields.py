from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("careplans", "0002_provider_patient_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="careplan",
            name="manual_retry_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="careplan",
            name="last_manual_retry_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
