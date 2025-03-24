from django import forms
from .models import OfflineMode


class OfflineModeForm(forms.ModelForm):
    class Meta:
        model = OfflineMode
        fields = "__all__"
        widgets = {
            "video_file": forms.FileInput(
                attrs={"accept": "video/*", "class": "form-control", "data-show-upload-progress": "true"}
            ),
        }
