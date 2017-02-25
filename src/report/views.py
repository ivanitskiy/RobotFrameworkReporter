import sys
import traceback

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.http.response import HttpResponseServerError, HttpResponseNotFound
from django.shortcuts import render
from django.template.context import Context
from django.template.loader import get_template
from django.urls.base import reverse
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from forms import UserForm
from models import TestRun, TestRunStatus
from report.forms import UploadOutputXmlForm
from report.utils import handle_uploaded_file


@login_required(login_url="login/")
def home(request):
    return render(request, "report/home.html")


class TestRunStatusListView(ListView):
    model = TestRunStatus
    queryset = TestRunStatus.objects.filter(name="All Tests")
    template_name = 'report/test_run_list.html'

    @method_decorator(login_required(login_url="login/"))
    def dispatch(self, *args, **kwargs):
        return super(TestRunStatusListView, self).dispatch(*args, **kwargs)


def adduser(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            new_user = User.objects.create_user(**form.cleaned_data)
            login(request, new_user)
            # redirect, or however you want to get to the main view
            return HttpResponseRedirect(reverse('home'))
    else:
        form = UserForm()

    return render(request, 'report/adduser.html', {'form': form})


@login_required(login_url="login/")
def upload_output_xml(request):
    if request.method == 'POST':
        form = UploadOutputXmlForm(request.POST, request.FILES)
        print "HELLP"
        if form.is_valid():
            print "YES"
            try:
                handle_uploaded_file(request)
            except:
                tt, value, tb = sys.exc_info()
                print {'exception_value': value,
                       'value': tt,
                       'tb': traceback.format_exception(tt, value, tb)}
                return handler500(request)
            return HttpResponseRedirect(reverse('home'))
        else:
            return handler500(request)
    else:
        print "No"
        form = UploadOutputXmlForm()
    return render(request, 'report/upload_xml_file.html', {'form': form})


def handler500(request, template_name='500.html'):
    t = get_template(template_name)
    tt, value, tb = sys.exc_info()
    ctx = Context({'exception_value': value,
                   'value': tt,
                   'tb': traceback.format_exception(tt, value, tb)})
    return HttpResponseServerError(t.render(ctx))


def handler404(request, template_name='404.html'):
    t = get_template(template_name)
    ctx = Context({})
    return HttpResponseNotFound(t.render(ctx))
