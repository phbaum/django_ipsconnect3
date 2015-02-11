from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext, ugettext_lazy as _

from ipsconnect3 import utils

class IPSCPasswordMixin:
    """
    A mixin for the IPS Connect password cleaning routine
    """
    def _clean_password(self, password=''):
        """
        Cleans the password in accordance with IPS Connect input cleaning routines
        Replaces HTML-relevant characters with respective HTML entities
        """
        htmlentities = [
            ('&',   '&amp;'), # this needs to run first to avoid replacing later ampersands
            ('\\',  '&#092;'),
            ('!',   '&#33;'),
            ('$',   '&#036;'),
            ('"',   '&quot;'),
            ('<',   '&lt;'),
            ('>',   '&gt;'),
            ('\'',  '&#39;'),
        ]
        for char, entity in htmlentities:
            password = password.replace(char, entity)
        return password
    
    def clean_password(self):
        """
        Make cleaning happen automatically for the 'password' field
        """
        password = self.cleaned_data.get('password', '')
        return self._clean_password(password)
    

class LoginForm(forms.Form, IPSCPasswordMixin):
    username = forms.CharField(label=_("Login Name"), max_length=254)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    
    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if user is None:
            raise forms.ValidationError(_("The username or password supplied is not valid."))
        # elif not user.is_active:
        #     raise forms.ValidationError("This user account is locked")
        self.user = user
        return cleaned_data


class RegistrationForm(forms.Form, IPSCPasswordMixin):
    """
    doc
    """
    error_messages = {
        'duplicate_username': _("This username is already taken."),
        'duplicate_email': _("This e-mail address is already taken."),
        'password_mismatch': _("The two password fields didn't match."),
    }
    
    username = forms.RegexField(label=_("Username"),
        min_length=3,
        max_length=26,
        regex=r'^[\w.@+-]+$',
        help_text=_("Required. Between 3 and 26 characters. Letters, digits and "
                      "@/./+/-/_ only."),
        error_messages={
            'invalid': _("This value may contain only letters, numbers and "
                         "@/./+/-/_ characters.")})
    email = forms.EmailField(label=_("E-mail"))
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput(render_value=True),
                                min_length=3, max_length=26)
    password2 = forms.CharField(label=_("Confirm Password"), widget=forms.PasswordInput(render_value=True),
                                help_text=_("Enter the same password as above, for verification."))

    def clean_username(self):
        username = self.cleaned_data.get('username')
        result = utils.request_check(username=username, displayname=username)
        if result.get('status') == 'SUCCESS':
            if result.get('username') == False or result.get('displayname') == False:
                raise forms.ValidationError(
                    self.error_messages['duplicate_username'],
                    code='duplicate_username',
                )
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        result = utils.request_check(email=email)
        if result.get('status') == 'SUCCESS' and result.get('email') == False:
            raise forms.ValidationError(
                self.error_messages['duplicate_email'],
                code='duplicate_email',
            )
        return email
                              
    def clean_password1(self):
        return self._clean_password(self.cleaned_data.get('password1'))
        
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self._clean_password(self.cleaned_data.get('password2'))
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2
    
    # def clean(self):
    #     cleaned_data = super(RegistrationForm, self).clean()
    #     username = cleaned_data.get('username')
    #     displayname = username # Username and display name are the same for us
    #     email = cleaned_data.get('email')
    #
    #     result = utils.request_check(username, displayname, email)
    #     if result.get('status') == 'SUCCESS':
    #         errors = []
    #         if result.get('username') == False or result.get('displayname') == False:
    #             errors.append(forms.ValidationError(
    #                 self.error_messages['duplicate_username'],
    #                 code='duplicate_username',
    #             ))
    #         if result.get('email') == False:
    #             errors.append(forms.ValidationError(
    #                 self.error_messages['duplicate_email'],
    #                 code='duplicate_email',
    #             ))
    #         raise forms.ValidationError(errors)
    #     else:
    #         raise forms.ValidationError(_("There was a problem validating your registration."))
    #     return cleaned_data

