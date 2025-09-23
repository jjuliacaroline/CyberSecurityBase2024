from django import forms

class VerifyForm(forms.Form):
    verify_url = forms.CharField(label="Add URL to verify", required=True)

    def clean_verify_url(self):
        url = self.cleaned_data['verify_url']
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        return url