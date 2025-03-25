from django import forms
from .models import OfflineMode


class OfflineModeForm(forms.ModelForm):
    class Meta:
        model = OfflineMode
        fields = ["video_file", "device_name"]

    def clean(self):
        cleaned_data = super().clean()
        # Ensure the form action doesn't append "undefined"
        return cleaned_data

    class Media:
        js = ("js/offlinemode_form.js",)
