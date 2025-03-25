from django.views.generic import TemplateView
from web_project import TemplateLayout
from stream.models import OfflineMode


class SourcesView(TemplateView):
    template_name = "sources.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        context["videos"] = OfflineMode.objects.all().order_by("-created_at")
        return context
