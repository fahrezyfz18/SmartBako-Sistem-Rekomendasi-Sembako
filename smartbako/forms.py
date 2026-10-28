from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(
        required=True, 
        max_length=30, 
        label="Nama Lengkap",
        widget=forms.TextInput(attrs={'placeholder': 'Nama Lengkap Anda'})
    )
    email = forms.EmailField(
        required=True, 
        help_text="Wajib. Masukkan alamat email yang aktif.",
        widget=forms.EmailInput(attrs={'placeholder': 'nama@email.com'})
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user