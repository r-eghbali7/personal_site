"""Views: tickets (stub)"""
from django.views import View
from django.shortcuts import render, redirect


class TicketListView(View):
    def get(self, request):
        return render(request, 'ticket_list.html')


class TicketCreateView(View):
    def get(self, request):
        return render(request, 'ticket_create.html')

    def post(self, request):
        return redirect('tickets:list')


class TicketDetailView(View):
    def get(self, request, pk):
        return render(request, 'ticket_detail.html')

    def post(self, request, pk):
        return redirect('tickets:detail', pk=pk)
