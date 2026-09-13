from .models import Contact
from django import forms

class ContactForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'e.g. John Doe'}),
            'email': forms.EmailInput(attrs={'placeholder': 'e.g. john@example.com'}),
            'subject': forms.TextInput(attrs={'placeholder': 'e.g. Project Inquiry'}),
            'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Tell me about your project...'}),
        }
        
    def clean_website(self):
        value = self.cleaned_data.get('website')
        if value:
            raise forms.ValidationError("Please don't try to spam me.")
        return value