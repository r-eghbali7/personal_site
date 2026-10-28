from django import forms

from courses.models import Course


class TicketCreateForm(forms.Form):
    subject = forms.CharField(max_length=300, label='موضوع')
    body = forms.CharField(min_length=5, label='شرح درخواست', widget=forms.Textarea)
    course = forms.ModelChoiceField(queryset=Course.objects.none(), required=False, label='دوره مرتبط')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and user.is_authenticated:
            self.fields['course'].queryset = Course.objects.filter(
                is_published=True,
                enrollments__user=user,
                enrollments__is_active=True,
            ).distinct()


class TicketReplyForm(forms.Form):
    body = forms.CharField(min_length=1, label='پاسخ', widget=forms.Textarea)