from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.formats import base_formats
from .models import Detection, StreamImage, Notification, NotificationType, ClassData, OfflineMode, OfflineVideoLocation
from .forms import OfflineModeForm


class NotificationResource(resources.ModelResource):
    class Meta:
        model = Notification
        fields = (
            "id",
            "detection",
            "class_name",
            "rule_name",
            "message",
            "department",
            "severity",
            "frequency",
            "send_time",
            "created_at",
        )


class DetectionResource(resources.ModelResource):
    class Meta:
        model = Detection
        fields = ("id", "image", "class_name", "x_min", "y_min", "x_max", "y_max", "confidence", "timestamp")
        export_order = fields


class StreamImageResource(resources.ModelResource):
    class Meta:
        model = StreamImage
        fields = ("id", "image", "timestamp", "processed", "lang", "long", "fulladdress", "area", "deviceuuid")
        export_order = fields


class ClassDataResource(resources.ModelResource):
    class Meta:
        model = ClassData
        import_id_fields = ("id",)
        fields = ("id", "Name", "Turkish", "Speech")
        export_order = ("id", "Name", "Turkish", "Speech")


class OfflineModeResource(resources.ModelResource):
    class Meta:
        model = OfflineMode
        import_id_fields = ("id",)
        skip_unchanged = True
        report_skipped = False
        export_order = (
            "id",
            "video_file",
            "coordinates_json",
            "device_name",
            "area",
            "processed",
            "created_at",
            "updated_at",
        )
        exclude = ()

    def get_export_fields(self):
        fields = self.get_fields()
        # Remove any fields that are not in export_order
        available_fields = [field for field in fields if field.column_name in self._meta.export_order]
        return available_fields

    def get_import_fields(self):
        return self.get_fields()

    def get_fields(self):
        fields = super().get_fields()
        return fields


class OfflineVideoLocationInline(admin.TabularInline):
    model = OfflineVideoLocation
    extra = 0
    readonly_fields = ("timestamp", "latitude", "longitude", "address", "speed", "heading")


@admin.register(Notification)
class NotificationAdmin(ImportExportModelAdmin):
    resource_class = NotificationResource
    list_display = ("rule_name", "class_name", "department", "severity", "frequency", "created_at")
    list_filter = ("severity", "frequency", "department", "created_at")
    search_fields = ("rule_name", "class_name", "message")
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("notification_type",)


@admin.register(Detection)
class DetectionAdmin(ImportExportModelAdmin):
    resource_class = DetectionResource
    formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX, base_formats.JSON]
    list_display = ["id", "image", "class_name", "confidence", "timestamp"]
    list_filter = ["class_name", "timestamp"]
    search_fields = ["class_name"]


@admin.register(StreamImage)
class StreamImageAdmin(ImportExportModelAdmin):
    resource_class = StreamImageResource
    formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX, base_formats.JSON]
    list_display = ["id", "timestamp", "processed", "area", "deviceuuid"]
    list_filter = ["processed", "timestamp", "area"]
    search_fields = ["area", "deviceuuid", "fulladdress"]


@admin.register(NotificationType)
class NotificationTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(ClassData)
class ClassDataAdmin(ImportExportModelAdmin):
    resource_class = ClassDataResource
    list_display = ("id", "Name", "Turkish", "Speech")
    search_fields = ("Name", "Turkish")
    list_filter = ("Name",)
    formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX, base_formats.JSON]


@admin.register(OfflineMode)
class OfflineModeAdmin(ImportExportModelAdmin):
    resource_class = OfflineModeResource
    form = OfflineModeForm
    list_display = ("id", "video_file", "device_name", "area", "processed", "created_at")
    list_filter = ("processed", "area", "created_at")
    search_fields = ("device_name", "area")
    readonly_fields = ("created_at", "updated_at")
    inlines = [OfflineVideoLocationInline]
    formats = [base_formats.CSV, base_formats.XLS, base_formats.XLSX, base_formats.JSON]
    change_form_template = "admin/stream/offlinemode/change_form.html"
