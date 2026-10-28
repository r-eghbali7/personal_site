"""Views: tickets"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponseForbidden
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404

from .forms import TicketCreateForm, TicketReplyForm
from .models import Ticket, TicketMessage


class TicketListView(LoginRequiredMixin, View):
    def get(self, request):
        tickets = request.user.tickets.prefetch_related('messages').all()
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
            return redirect('tickets:detail', pk=pk)
        return render(request, 'ticket_detail.html', {
            'ticket': ticket,
            'form': form,
        }, status=400)
