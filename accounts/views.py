"""
Views: accounts

فلوی احراز هویت:

  ثبت‌نام:  RegisterView → ذخیره اطلاعات در session → ارسال OTP → OTPVerifyView → ایجاد User + Login
  ورود:     LoginView → احراز هویت با رمز عبور → Login مستقیم
  OTP مجزا: OTPRequestView → OTPVerifyView → Login (برای کاربران موجود بدون رمز)
"""

import logging
from django.views import View
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import login, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.db import transaction
from django.db.models import Avg, Count
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache

from .models import CustomUser, OTPCode
from .forms import RegisterForm, LoginForm, OTPVerifyForm, OTPRequestForm, ProfileForm
from .services import send_otp_code
from tickets.forms import TicketCreateForm
from tickets.models import Ticket, TicketMessage

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# ثبت‌نام
# ──────────────────────────────────────────────────────────────

@method_decorator(never_cache, name='dispatch')
class RegisterView(View):
    """
    مرحله اول ثبت‌نام:
    - نمایش فرم (GET)
    - اعتبارسنجی اطلاعات + ذخیره در session + ارسال OTP (POST)
    - redirect به صفحه OTP
    """

    template_name = 'register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('courses:home')
        return render(request, self.template_name, {'form': RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if not form.is_valid():
            # بازگرداندن خطاها به template
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0]
            return render(request, self.template_name, {
                'form': form,
                'errors': errors,
            })

        mobile = form.cleaned_data['mobile']
        fullname = form.cleaned_data['fullname']
        password = form.cleaned_data['password']

        # ذخیره اطلاعات ثبت‌نام در session تا بعد از تأیید OTP استفاده شود
        request.session['register_data'] = {
            'phone_number': mobile,
            'full_name': fullname,
            'password': password,
            'action': 'register',
        }

        # ایجاد و ارسال OTP
        otp = OTPCode.create_for_phone(mobile)
        result = send_otp_code(mobile, otp.code)

        if not result['success']:
            logger.warning('OTP send failed for %s: %s', mobile, result['message'])
            if settings.DEBUG:
                messages.warning(request, f'ارسال پیامک ناموفق بود. کد تست: {otp.code}')
            else:
                messages.error(request, 'ارسال کد تأیید ناموفق بود. کمی بعد دوباره تلاش کنید.')
        else:
            messages.success(request, f'کد تأیید به شماره {mobile} ارسال شد.')

        return redirect('accounts:otp_verify')


# ──────────────────────────────────────────────────────────────
# ورود
# ──────────────────────────────────────────────────────────────

@method_decorator(never_cache, name='dispatch')
class LoginView(View):
    """
    ورود با شماره موبایل + رمز عبور.
    """

    template_name = 'login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('courses:home')
        return render(request, self.template_name, {'form': LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST, request=request)
        if not form.is_valid():
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0] if field != '__all__' else error_list[0]
            return render(request, self.template_name, {
                'form': form,
                'errors': errors,
                'non_field_error': form.non_field_errors()[0] if form.non_field_errors() else None,
            })

        user = form.get_user()
        login(request, user, backend='accounts.backends.PhoneAuthBackend')
        messages.success(request, f'خوش آمدید، {user.full_name or user.phone_number}!')

        next_url = request.POST.get('next', '')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)
        return redirect('courses:home')


# ──────────────────────────────────────────────────────────────
# OTP
# ──────────────────────────────────────────────────────────────

@method_decorator(never_cache, name='dispatch')
class OTPVerifyView(View):
    """
    تأیید کد OTP.

    این View دو حالت دارد:
    1. بعد از ثبت‌نام: session['register_data']['action'] == 'register'
       → ایجاد کاربر جدید + login
    2. بعد از درخواست OTP برای ورود: session['register_data']['action'] == 'login_otp'
       → login کاربر موجود
    """

    template_name = 'otp.html'

    def get(self, request):
        register_data = request.session.get('register_data')
        if not register_data:
            messages.error(request, 'لطفاً ابتدا شماره موبایل خود را وارد کنید.')
            return redirect('accounts:register')

        phone = register_data.get('phone_number', '')
        masked = f'{phone[:4]}****{phone[7:]}'
        return render(request, self.template_name, {
            'masked_phone': masked,
            'form': OTPVerifyForm(),
        })

    def post(self, request):
        register_data = request.session.get('register_data')
        if not register_data:
            return redirect('accounts:register')

        form = OTPVerifyForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {
                'form': form,
                'error': form.errors.get('code', ['کد وارد شده نامعتبر است.'])[0],
            })

        phone = register_data['phone_number']
        code = form.cleaned_data['code']

        # بررسی کد OTP در دیتابیس
        otp_obj = OTPCode.objects.filter(
            phone_number=phone,
            code=code,
            is_used=False,
        ).last()

        if not otp_obj or not otp_obj.is_valid:
            return render(request, self.template_name, {
                'form': form,
                'error': 'کد وارد شده اشتباه یا منقضی شده است.',
            })

        # علامت‌گذاری کد به عنوان استفاده‌شده
        otp_obj.is_used = True
        otp_obj.save(update_fields=['is_used'])

        action = register_data.get('action', 'register')

        if action == 'register':
            # ایجاد کاربر جدید
            user = CustomUser.objects.create_user(
                phone_number=phone,
                password=register_data.get('password'),
                full_name=register_data.get('full_name', ''),
            )
            logger.info('New user registered: %s', phone)
        else:
            # ورود کاربر موجود از طریق OTP
            try:
                user = CustomUser.objects.get(phone_number=phone)
            except CustomUser.DoesNotExist:
                messages.error(request, 'کاربری با این شماره یافت نشد.')
                return redirect('accounts:register')

        # پاک‌سازی session
        del request.session['register_data']

        # ورود کاربر
        login(request, user, backend='accounts.backends.PhoneAuthBackend')
        messages.success(request, f'خوش آمدید، {user.full_name or user.phone_number}!')

        return redirect('courses:home')

    def _resend_otp(self, request, phone):
        """helper برای ارسال مجدد OTP (فراخوانی از طریق URL جداگانه)."""
        otp = OTPCode.create_for_phone(phone)
        result = send_otp_code(phone, otp.code)
        return result


class OTPResendView(View):
    """ارسال مجدد کد OTP."""

    def post(self, request):
        register_data = request.session.get('register_data')
        if not register_data:
            messages.error(request, 'نشست منقضی شده است. لطفاً دوباره تلاش کنید.')
            return redirect('accounts:register')

        phone = register_data['phone_number']
        otp = OTPCode.create_for_phone(phone)
        result = send_otp_code(phone, otp.code)

        if result['success']:
            messages.success(request, 'کد جدید ارسال شد.')
        else:
            if settings.DEBUG:
                messages.warning(request, f'ارسال ناموفق. کد تست: {otp.code}')
            else:
                messages.error(request, 'ارسال کد تأیید ناموفق بود. کمی بعد دوباره تلاش کنید.')

        return redirect('accounts:otp_verify')


# ──────────────────────────────────────────────────────────────
# خروج
# ──────────────────────────────────────────────────────────────

class LogoutView(View):
    """خروج از سیستم — فقط با POST."""

    def post(self, request):
        logout(request)
        messages.info(request, 'با موفقیت از سیستم خارج شدید.')
        return redirect('courses:home')

    # جلوگیری از logout با GET (امنیتی)
    def get(self, request):
        return redirect('courses:home')


# ──────────────────────────────────────────────────────────────
# پروفایل
# ──────────────────────────────────────────────────────────────

class ProfileView(LoginRequiredMixin, View):
    """
    صفحه پروفایل کاربر.
    نمایش: اطلاعات شخصی + دوره‌های خریداری‌شده + تیکت‌های اخیر
    """

    template_name = 'profile.html'
    login_url = '/accounts/login/'

    def get(self, request):
        form = ProfileForm(instance=request.user)
        context = self._build_context(request, form, TicketCreateForm(user=request.user))
        return render(request, self.template_name, context)

    def post(self, request):
        if request.POST.get('action') == 'create_ticket':
            ticket_form = TicketCreateForm(request.POST, user=request.user)
            if ticket_form.is_valid():
                with transaction.atomic():
                    ticket = Ticket.objects.create(
                        user=request.user,
                        subject=ticket_form.cleaned_data['subject'],
                        course=ticket_form.cleaned_data['course'],
                    )
                    TicketMessage.objects.create(
                        ticket=ticket,
                        sender=request.user,
                        body=ticket_form.cleaned_data['body'],
                    )
                messages.success(request, 'تیکت شما با موفقیت ثبت شد.')
                return redirect(f"{reverse('accounts:profile')}#tab-tickets")

            context = self._build_context(
                request,
                ProfileForm(instance=request.user),
                ticket_form,
            )
            return render(request, self.template_name, context, status=400)

        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'پروفایل با موفقیت بروزرسانی شد.')
            return redirect('accounts:profile')

        context = self._build_context(request, form, TicketCreateForm(user=request.user))
        return render(request, self.template_name, context)

    def _build_context(self, request, form, ticket_form=None):
        """ساخت context صفحه پروفایل."""
        user = request.user

        enrollments = user.enrollments.filter(is_active=True).select_related(
            'course__category',
            'course__instructor',
        ).annotate(
            chapter_count=Count('course__chapters', distinct=True),
            lesson_count=Count('course__chapters__lessons', distinct=True),
        )
        tickets = user.tickets.select_related('course').prefetch_related(
            'messages__sender',
        ).order_by('-created_at')
        orders = user.orders.prefetch_related('items__course').order_by('-created_at')
        quiz_attempts = user.quiz_attempts.select_related(
            'quiz__chapter__course'
        ).order_by('-taken_at')
        quiz_stats = quiz_attempts.aggregate(average_score=Avg('score'))

        return {
            'form': form,
            'ticket_form': ticket_form or TicketCreateForm(user=user),
            'enrollments': enrollments,
            'enrollment_count': enrollments.count(),
            'recent_tickets': tickets[:10],
            'ticket_count': tickets.count(),
            'open_ticket_count': tickets.exclude(status='closed').count(),
            'orders': orders[:10],
            'order_count': orders.count(),
            'paid_order_count': orders.filter(status='paid').count(),
            'recent_quiz_attempts': quiz_attempts[:10],
            'quiz_average_score': quiz_stats['average_score'],
        }


class PasswordChangeView(LoginRequiredMixin, View):
    def post(self, request):
        form = PasswordChangeForm(request.user, request.POST)
        if not form.is_valid():
            messages.error(request, 'رمز عبور تغییر نکرد. رمز فعلی و مقادیر جدید را بررسی کنید.')
            return redirect(f"{reverse('accounts:profile')}#tab-security")
        user = form.save()
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)
        messages.success(request, 'رمز عبور با موفقیت تغییر کرد.')
        return redirect(f"{reverse('accounts:profile')}#tab-security")
