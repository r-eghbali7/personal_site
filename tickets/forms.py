from django import forms

from courses.models import Course


class TicketCreateForm(forms.Form):
    subject = forms.CharField(max_length=300, label='موضوع')
    body = forms.CharField(min_length=5, label='شرح درخواست', widget=forms.Textarea)
    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(is_published=True),
        required=False,
        label='دوره مرتبط',
    )


class TicketReplyForm(forms.Form):
    body = forms.CharField(min_length=1, label='پاسخ', widget=forms.Textarea)