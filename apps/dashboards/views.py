import cv2
import uuid
from django.core import serializers
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta


class DashboardsView(TemplateView):

    def get_context_data(self, **kwargs):
        # Parent sınıftan context'i al
        context = super().get_context_data(**kwargs)


        TemplateLayout.init(self, context)

        return context
