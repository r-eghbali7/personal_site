"""
Forms: accounts

RegisterForm  — ثبت‌نام با موبایل + رمز عبور
LoginForm     — ورود با موبایل + رمز عبور
OTPVerifyForm — تأیید کد ۶ رقمی
ProfileForm   — ویرایش پروفایل
"""

import re
from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from .models import CustomUser


PHONE_VALIDATOR = RegexValidator(
    regex=r'^09[0-9]{9}$',
    message='شماره موبایل باید با ۰۹ شروع شود و ۱۱ رقم باشد.',
)


class RegisterForm(forms.Form):
    """فرم ثبت‌نام — نام fields باید با template یکسان باشد."""

    fullname = forms.CharField(
        max_length=150,
        label='نام و نام‌خانوادگی',
        error_messages={'required': 'نام و نام‌خانوادگی الزامی است.'},
    )
    mobile = forms.CharField(
        max_length=11,
        label='شماره موبایل',
        validators=[PHONE_VALIDATOR],
    )
    password = forms.CharField(
        min_length=8,
        label='رمز عبور',
        widget=forms.PasswordInput,
        error_messages={
            'required': 'رمز عبور الزامی است.',
            'min_length': 'رمز عبور باید حداقل ۸ کاراکتر باشد.',
        },
    )

    def clean_mobile(self):
        mobile = self.cleaned_data['mobile']
        if CustomUser.objects.filter(phone_number=mobile).exists():
            raise forms.ValidationError('این شماره موبایل قبلاً ثبت شده است.')
        return mobile

    def clean_password(self):
        password = self.cleaned_data['password']
        candidate_user = CustomUser(phone_number=self.cleaned_data.get('mobile', ''))
        try:
            validate_password(password, user=candidate_user)
        except ValidationError as error:
            raise forms.ValidationError(error.messages)
        return password


class LoginForm(forms.Form):
    """فرم ورود — موبایل + رمز عبور."""

    mobile = forms.CharField(
        max_length=11,
        label='شماره موبایل',
        validators=[PHONE_VALIDATOR],
    )
    password = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput,
        error_messages={'required': 'رمز عبور الزامی است.'},
    )

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        mobile = cleaned_data.get('mobile')
        password = cleaned_data.get('password')

        if mobile and password:
            user = authenticate(
                self.request,
                phone_number=mobile,
                password=password,
            )
            if user is None:
                raise forms.ValidationError('شماره موبایل یا رمز عبور اشتباه است.')
            if not user.is_active:
                raise forms.ValidationError('حساب کاربری شما غیرفعال شده است.')
            cleaned_data['user'] = user

        return cleaned_data

    def get_user(self):
        return self.cleaned_data.get('user')


class OTPRequestForm(forms.Form):
    """فرم درخواست ارسال کد OTP (گام اول فلوی OTP)."""

    mobile = forms.CharField(
        max_length=11,
        label='شماره موبایل',
        validators=[PHONE_VALIDATOR],
    )


class OTPVerifyForm(forms.Form):
    """فرم تأیید کد OTP (گام دوم فلوی OTP)."""

    code = forms.CharField(
        max_length=6,
        min_length=6,
        label='کد تأیید',
        error_messages={
            'required': 'کد تأیید الزامی است.',
            'min_length': 'کد باید ۶ رقم باشد.',
            'max_length': 'کد باید ۶ رقم باشد.',
        },
    )

    def clean_code(self):
        code = self.cleaned_data['code']
        if not code.isdigit():
            raise forms.ValidationError('کد باید فقط شامل اعداد باشد.')
        return code


class ProfileForm(forms.ModelForm):
    """فرم ویرایش پروفایل کاربر."""

    class Meta:
        model = CustomUser
        fields = ('full_name', 'email', 'avatar', 'bio')
        labels = {
            'full_name': 'نام و نام‌خانوادگی',
            'email': 'ایمیل',
            'avatar': 'تصویر پروفایل',
            'bio': 'درباره من',
        }
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }
