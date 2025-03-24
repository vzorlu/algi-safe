from .views import (
    add_source,
    update_source,
    delete_source,
    ServicesView,
    ServicesAddView,
    refresh_source_image,  # Add this import
    get_source,  # Add this import
)
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('services/sources/', ServicesView.as_view(), name='services-sources'),
    path('services/task-add/', ServicesAddView.as_view(), name='task-add'),
    path('services/sources/add-source/', add_source, name='add-source'),
    path('services/sources/update-source/<int:source_id>/', update_source, name='update-source'),
    path('services/sources/delete-source/<int:source_id>/', delete_source, name='delete-source'),
    path('services/sources/refresh-image/<int:source_id>/', refresh_source_image, name='refresh-source-image'),  # Add this line
    path('services/sources/get-source/<int:source_id>/', get_source, name='get-source'),  # Add this line
    path('services/sources/save-polygon/', views.save_polygon, name='save-polygon'),  # Add this line
    path('services/sources/<int:source_id>/polygons/<int:polygon_index>/', views.delete_polygon, name='delete_polygon'),  # Update this line
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
