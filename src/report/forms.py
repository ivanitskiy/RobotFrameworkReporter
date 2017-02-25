'''
Created on Jan 28, 2017

@author: ivanitskiy
'''
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.forms.models import ModelForm


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username",
                               max_length=30,
                               widget=forms.TextInput(attrs={'class': 'form-control',
                                                             'name': 'username'}
                                                      )
                               )
    password = forms.CharField(label="Password",
                               max_length=30,
                               widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                                 'name': 'password'}
                                                          )
                               )


class UploadOutputXmlForm(forms.Form):
    xmlfile = forms.FileField()


class UserForm(ModelForm):
    username = forms.CharField(label="User Name",
                               widget=forms.TextInput(attrs={'class': 'form-control', 'name': 'username'}))
    email = forms.CharField(label="Email address", widget=forms.EmailInput(attrs={'class': 'form-control', 'name': 'email'}))
    password = forms.CharField(label="Password",
                               widget=forms.PasswordInput(attrs={'class': 'form-control',
                                                                 'name': 'password'}
                                                          )
                               )

    class Meta:
        model = User
        fields = ('username', 'email', 'password')
