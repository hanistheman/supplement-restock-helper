from django.db import models

class User(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    hashed_password = models.CharField(max_length=255)
    notifications_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "users"

    @property
    def is_authenticated(self):
        return True

class RefreshToken(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="refresh_tokens")
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = "refresh_tokens"

class Supplement(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="supplements")
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    total_doses = models.PositiveIntegerField()
    dose_amount = models.FloatField(default=1)
    frequency_count = models.FloatField(default=1)
    frequency_unit = models.CharField(max_length=10, default="day")
    notes = models.TextField(null=True, blank=True)
    class Meta:
        db_table = "supplements"

class Source(models.Model):
    id = models.AutoField(primary_key=True)
    supplement = models.ForeignKey(Supplement, on_delete=models.CASCADE, related_name="sources")
    name = models.CharField(max_length=100)
    url = models.URLField(null=True, blank=True)
    class Meta:
        db_table = "sources"

class SkippedDay(models.Model):
    supplement = models.ForeignKey(Supplement, on_delete=models.CASCADE, related_name="skipped_days")
    date = models.DateField()

    class Meta:
        db_table = "skipped_days"
        ordering = ["date", "id"]
        constraints = [models.UniqueConstraint(fields=["supplement", "date"], name="uq_skipped_day_supplement_date")]
