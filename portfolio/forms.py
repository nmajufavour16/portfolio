from .models import Contact
from django import forms

class ContactForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)
    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter Your Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter Your Email Address'}),
            'subject': forms.TextInput(attrs={'placeholder': 'Enter Subject or Project Type'}),
            'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Tell Me About Your Project or Write Your Message Here...'}),
        }
        
    def clean_website(self):
        value = self.cleaned_data.get('website')
        if value:
            raise forms.ValidationError("Please don't try to spam me.")
        return value