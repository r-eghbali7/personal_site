"""Views: blog"""
import json

from django.contrib import messages
from django.views import View
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import F
from .models import BlogPost, Comment

def is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept','')

class BlogListView(View):
    def get(self, request):
        posts = BlogPost.objects.filter(is_published=True).select_related('author')
        context = {'posts': posts}
        if is_ajax(request):
            return JsonResponse({'posts':[{'id':p.id,'title':p.title,'slug':p.slug,'summary':p.summary} for p in posts]})
        response = render(request, 'list_blog.html', context)
        response.content = response.content.replace(
            b'</body>',
            b'<script src="/static/js/site-header.js" defer></script></body>',
            1,
        )
        return response

class BlogDetailView(View):
    def get(self, request, slug):
        post = get_object_or_404(BlogPost, slug=slug, is_published=True)
        BlogPost.objects.filter(pk=post.pk).update(views_count=F('views_count') + 1)
        post.refresh_from_db(fields=['views_count'])
        comments = post.comments.filter(is_approved=True).select_related('user')
        context = {'post': post, 'comments': comments}
        if is_ajax(request):
            return JsonResponse({'post':{'id':post.id,'title':post.title,'slug':post.slug,'content':post.content},'comments':[{'id':c.id,'body':c.body,'user':str(c.user)} for c in comments]})
        return render(request, 'detail_blog.html', context)


class BlogCommentView(View):
    def post(self, request, slug):
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') != 'XMLHttpRequest':
                return redirect(f"/accounts/login/?next={request.path}")
            return JsonResponse({'error': 'login required'}, status=401)
        post = get_object_or_404(BlogPost, slug=slug, is_published=True)
        try:
            data = json.loads(request.body or '{}')
        except (json.JSONDecodeError, UnicodeDecodeError):
            data = request.POST
        if not hasattr(data, 'get'):
            return JsonResponse({'error': 'invalid request body'}, status=400)
        body = (data.get('body') or '').strip()
        if len(body) < 2 or len(body) > 5000:
            if request.headers.get('x-requested-with') != 'XMLHttpRequest':
                messages.error(request, 'متن دیدگاه باید بین ۲ تا ۵۰۰۰ نویسه باشد.')
                return redirect('blog:detail', slug=slug)
            return JsonResponse({'error': 'comment length must be between 2 and 5000 characters'}, status=400)
        c = Comment.objects.create(post=post, user=request.user, body=body, is_approved=False)
        if request.headers.get('x-requested-with') != 'XMLHttpRequest':
            messages.success(request, 'دیدگاه شما پس از تأیید نمایش داده می‌شود.')
            return redirect('blog:detail', slug=slug)
        return JsonResponse({'success': True, 'comment': {'id': c.id, 'body': c.body, 'user': str(c.user)}})
