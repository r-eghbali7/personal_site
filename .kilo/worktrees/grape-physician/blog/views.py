"""Views: blog (stub)"""
from django.views import View
from django.shortcuts import render


class BlogListView(View):
    def get(self, request):
        return render(request, 'list_blog.html')


class BlogDetailView(View):
    def get(self, request, slug):
        return render(request, 'detail_blog.html')
