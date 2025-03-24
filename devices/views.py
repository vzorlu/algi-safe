from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Device, License, DeviceReport
from .serializers import DeviceSerializer, DeviceDataSerializer
import uuid  # Lisans anahtarı üretmek için
import traceback
from django.views.generic import TemplateView
from web_project import TemplateLayout
from rest_framework.permissions import AllowAny  # AllowAny izni


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [AllowAny]  # Herkese açık; gerekirse izinleri özelleştirin

    def create(self, request, *args, **kwargs):
        # Cihaz oluşturmak için gelen veriyi serializer ile doğrulama
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class DevicesView(TemplateView):
    # Predefined function
    def get_context_data(self, **kwargs):
        # A function to init the global layout. It is defined in web_project/__init__.py file
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        return context


@api_view(["POST"])
def register_device(request):
    serializer = DeviceSerializer(data=request.data)

    if serializer.is_valid():
        device = serializer.save()

        license_key = str(uuid.uuid4())  # UUID kullanarak lisans anahtarı oluşturma
        license = License.objects.create(device=device, license_key=license_key, is_active=False)

        return Response({"device": serializer.data, "license_key": license.license_key}, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def web_activate_device(request):
    """
    Web arayüzünden cihazı lisans anahtarı ile aktive eder.
    """
    license_key = request.data.get("license_key")

    try:
        # Lisans anahtarını bul ve cihaza eşleştir
        license = License.objects.get(license_key=license_key)

        if not license.is_active:
            return Response(
                {"status": "License is valid but needs activation via SH script"}, status=status.HTTP_200_OK
            )
        else:
            return Response({"status": "License is already active"}, status=status.HTTP_200_OK)

    except License.DoesNotExist:
        return Response({"error": "License not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
def sh_activate_device(request):
    """
    SH betiğinden lisans anahtarı ve mac_address bilgileri gönderilerek aktivasyon işlemi yapılır.
    """
    license_key = request.data.get("license_key")
    mac_address = request.data.get("mac_address")

    try:
        # Lisans anahtarını bul ve cihazla eşleştir
        license = License.objects.get(license_key=license_key)

        if not license.is_active:
            # Cihaz bilgilerini güncelle ve lisansı aktif hale getir
            device = license.device
            device.mac_address = mac_address
            device.save()

            # Lisansı aktif hale getir
            license.is_active = True
            license.save()

            return Response({"status": "Device activated successfully"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "License is already active"}, status=status.HTTP_400_BAD_REQUEST)
    except License.DoesNotExist:
        return Response({"error": "License not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
def post_device_data(request):
    serializer = DeviceDataSerializer(data=request.data)
    if serializer.is_valid():
        device_id = request.data.get("device_id")

        try:
            device = Device.objects.get(device_id=device_id)
            serializer.save(device=device)

            # NEW: Add device data to DeviceReport if MAC address matches
            mac_address = device.mac_address
            report, created = DeviceReport.objects.get_or_create(mac_address=mac_address)
            data_entry = {
                "cpu_usage": request.data.get("cpu_usage"),
                "memory_usage": request.data.get("memory_usage"),
                "disk_space": request.data.get("disk_space"),
                "timestamp": serializer.data.get("timestamp"),
            }
            if not created:
                report_data = report.data
                report_data.append(data_entry)
                report.data = report_data
            else:
                report.data = [data_entry]
            report.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Device.DoesNotExist:
            return Response({"error": "Device not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def verify_license(request):
    license_key = request.data.get("license_key")
    try:
        license = License.objects.get(license_key=license_key)
        if license.is_active:
            return Response({"status": "License verified successfully"}, status=status.HTTP_200_OK)
        return Response({"error": "License is inactive"}, status=status.HTTP_400_BAD_REQUEST)
    except License.DoesNotExist:
        return Response({"error": "License not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
def device_list(request):
    try:
        devices = Device.objects.all()  # Tüm cihazları veritabanından alır
        serializer = DeviceSerializer(devices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error occurred: {str(e)}")  # DEBUG: Hata mesajını yazdır
        print(traceback.format_exc())  # Hatanın tam izini yazdır (stack trace)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
