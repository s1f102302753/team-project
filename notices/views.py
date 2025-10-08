from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView

app_name = 'notices'

class NoticeHomeView(TemplateView):
    template_name = 'notices/home.html'