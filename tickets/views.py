"""Views: tickets"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponseForbidden, JsonResponse
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone

from .forms import TicketCreateForm, TicketReplyForm
from .models import Ticket, TicketMessage, ConsultationRequest


class TicketListView(LoginRequiredMixin, View):
    def get(self, request):
        tickets = request.user.tickets.annotate(
            message_count=Count('messages'),
        )
        return render(request, 'ticket_list.html', {'tickets': tickets})


class TicketCreateView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'ticket_create.html', {'form': TicketCreateForm(user=request.user)})

    def post(self, request):
        form = TicketCreateForm(request.POST, user=request.user)
        if not form.is_valid():
            return render(request, 'ticket_create.html', {'form': form}, status=400)
        with transaction.atomic():
            ticket = Ticket.objects.create(
                user=request.user,
                subject=form.cleaned_data['subject'],
                course=form.cleaned_data['course'],
            )
            TicketMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                body=form.cleaned_data['body'],
            )
        messages.success(request, 'تیکت شما با موفقیت ثبت شد.')
        return redirect('tickets:detail', pk=ticket.pk)


class TicketDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        ticket = get_object_or_404(
            Ticket.objects.prefetch_related('messages__sender'),
            pk=pk,
            user=request.user,
        )
        return render(request, 'ticket_detail.html', {
            'ticket': ticket,
            'form': TicketReplyForm(),
        })

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        if ticket.user_id != request.user.id:
            return HttpResponseForbidden('دسترسی به این تیکت مجاز نیست.')
        if ticket.status == 'closed':
            return HttpResponseForbidden('این تیکت بسته شده است.')
        form = TicketReplyForm(request.POST)
        if form.is_valid():
            TicketMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                body=form.cleaned_data['body'],
            )
            messages.success(request, 'پاسخ شما ثبت شد.')
            return redirect('tickets:detail', pk=pk)
        return render(request, 'ticket_detail.html', {
            'ticket': ticket,
            'form': form,
        }, status=400)


@method_decorator(csrf_protect, name='dispatch')
class ConsultationRequestView(View):
    """ثبت درخواست مشاوره اختصاصی از طریق AJAX (ثبت نهایی پس از تایید OTP)."""

    def post(self, request):
        full_name = (request.POST.get('full_name') or '').strip()
        phone_number = (request.POST.get('phone_number') or '').strip()
        message = (request.POST.get('message') or '').strip()

        if not full_name:
            return JsonResponse(
                {'success': False, 'error': 'نام و نام خانوادگی الزامی است.'},
                status=400,
            )
        if not phone_number:
            return JsonResponse(
                {'success': False, 'error': 'شماره موبایل الزامی است.'},
                status=400,
            )

        # تایید اینکه شماره موبایل از طریق OTP تایید شده باشد
        verified_phones = request.session.get('consultation_verified_phones', {})
        if not verified_phones.get(phone_number):
            return JsonResponse(
                {
                    'success': False,
                    'error': 'شماره موبایل از طریق کد تأیید تایید نشده است.',
                },
                status=400,
            )

        ConsultationRequest.objects.create(
            full_name=full_name,
            phone_number=phone_number,
            message=message,
        )
        # علامت تایید را پس از ثبت پاک کنید تا یکبار استفاده شود
        verified_phones.pop(phone_number, None)
        request.session['consultation_verified_phones'] = verified_phones
        return JsonResponse(
            {
                'success': True,
                'message': 'درخواست شما با موفقیت ثبت شد و به‌زودی با شما تماس خواهیم گرفت.',
            }
        )


@method_decorator(csrf_protect, name='dispatch')
class SendOTPView(View):
    """ارسال کد OTP به شماره موبایل کاربر برای تایید درخواست مشاوره."""

    def post(self, request):
        from accounts.models import OTPCode
        from accounts.services import send_otp_code

        phone_number = (request.POST.get('phone_number') or '').strip()
        if not phone_number:
            return JsonResponse(
                {'success': False, 'error': 'شماره موبایل الزامی است.'},
                status=400,
            )

        otp = OTPCode.create_for_phone(phone_number)
        result = send_otp_code(phone_number, otp.code)
        if result['success']:
            # ذخیره شماره در session تا در مرحله تایید شناخته شود
            pending = request.session.get('consultation_pending_otp', {})
            pending[phone_number] = True
            request.session['consultation_pending_otp'] = pending
            return JsonResponse(
                {
                    'success': True,
                    'message': 'کد تایید به شماره موبایل شما ارسال شد.',
                }
            )
        return JsonResponse(
            {'success': False, 'error': result['message']}, status=400
        )


@method_decorator(csrf_protect, name='dispatch')
class VerifyOTPView(View):
    """تایید کد OTP دریافت‌شده از کاربر."""

    def post(self, request):
        from accounts.services import verify_otp_code

        phone_number = (request.POST.get('phone_number') or '').strip()
        code = (request.POST.get('code') or '').strip()

        if not phone_number or not code:
            return JsonResponse(
                {'success': False, 'error': 'شماره موبایل و کد تایید الزامی هستند.'},
                status=400,
            )

        pending = request.session.get('consultation_pending_otp', {})
        if not pending.get(phone_number):
            return JsonResponse(
                {
                    'success': False,
                    'error': 'ابتدا کد تایید برای این شماره درخواست دهید.',
                },
                status=400,
            )

        result = verify_otp_code(phone_number, code)
        if not result['success']:
            return JsonResponse(
                {'success': False, 'error': result['message']}, status=400
            )

        # علامت تایید شماره در session
        verified = request.session.get('consultation_verified_phones', {})
        verified[phone_number] = True
        request.session['consultation_verified_phones'] = verified

        # حذف از انتظار OTP
        pending.pop(phone_number, None)
        request.session['consultation_pending_otp'] = pending

        return JsonResponse(
            {'success': True, 'message': 'شماره موبایل با موفقیت تایید شد.'}
        )
