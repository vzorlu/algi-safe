from rest_framework import serializers
from .models import StreamImage, Detection, Notification, NotificationType, VideoUpload, ClassData, RulesAdd


class DetectionSerializer(serializers.ModelSerializer):
    # Add a speech field that doesn't come from the model
    speech = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Detection
        fields = ["id", "image", "class_name", "x_min", "y_min", "x_max", "y_max", "speech", "confidence", "timestamp"]

    def get_speech(self, obj):
        """Get speech content for this detection's class from CLASS_SPEECH_LOOKUP"""
        from .views import CLASS_SPEECH_LOOKUP

        # For standard model detections, we need to remove the "std_" prefix
        class_name = obj.class_name
        if class_name.startswith("std_"):
            class_name = class_name[4:]  # Remove "std_" prefix for lookup

        return CLASS_SPEECH_LOOKUP.get(class_name, "")


class StreamImageSerializer(serializers.ModelSerializer):
    detections = DetectionSerializer(many=True, read_only=True)
    detection_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = StreamImage
        fields = [
            "id",
            "image",
            "timestamp",
            "processed",
            "lang",
            "long",
            "fulladdress",
            "area",
            "speech",
            "deviceuuid",
            "detections",
            "detection_count",
        ]


class NotificationSerializer(serializers.ModelSerializer):
    notification_type = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=NotificationType.objects.filter(is_active=True),
        error_messages={
            "required": "En az bir bildirim türü seçmelisiniz.",
            "empty": "En az bir bildirim türü seçmelisiniz.",
            "invalid": "Geçersiz bildirim türü seçimi.",
        },
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "detection_id",
            "class_name",
            "rule_name",
            "message",
            "department",
            "severity",
            "notification_type",
            "frequency",
            "send_time",
        ]

    def validate(self, data):
        if not data.get("notification_type"):
            raise serializers.ValidationError({"notification_type": "En az bir bildirim türü seçmelisiniz."})
        if data.get("frequency") != "immediate" and not data.get("send_time"):
            raise serializers.ValidationError({"send_time": "Send time is required for non-immediate notifications"})
        return data


class VideoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoUpload
        fields = ["id", "video", "json_file", "device_id", "timestamp"]


class ClassDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassData
        fields = ["id", "Name", "Turkish", "Speech"]


class RulesAddSerializer(serializers.ModelSerializer):
    detection_id = serializers.IntegerField(write_only=True)
    notification_types = serializers.PrimaryKeyRelatedField(
        many=True, queryset=NotificationType.objects.all(), required=False
    )

    class Meta:
        model = RulesAdd
        fields = [
            "id",
            "detection_id",
            "class_name",
            "rule_name",
            "rule_scope",
            "department",
            "create_task",
            "task_type",
            "task_description",
            "task_due_date",
            "create_notification",
            "notification_types",
            "message",
            "frequency",
            "send_time",
        ]

    def create(self, validated_data):
        detection_id = validated_data.pop("detection_id")
        notification_types = validated_data.pop("notification_types", [])

        try:
            detection = Detection.objects.get(id=detection_id)
        except Detection.DoesNotExist:
            raise serializers.ValidationError({"detection_id": "Detection not found"})

        rule = RulesAdd.objects.create(detection=detection, **validated_data)

        if notification_types:
            rule.notification_types.set(notification_types)

        return rule

    def validate(self, data):
        if data.get("create_task"):
            if not data.get("task_type"):
                raise serializers.ValidationError({"task_type": "Task type is required when create_task is True"})
            if not data.get("task_description"):
                raise serializers.ValidationError(
                    {"task_description": "Task description is required when create_task is True"}
                )
            if not data.get("task_due_date"):
                raise serializers.ValidationError(
                    {"task_due_date": "Task due date is required when create_task is True"}
                )

        if data.get("create_notification"):
            if not data.get("notification_types"):
                raise serializers.ValidationError(
                    {
                        "notification_types": "At least one notification type is required when create_notification is True"
                    }
                )
            if not data.get("message"):
                raise serializers.ValidationError({"message": "Message is required when create_notification is True"})

        return data
