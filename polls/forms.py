from django import forms

class VerifyForm(forms.Form):
    id = forms.IntegerField()
    verify_url = forms.CharField(label="Add URL to verify", required=True)

    def clean_verify_url(self):
        return self.cleaned_data['verify_url']