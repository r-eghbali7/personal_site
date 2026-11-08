"""Views: blog"""
import json
import random
import secrets
from datetime import timedelta

from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator
from django.views import View
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db import IntegrityError, transaction
from django.db.models import Count, F, Prefetch, Q, Sum
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from accounts.models import CustomUser, OTPCode
from accounts.services import send_otp_code
from .content import article_content_and_toc
from .models import BlogCouponClaim, BlogPost, Comment, PodcastComment, PodcastLike

def is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('accept','')

class BlogListView(View):
    def get(self, request):
        posts = BlogPost.objects.filter(is_published=True).select_related('author')
        article_count = posts.count()
        selected_category = request.GET.get('category', '').strip()
        if selected_category:
            posts = posts.filter(category=selected_category)
        search_query = request.GET.get('q', '').strip()
        if search_query:
            posts = posts.filter(
                Q(title__icontains=search_query)
                | Q(summary__icontains=search_query)
                | Q(content__icontains=search_query)
            )
        categories_query = (
            BlogPost.objects.filter(is_published=True)
            .exclude(category='')
            .values_list('category', flat=True)
            .distinct()
            .order_by('category')
        )
        categories = list(categories_query)
        paginator = Paginator(posts, 9)
        # در حالت بدون فیلتر، تعداد کلِ محاسبه‌شده را دوباره نشمار
        if not selected_category and not search_query:
            paginator.count = article_count
        page_obj = paginator.get_page(request.GET.get('page'))
        context = {
            'posts': page_obj.object_list,
            'page_obj': page_obj,
            'article_count': article_count,
            'category_count': len(categories),
            'categories': categories,
            'selected_category': selected_category,
            'search_query': search_query,
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
        return render(request, 'list_blog.html', context)

class BlogDetailView(View):
    def get(self, request, slug):
        post = get_object_or_404(BlogPost, slug=slug, is_published=True)
        BlogPost.objects.filter(pk=post.pk).update(views_count=F('views_count') + 1)
        post.refresh_from_db(fields=['views_count'])
        comments = post.comments.filter(is_approved=True).select_related('user')
        post_content_html, toc = article_content_and_toc(post.content)
        pending_coupon = request.session.get('blog_coupon_pending', {})
        coupon_claim = None
        claim_id = request.session.get('blog_coupon_claim_id')
        if claim_id:
            coupon_claim = BlogCouponClaim.objects.filter(pk=claim_id, post=post).first()
        # مقالات مرتبط بر اساس تگ‌های مشترک (اولویت تعداد تگ مشترک، سپس تصادفی)
        current_tags = set(post.get_tags_list())
        related_posts = []
        if current_tags:
            candidates = (
                BlogPost.objects.filter(is_published=True)
                .exclude(pk=post.pk)
                .select_related('author')
            )
            scored = []
            for candidate in candidates:
                shared = len(current_tags & set(candidate.get_tags_list()))
                if shared:
                    scored.append((shared, candidate))
            scored.sort(key=lambda item: (-item[0], random.random()))
            related_posts = [candidate for _, candidate in scored[:3]]

        stats = BlogPost.objects.filter(is_published=True).aggregate(
            total_articles=Count('id'),
            total_reading_minutes=Sum('read_time_minutes'),
        )
        context = {
            'post': post,
            'related_posts': related_posts,
            'seo_image': request.build_absolute_uri(post.thumbnail.url) if post.thumbnail else '',
            'comments': comments,
            'post_content_html': post_content_html,
            'toc': toc,
            'coupon_otp_sent': pending_coupon.get('post_id') == post.pk,
            'coupon_phone': pending_coupon.get('phone', ''),
            'coupon_claim': coupon_claim,
            'total_articles': stats['total_articles'],
            'total_reading_minutes': stats['total_reading_minutes'] or 0,
            'enterprise_project_count': post.enterprise_project_count,
        }
        if is_ajax(request):
            return JsonResponse({'post':{'id':post.id,'title':post.title,'slug':post.slug,'content':post.content},'comments':[{'id':c.id,'body':c.body,'user': c.user.full_name or 'کاربر آکادمی'} for c in comments]})
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
        # خواندن request.body بعد از پردازش فرم توسط CSRF خطا می‌دهد؛
        # فقط برای درخواست‌های JSON بدنه را مستقیم می‌خوانیم.
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body or '{}')
            except (json.JSONDecodeError, UnicodeDecodeError):
                return JsonResponse({'error': 'ساختار درخواست معتبر نیست.'}, status=400)
        else:
            data = request.POST
        if not hasattr(data, 'get'):
            return JsonResponse({'error': 'invalid request body'}, status=400)
        body = (data.get('body') or '').strip()
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        if len(body) < 2 or len(body) > 5000:
            error_message = 'متن دیدگاه باید بین ۲ تا ۵۰۰۰ نویسه باشد.'
            if not is_ajax:
                messages.error(request, error_message)
                return redirect('blog:detail', slug=slug)
            return JsonResponse({'error': error_message}, status=400)
        c = Comment.objects.create(post=post, user=request.user, body=body, is_approved=False)
        if not is_ajax:
            messages.success(request, 'دیدگاه شما پس از تأیید نمایش داده می‌شود.')
            return redirect('blog:detail', slug=slug)
        return JsonResponse({
            'success': True,
            'pending': True,
            'message': 'دیدگاه شما پس از تأیید نمایش داده می‌شود.',
            'level': 'success',
            'comment': {
                'id': c.id,
                'body': c.body,
                'user': c.user.full_name or 'کاربر آکادمی',
            },
        })


class PodcastListView(View):
    """صفحه مستقل پادکست‌ها: همه اپیزودها زیر هم با دیدگاه و دکمه پسندیدن."""

    def get(self, request):
        posts = (
            BlogPost.objects.filter(is_published=True)
            .exclude(podcast_audio_url='')
            .select_related('author')
            .prefetch_related(
                Prefetch(
                    'podcast_comments',
                    queryset=PodcastComment.objects.filter(is_approved=True).select_related('user'),
                    to_attr='approved_comments',
                )
            )
            .annotate(
                like_count=Count('podcast_likes', distinct=True),
                comment_count=Count(
                    'podcast_comments',
                    filter=Q(podcast_comments__is_approved=True),
                    distinct=True,
                ),
            )
            .order_by('-published_at', '-created_at')
        )
        posts = list(posts)
        liked_ids = set()
        if request.user.is_authenticated and posts:
            liked_ids = set(
                PodcastLike.objects.filter(
                    user=request.user,
                    post_id__in=[post.pk for post in posts],
                ).values_list('post_id', flat=True)
            )
        return render(request, 'podcasts.html', {
            'posts': posts,
            'liked_ids': liked_ids,
            'podcast_count': len(posts),
        })


class PodcastLikeToggleView(View):
    """افزودن/برداشتن قلب (پسندیدن) یک اپیزود — با پاسخ JSON برای درخواست‌های AJAX."""

    def post(self, request, slug):
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        if not request.user.is_authenticated:
            if is_ajax:
                return JsonResponse({'error': 'login required'}, status=401)
            return redirect(f"{reverse('accounts:login')}?next={reverse('podcasts:list')}")

        post = get_object_or_404(BlogPost, slug=slug, is_published=True)
        like, created = PodcastLike.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()

        like_count = PodcastLike.objects.filter(post=post).count()
        message = 'این اپیزود را پسندیدید.' if created else 'پسندیدن این اپیزود برداشته شد.'
        level = 'success' if created else 'error'

        if is_ajax:
            return JsonResponse({
                'liked': created,
                'like_count': like_count,
                'message': message,
                'level': level,
            })

        getattr(messages, level)(request, message)
        return redirect(f"{reverse('podcasts:list')}#episode-{post.pk}")


class PodcastCommentCreateView(View):
    """ثبت دیدگاه برای یک اپیزود پادکست — با پاسخ JSON برای درخواست‌های AJAX."""

    MAX_LENGTH = 2000

    def post(self, request, slug):
        post = get_object_or_404(BlogPost, slug=slug, is_published=True)
        anchor = f"{reverse('podcasts:list')}#episode-{post.pk}"
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

        if not request.user.is_authenticated:
            if is_ajax:
                return JsonResponse({'error': 'login required'}, status=401)
            return redirect(f"{reverse('accounts:login')}?next={reverse('podcasts:list')}")

        body = (request.POST.get('body') or '').strip()
        if len(body) < 2:
            return self._error(request, anchor, 'متن دیدگاه خیلی کوتاه است.', is_ajax)
        if len(body) > self.MAX_LENGTH:
            return self._error(
                request,
                anchor,
                f'متن دیدگاه حداکثر {self.MAX_LENGTH} نویسه است.',
                is_ajax,
            )

        comment = PodcastComment.objects.create(post=post, user=request.user, body=body)

        if is_ajax:
            return JsonResponse({
                'message': 'دیدگاه شما ثبت شد.',
                'level': 'success',
                'html': render_to_string(
                    'includes/comment_item.html',
                    {'comment': comment},
                    request=request,
                ),
                'comment_count': post.podcast_comments.filter(is_approved=True).count(),
            })

        messages.success(request, 'دیدگاه شما ثبت شد.')
        return redirect(anchor)

    def _error(self, request, anchor, message, is_ajax):
        if is_ajax:
            return JsonResponse({'error': message}, status=400)
        messages.error(request, message)
        return redirect(anchor)
