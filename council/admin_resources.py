from import_export import resources
from .models import Way, Department

class WayResource(resources.ModelResource):
    class Meta:
        model = Way
        fields = "__all__"  # Tüm alanlar dahil ediliyor
        export_order = ["id", "name", "description"]  # Alan sırasını kontrol edin (varsa)

class DepartmentResource(resources.ModelResource):
    class Meta:
        model = Department
        fields = "__all__"
