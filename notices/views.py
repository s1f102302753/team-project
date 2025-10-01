from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from .models import Notice

def notice_list(request):
    notices = Notice.objects.all().order_by('-created_at')
    return render(request, 'notices/index.html', {'notices': notices})

def notice_detail(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    return render(request, 'notices/detail.html', {'notice': notice})

