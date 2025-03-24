from import_export import resources
from .models import Way, Department

class WayResource(resources.ModelResource):
    class Meta:
        model = Way
        fields = ('way_id', 'base_type', 'nodes', 'destination', 'highway',
                 'hist_ref', 'loc_name', 'maxspeed', 'name', 'oneway',
                 'ref', 'lanes', 'nat_ref', 'toll')
        import_id_fields = ['way_id']
        skip_unchanged = True

class DepartmentResource(resources.ModelResource):
    class Meta:
        model = Department
        fields = ('id', 'name', 'description', 'created_at', 'updated_at')
        skip_unchanged = True
