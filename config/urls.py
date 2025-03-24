from django.contrib import admin
from django.urls import include, path
from web_project.views import SystemView
from apps.containers.views import get_call_details
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "Algi Yönetim Paneli"
admin.site.site_title = "AI Studio"
admin.site.index_title = "Algi Yönetim Paneli"


urlpatterns = [
    path("admin/", admin.site.urls),
    # Dashboard urls
    path("", include("apps.dashboards.urls")),
    # layouts urls
    path("", include("apps.layouts.urls")),
    # FrontPages urls
    path("", include("apps.front_pages.urls")),
    # FrontPages urls
    path("", include("apps.mail.urls")),
    # Chat urls
    path("", include("apps.chat.urls")),
    # Calendar urls
    path("", include("apps.my_calendar.urls")),
    # kanban urls
    path("", include("apps.kanban.urls")),
    # eCommerce urls
    path("", include("apps.ecommerce.urls")),
    # Academy urls
    path("", include("apps.academy.urls")),
    # Logistics urls
    path("", include("apps.logistics.urls")),
    # Invoice urls
    path("", include("apps.invoice.urls")),
    # User urls
    path("", include("apps.users.urls")),
    # Access urls
    path("", include("apps.access.urls")),
    # Pages urls
    path("", include("apps.pages.urls")),
    # Auth urls
    path("", include("apps.authentication.urls")),
    # Wizard urls
    path("", include("apps.wizard_examples.urls")),
    # ModalExample urls
    path("", include("apps.modal_examples.urls")),
    # Card urls
    path("", include("apps.cards.urls")),
    # UI urls
    path("", include("apps.ui.urls")),
    # Extended UI urls
    path("", include("apps.extended_ui.urls")),
    # Icons urls
    path("", include("apps.icons.urls")),
    path("", include("apps.containers.urls")),
    # Forms urls
    path("", include("apps.forms.urls")),
    # FormLayouts urls
    path("", include("apps.form_layouts.urls")),
    # FormWizard urls
    path("", include("apps.form_wizard.urls")),
    # FormValidation urls
    path("", include("apps.form_validation.urls")),
    # Tables urls
    path("", include("apps.tables.urls")),
    # Chart urls
    path("", include("apps.charts.urls")),
    # Map urls
    path("", include("apps.maps.urls")),
    # auth urls
    path("", include("auth.urls")),
    # transaction urls
    path("", include("apps.transactions.urls")),
    path("", include("apps.jobs.urls")),
    path("", include("apps.logs.urls")),
    path("", include("devices.urls")),
    path("", include("services.urls")),
    path("api/stream/", include("stream.urls")),
    path("", include("council.urls")),
    path("get_call_details/<str:call_id>/", get_call_details, name="get_call_details"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = SystemView.as_view(template_name="pages_misc_error.html", status=404)
handler403 = SystemView.as_view(template_name="pages_misc_not_authorized.html", status=403)
handler400 = SystemView.as_view(template_name="pages_misc_error.html", status=400)
handler500 = SystemView.as_view(template_name="pages_misc_error.html", status=500)
