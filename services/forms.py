# forms.py
from django import forms
from .models import Sources

class SourcesForm(forms.ModelForm):
    class Meta:
        model = Sources
        fields = '__all__'
