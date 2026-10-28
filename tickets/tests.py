from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from .models import Ticket, TicketMessage


class TicketFlowTests(TestCase):
	def setUp(self):
		self.user = CustomUser.objects.create_user(
			phone_number='09121112222',
			password='test-password-123',
		)
		self.other_user = CustomUser.objects.create_user(
			phone_number='09123334444',
			password='test-password-123',
		)

	def test_create_ticket_creates_first_message(self):
		self.client.force_login(self.user)
		response = self.client.post(reverse('tickets:create'), {
			'subject': 'Cannot access course',
			'body': 'The lesson page returns an error.',
			'course': '',
		})

		ticket = Ticket.objects.get(user=self.user)
		self.assertRedirects(response, reverse('tickets:detail', kwargs={'pk': ticket.pk}))
		self.assertEqual(ticket.messages.count(), 1)
		self.assertEqual(ticket.messages.get().sender, self.user)

	def test_ticket_pages_render_and_require_authentication(self):
		self.assertEqual(self.client.get(reverse('tickets:list')).status_code, 302)
		self.client.force_login(self.user)

		self.assertEqual(self.client.get(reverse('tickets:list')).status_code, 200)
		self.assertEqual(self.client.get(reverse('tickets:create')).status_code, 200)

	def test_ticket_detail_is_owner_scoped_and_replies_persist(self):
		ticket = Ticket.objects.create(user=self.user, subject='Support request')
		TicketMessage.objects.create(ticket=ticket, sender=self.user, body='Initial message')
		self.client.force_login(self.other_user)

		self.assertEqual(self.client.get(reverse('tickets:detail', kwargs={'pk': ticket.pk})).status_code, 404)

		self.client.force_login(self.user)
		response = self.client.post(
			reverse('tickets:detail', kwargs={'pk': ticket.pk}),
			{'body': 'Additional details'},
		)
		self.assertRedirects(response, reverse('tickets:detail', kwargs={'pk': ticket.pk}))
		self.assertEqual(ticket.messages.count(), 2)

# Create your tests here.
