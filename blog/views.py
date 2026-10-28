"""Views: blog"""
import json
import secrets
from datetime import timedelta

from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator
from django.views import View
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone
from accounts.models import CustomUser, OTPCode
from accounts.services import send_otp_code
from .models import BlogCouponClaim, BlogPost, Comment

def is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept','')

class BlogListView(View):
    def get(self, request):
        posts = BlogPost.objects.filter(is_published=True).select_related('author')
        article_count = posts.count()
        selected_category = request.GET.get('category', '').strip()
        if selected_category:
            posts = posts.filter(category=selected_category)
        categories_query = (
            BlogPost.objects.filter(is_published=True)
            .exclude(category='')
            .values_list('category', flat=True)
            .distinct()
            .order_by('category')
        )
        categories = list(categories_query)
        page_obj = Paginator(posts, 9).get_page(request.GET.get('page'))
        context = {
            'posts': page_obj.object_list,
            'page_obj': page_obj,
            'article_count': article_count,
            'category_count': len(categories),
            'categories': categories,
            'selected_category': selected_category,
        }
        if is_ajax(request):
            return JsonResponse({
                'posts': [
                    {'id': p.id, 'title': p.title, 'slug': p.slug, 'summary': p.summary}
                    for p in page_obj.object_list
                ],
                'page': page_obj.number,
                'pages': page_obj.paginator.num_pages,
                'total': page_obj.paginator.count,
            })
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
        pending_coupon = request.session.get('blog_coupon_pending', {})
        coupon_claim = None
        claim_id = request.session.get('blog_coupon_claim_id')
        if claim_id:
            coupon_claim = BlogCouponClaim.objects.filter(pk=claim_id, post=post).first()
        context = {
            'post': post,
            'comments': comments,
            'coupon_otp_sent': pending_coupon.get('post_id') == post.pk,
            'coupon_phone': pending_coupon.get('phone', ''),
            'coupon_claim': coupon_claim,
        }
        if is_ajax(request):
            return JsonResponse({'post':{'id':post.id,'title':post.title,'slug':post.slug,'content':post.content},'comments':[{'id':c.id,'body':c.body,'user':str(c.user)} for c in comments]})
        return render(request, 'detail_blog.html', context)


class BlogCouponRequestView(View):
    def post(self, request, slug):
        post = get_object_or_404(BlogPost, slug=slug, is_published=True)
        phone = (request.POST.get('phone_number') or '').strip()
        if len(phone) != 11 or not phone.startswith('09') or not phone.isdigit():
            messages.error(request, 'شماره موبایل را با قالب ۰۹ و ۱۱ رقم وارد کنید.')
            return redirect('blog:detail', slug=slug)

        if CustomUser.objects.filter(phone_number=phone).exists():
            messages.info(request, 'برای شماره‌های ثبت‌شده، وارد حساب کاربری شوید تا پیشنهادهای ویژه را ببینید.')
            return redirect('blog:detail', slug=slug)

        if BlogCouponClaim.objects.filter(phone_number=phone).exists():
            messages.info(request, 'برای هر شماره موبایل فقط یک کد تخفیف قابل دریافت است.')
            return redirect('blog:detail', slug=slug)

        now = timezone.now()
        recent_codes = OTPCode.objects.filter(phone_number=phone, created_at__gte=now - timedelta(hours=1))
        if recent_codes.count() >= 5 or recent_codes.filter(created_at__gte=now - timedelta(seconds=60)).exists():
            messages.error(request, 'برای ارسال دوباره کد کمی صبر کنید.')
            return redirect('blog:detail', slug=slug)

        otp = OTPCode.create_for_phone(phone)
        result = send_otp_code(phone, otp.code)
        if not result.get('success'):
            otp.is_used = True
            otp.save(update_fields=['is_used'])
            messages.error(request, 'ارسال پیامک ناموفق بود. لطفاً کمی بعد دوباره تلاش کنید.')
            return redirect('blog:detail', slug=slug)

        request.session['blog_coupon_pending'] = {'phone': phone, 'post_id': post.pk}
        request.session.set_expiry(settings.OTP_EXPIRY_MINUTES * 60)
        messages.success(request, 'کد تأیید برای شماره واردشده ارسال شد.')
        return redirect('blog:detail', slug=slug)


class BlogCouponVerifyView(View):
    def post(self, request, slug):
        post = get_object_or_404(BlogPost, slug=slug, is_published=True)
        pending = request.session.get('blog_coupon_pending', {})
        if pending.get('post_id') != post.pk or not pending.get('phone'):
            messages.error(request, 'ابتدا شماره موبایل را برای دریافت کد تأیید ثبت کنید.')
            return redirect('blog:detail', slug=slug)

        code = (request.POST.get('otp_code') or '').strip()
        if len(code) != 6 or not code.isdigit():
            messages.error(request, 'کد تأیید باید ۶ رقم باشد.')
            return redirect('blog:detail', slug=slug)

        attempts_key = 'blog_coupon_otp_attempts'
        attempts = request.session.get(attempts_key, 0)
        if attempts >= 5:
            OTPCode.objects.filter(
                phone_number=pending['phone'],
                is_used=False,
            ).update(is_used=True)
            request.session.pop('blog_coupon_pending', None)
            request.session.pop(attempts_key, None)
            messages.error(request, 'تعداد تلاش‌ها بیش از حد مجاز بود. دوباره درخواست کد کنید.')
            return redirect('blog:detail', slug=slug)

        otp = OTPCode.objects.filter(
            phone_number=pending['phone'],
            code=code,
            is_used=False,
        ).order_by('-created_at').first()
        if not otp or not otp.is_valid:
            request.session[attempts_key] = attempts + 1
            messages.error(request, 'کد واردشده اشتباه است یا اعتبار آن تمام شده است.')
            return redirect('blog:detail', slug=slug)
        if CustomUser.objects.filter(phone_number=pending['phone']).exists():
            otp.is_used = True
            otp.save(update_fields=['is_used'])
            request.session.pop('blog_coupon_pending', None)
            messages.info(request, 'برای شماره‌های ثبت‌شده، وارد حساب کاربری شوید.')
            return redirect('blog:detail', slug=slug)

        coupon_code = f'ARCH-{secrets.token_hex(4).upper()}'
        try:
            with transaction.atomic():
                otp.is_used = True
                otp.save(update_fields=['is_used'])
                claim = BlogCouponClaim.objects.create(
                    phone_number=pending['phone'],
                    coupon_code=coupon_code,
                    discount_percent=post.coupon_discount_percent,
                    post=post,
                )
        except IntegrityError:
            request.session.pop('blog_coupon_pending', None)
            messages.info(request, 'برای هر شماره موبایل فقط یک کد تخفیف قابل دریافت است.')
            return redirect('blog:detail', slug=slug)

        request.session.pop('blog_coupon_pending', None)
        request.session.pop(attempts_key, None)
        request.session['blog_coupon_claim_id'] = claim.pk
        messages.success(request, 'شماره تأیید شد. کد تخفیف شما در همین صفحه نمایش داده می‌شود.')
        return redirect('blog:detail', slug=slug)


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
