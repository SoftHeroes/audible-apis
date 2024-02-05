import uuid
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, HttpResponse
from django.urls import reverse
from django.shortcuts import redirect
from django.views.generic import FormView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.decorators.csrf import csrf_exempt
import json
import requests

from .forms import AudibleCreateLoginForm, AuthFileImportForm
from .models import AudibleDevice
from core.login import session_pool
from django.shortcuts import render

from urllib.parse import urlparse
from urllib.parse import parse_qs

from datetime import datetime

import urllib.request


# Custom JSON encoder to serialize datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def post_webhook(url, json_string):
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json_string, headers=headers)
    
    if response.status_code == 200:
        print("Webhook successfully posted!")
    else:
        print("Failed to post webhook. Status code:", response.status_code)

@csrf_exempt
def register_device(request, login_uuid, resource=None, *args, **kwargs):
    s_obj = session_pool.get_session_by_uuid(login_uuid)
    if not s_obj:
        raise Http404('Login session does not exist.')

    if resource:
        if request.META['QUERY_STRING']:
            resource += '?' + request.META['QUERY_STRING']

        data = None
        
        
        if request.method == 'POST':
            data = request.POST
        s_obj.session.request(method=request.method, url=resource, data=data)


    if s_obj.session._last_response.status_code == 302:
        # Redirect the user to the external URL
        redirect_url = s_obj.session._last_response.headers['Location']
        
        parsed_url = urlparse(redirect_url)
        resource_path = parsed_url.path
        
        if resource_path == '/ap/maplanding':
            access_token = parse_qs(parsed_url.query)['openid.oa2.access_token'][0]
            s_obj.session._access_token = access_token

         

    # we are finished
    if s_obj.is_logged_in or s_obj.session._last_response.status_code == 302:
        
        # Redirect the user to the external URL
        redirect_url = s_obj.session._last_response.headers['Location']
        
        parsed_url = urlparse(redirect_url)
        resource_path = parsed_url.path
        
        if resource_path == '/ap/maplanding':
        
            registration_data = s_obj.session.register()
            
            # AudibleDevice.create_from_registration(
            #     data=registration_data,
            #     user=AudibleDevice.user
            # )
            # session_pool.remove_session(login_uuid)
            
            content = json.dumps(registration_data, cls=DateTimeEncoder)
            
            return render(request, 'devices/login-success.html',{'content': content})
        
        # return HttpResponse(
        #     content,
        #     status=200,
        #     content_type='application/json'
        # )
        
        # return redirect('own_devices_list')

    
    status = s_obj.session._last_response.status_code
    content_type = s_obj.session._last_response.headers['Content-Type']
    content = s_obj.session._last_response_content
    
    return HttpResponse(
        content,
        status=status,
        content_type=content_type
    )


class RegisterDeviceView(LoginRequiredMixin, FormView):

    form_class = AudibleCreateLoginForm
    template_name = 'devices/create-login.html'

    # def get(self, request, *args, **kwargs):
    #     # remove old login session if exists
    #     session_key = self.request.session.session_key
    #     if session_key in session_pool:
    #         session_pool.remove_session(session_key)

    #     return super().get(request, *args, **kwargs)
    
    
    def get(self, request, *args, **kwargs):
        session_key = uuid.uuid4().hex
        # Creating Session
        s_obj = session_pool.create_session(
            session_key= session_key,
            country_code=request.GET.get('country','in'),
            with_username=False
        )

        proxy_url = self.request.build_absolute_uri(
            reverse(register_device, kwargs={'login_uuid': s_obj.session_uuid})
        )
        s_obj.start_session(proxy_url=proxy_url)
        
        return redirect(register_device, login_uuid=s_obj.session_uuid)

    def form_valid(self, form):
        cd = form.cleaned_data
        session_key = self.request.session.session_key

        s_obj = session_pool.create_session(
            session_key=session_key,
            country_code=cd['marketplace'],
            with_username=cd['with_username']
        )

        proxy_url = self.request.build_absolute_uri(
            reverse(register_device, kwargs={'login_uuid': s_obj.session_uuid})
        )
        s_obj.start_session(proxy_url=proxy_url)
        
        return redirect(register_device, login_uuid=s_obj.session_uuid)


class ImportAuthFileView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    form_class = AuthFileImportForm
    success_message = 'Your auth file has been imported'
    template_name = 'devices/auth-file-import-form.html'

    def form_valid(self, form):
        cd = form.cleaned_data
        auth_file = cd['auth_file']
        password = cd['password']

        AudibleDevice.create_from_file_import(
            file=auth_file,
            password=password,
            user=self.request.user
        )

        return redirect('own_devices_list')


class OwnDevicesListView(LoginRequiredMixin, ListView):

    model = AudibleDevice
    template_name = 'devices/audible-devices-list.html'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)


class OwnDevicesDetailView(LoginRequiredMixin, DetailView):

    model = AudibleDevice
    template_name = 'devices/audible-device-detail.html'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user)
