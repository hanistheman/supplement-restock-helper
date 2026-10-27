from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("tracker", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="SkippedDay",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                ("supplement", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="skipped_days", to="tracker.supplement")),
            ],
            options={"db_table": "skipped_days", "ordering": ["date", "id"]},
        ),
        migrations.AddConstraint(
            model_name="skippedday",
            constraint=models.UniqueConstraint(fields=("supplement", "date"), name="uq_skipped_day_supplement_date"),
        ),
    ]
