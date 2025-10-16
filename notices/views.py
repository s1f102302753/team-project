# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView
from .models import Notice, Post
from django.contrib.auth.decorators import login_required

app_name = 'notices'

class NoticeHomeView(TemplateView):
    template_name = 'notices/home.html'


@login_required
def notices_list(request):
    notices = fetch_notices_for_user(request.user)
    return  render(request, 'notices/notices_list.html', {'notices': notices})
