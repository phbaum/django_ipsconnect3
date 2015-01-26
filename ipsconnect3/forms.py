from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm

class LoginForm(forms.Form):
    username = forms.CharField(label='Login Name', max_length=254)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    
    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if user is None:
            raise forms.ValidationError("The username or password supplied is not valid.")
        # elif not user.is_active:
        #     raise forms.ValidationError("This user account is locked")
        self.user = user
        return cleaned_data
