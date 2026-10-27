from rest_framework import serializers

from .models import SkippedDay, Source, Supplement, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "notifications_enabled", "created_at"]


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(min_length=8, max_length=72, write_only=True, trim_whitespace=False)


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ["id", "name", "url"]


class SkippedDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = SkippedDay
        fields = ["id", "date"]
        read_only_fields = ["id"]


class SupplementSerializer(serializers.ModelSerializer):
    sources = SourceSerializer(many=True, required=False)
    skipped_days = SkippedDaySerializer(many=True, read_only=True)
    days_remaining = serializers.SerializerMethodField()
    restock_date = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Supplement
        fields = ["id", "name", "start_date", "total_doses", "dose_amount", "frequency_count",
                  "frequency_unit", "notes", "days_remaining", "restock_date", "status", "sources", "skipped_days"]
        read_only_fields = ["id", "days_remaining", "restock_date", "status", "skipped_days"]

    def validate_frequency_unit(self, value):
        if value not in {"day", "week", "month", "year"}:
            raise serializers.ValidationError("Invalid frequency_unit")
        return value

    def validate(self, attrs):
        if attrs.get("total_doses", 1) <= 0:
            raise serializers.ValidationError({"total_doses": "Must be greater than 0."})
        for field in ("dose_amount", "frequency_count"):
            if attrs.get(field, 1) <= 0:
                raise serializers.ValidationError({field: "Must be greater than 0."})
        return attrs

    def update(self, instance, validated_data):
        validated_data.pop("sources", None)
        return super().update(instance, validated_data)

    def create(self, validated_data):
        sources = validated_data.pop("sources", [])
        supplement = Supplement.objects.create(user=self.context["request"].user, **validated_data)
        Source.objects.bulk_create([Source(supplement=supplement, **source) for source in sources])
        return supplement

    def get_days_remaining(self, obj):
        from logic import DAYS_PER_UNIT, days_remaining, doses_per_day_from_frequency
        per_day = doses_per_day_from_frequency(obj.dose_amount, obj.frequency_count, obj.frequency_unit)
        skipped = obj.skipped_days.filter(date__gte=obj.start_date).count()
        return days_remaining(obj.start_date, obj.total_doses, per_day) + round(skipped * DAYS_PER_UNIT[obj.frequency_unit] / obj.frequency_count)

    def get_restock_date(self, obj):
        from datetime import timedelta
        from logic import DAYS_PER_UNIT, doses_per_day_from_frequency, restock_date
        per_day = doses_per_day_from_frequency(obj.dose_amount, obj.frequency_count, obj.frequency_unit)
        skipped = obj.skipped_days.filter(date__gte=obj.start_date).count()
        adjustment = round(skipped * DAYS_PER_UNIT[obj.frequency_unit] / obj.frequency_count)
        return restock_date(obj.start_date, obj.total_doses, per_day) + timedelta(days=adjustment)

    def get_status(self, obj):
        from logic import status_for
        return status_for(self.get_days_remaining(obj))
