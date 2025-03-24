from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import logging

from council.models import Department

User = get_user_model()

logger = logging.getLogger(__name__)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)  # Changed required to False
    full_name = serializers.CharField(required=False)
    department_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "full_name", "department_id")
        extra_kwargs = {
            "username": {"required": False},  # Make username optional for updates
            "email": {"required": False},  # Make email optional for updates
        }

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Bu kullanıcı adı zaten kullanılıyor.")
        return value

    def validate_email(self, value):
        # Only validate email uniqueness if it changed
        instance = getattr(self, "instance", None)
        if instance and instance.email == value:
            return value
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email adresi zaten kullanılıyor.")
        return value

    def create(self, validated_data):
        full_name = validated_data.pop("full_name", "")
        department_id = validated_data.pop("department_id", None)

        user = User.objects.create_user(**validated_data)

        if full_name:
            names = full_name.split(" ", 1)
            user.first_name = names[0]
            user.last_name = names[1] if len(names) > 1 else ""

        if department_id:
            user.department_id = department_id

        user.save()
        return user

    def update(self, instance, validated_data):
        logger.info(f"Update called with data: {validated_data}")

        if "full_name" in validated_data:
            full_name = validated_data.pop("full_name")
            names = full_name.split(" ", 1)
            instance.first_name = names[0]
            instance.last_name = names[1] if len(names) > 1 else ""
            logger.info(f"Updated full name: {instance.first_name} {instance.last_name}")

        if "department_id" in validated_data:
            department_id = validated_data.pop("department_id")
            logger.info(f"Updating department_id to: {department_id}")
            if department_id:
                try:
                    department = Department.objects.get(id=department_id)
                    instance.department = department
                    logger.info(f"Found department: {department.name}")
                except Department.DoesNotExist:
                    logger.error(f"Department with id {department_id} not found")
                    raise serializers.ValidationError({"department_id": "Geçersiz departman ID"})
            else:
                instance.department = None
                logger.info("Department set to None")

        result = super().update(instance, validated_data)
        instance.save()  # Make sure to save the instance
        logger.info(f"Final user state - department: {instance.department}")
        return result
