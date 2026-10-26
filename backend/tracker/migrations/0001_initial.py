from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name="User", fields=[
            ("id", models.AutoField(primary_key=True, serialize=False)),
            ("email", models.EmailField(max_length=254, unique=True)),
            ("hashed_password", models.CharField(max_length=255)),
            ("notifications_enabled", models.BooleanField(default=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
        ], options={"db_table": "users"}),
        migrations.CreateModel(name="Supplement", fields=[
            ("id", models.AutoField(primary_key=True, serialize=False)),
            ("name", models.CharField(max_length=100)), ("start_date", models.DateField()),
            ("total_doses", models.PositiveIntegerField()), ("dose_amount", models.FloatField(default=1)),
            ("frequency_count", models.FloatField(default=1)), ("frequency_unit", models.CharField(default="day", max_length=10)),
            ("notes", models.TextField(blank=True, null=True)),
            ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="supplements", to="tracker.user")),
        ], options={"db_table": "supplements"}),
        migrations.CreateModel(name="RefreshToken", fields=[
            ("id", models.AutoField(primary_key=True, serialize=False)), ("token_hash", models.CharField(max_length=64, unique=True)),
            ("expires_at", models.DateTimeField()), ("revoked", models.BooleanField(default=False)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="refresh_tokens", to="tracker.user")),
        ], options={"db_table": "refresh_tokens"}),
        migrations.CreateModel(name="Source", fields=[
            ("id", models.AutoField(primary_key=True, serialize=False)), ("name", models.CharField(max_length=100)),
            ("url", models.URLField(blank=True, null=True)),
            ("supplement", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sources", to="tracker.supplement")),
        ], options={"db_table": "sources"}),
    ]
