'''
Created on Jan 28, 2017

@author: ivanitskiy
'''
from django.conf.urls import url

from . import views


urlpatterns = [
    #     url(r'^$', views.home, name='home'),
    url(r'^$', views.TestRunStatusListView.as_view(), name='home'),
    url(r'^adduser/$', views.adduser, name='adduser'),
    url(r'^upload/$', views.upload_output_xml, name='upload_output_xml'),
]
