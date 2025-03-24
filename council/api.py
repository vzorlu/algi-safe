from httpcore import Response
from rest_framework import viewsets


class DepartmentViewSet(viewsets.ModelViewSet):
    # ...existing code...

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.name = request.data.get("name")
        instance.save()

        # Update class names
        class_names = request.data.get("class_names", [])
        instance.class_names.set(class_names)

        return Response(self.get_serializer(instance).data)
