
from django import forms

class LocationForm(forms.Form):
    lat = forms.FloatField()
    lng = forms.FloatField()
    message = forms.CharField(
        max_length=1000, required=False,
        error_messages=dict(max_length='Message exceeds 1000 characters'))
