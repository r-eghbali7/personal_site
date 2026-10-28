"""Seed script: populate sample data for all apps."""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from accounts.models import CustomUser
from courses.models import Category, Course, Chapter, Lesson, Quiz, Question, Choice, Enrollment, FinalProject
from blog.models import BlogPost, Comment
from orders.models import Cart, CartItem, Order, OrderItem, Transaction
from tickets.models import Ticket, TicketMessage

User = get_user_model()

# Users
admin, _ = CustomUser.objects.get_or_create(phone_number='09120000000', defaults={'full_name':'ادمین سیستم','is_staff':True,'is_superuser':True,'is_active':True})
admin.set_password('admin1234'); admin.save()
student, _ = CustomUser.objects.get_or_create(phone_number='09123456789', defaults={'full_name':'دانشجوی نمونه','is_active':True})
student.set_password('student1234'); student.save()
instructor, _ = CustomUser.objects.get_or_create(phone_number='09129876543', defaults={'full_name':'مدرس نمونه','is_active':True})
instructor.set_password('teacher1234'); instructor.save()

# Categories
cat1, _ = Category.objects.get_or_create(name='برنامه‌نویسی وب', defaults={'slug':'web-dev','icon':'code'})
cat2, _ = Category.objects.get_or_create(name='هوش مصنوعی', defaults={'slug':'ai','icon':'psychology'})

# Courses
course1, _ = Course.objects.get_or_create(title='دوره جنگو پیشرفته', slug='django-advanced', defaults={'short_description':'آموزش جنگو','description':'توضیحات کامل دوره','price':1500000,'level':'advanced','is_published':True,'category':cat1,'instructor':instructor})
course2, _ = Course.objects.get_or_create(title='دوره رایگان پایتون', slug='python-free', defaults={'short_description':'پایتون مقدماتی','description':'توضیحات','price':0,'level':'beginner','is_published':True,'category':cat1,'instructor':instructor})

# Chapters & lessons
ch1, _ = Chapter.objects.get_or_create(course=course1, title='فصل اول', defaults={'order':1})
Lesson.objects.get_or_create(chapter=ch1, title='جلسه ۱', defaults={'order':1,'duration_seconds':600,'is_free_preview':True})
Quiz.objects.get_or_create(chapter=ch1, defaults={'title':'آزمون فصل ۱','pass_score':70})
q = Quiz.objects.get(chapter=ch1)
ques, _ = Question.objects.get_or_create(quiz=q, body='جنگو چیست؟', defaults={'order':1})
Choice.objects.get_or_create(question=ques, text='فریمورک پایتون', defaults={'is_correct':True})
Choice.objects.get_or_create(question=ques, text='زبان برنامه‌نویسی', defaults={'is_correct':False})
FinalProject.objects.get_or_create(course=course1, defaults={'title':'پروژه نهایی','description':'توضیح پروژه','deadline_days':30})

# Enrollment
Enrollment.objects.get_or_create(user=student, course=course1, defaults={'is_active':True})

# Blog
post, _ = BlogPost.objects.get_or_create(title='مقاله نمونه', slug='sample-post', defaults={'summary':'خلاصه','content':'محتوا','author':instructor,'category':'بک‌اند','is_published':True,'published_at':timezone.now()})
Comment.objects.get_or_create(post=post, user=student, body='نظر نمونه', defaults={'is_approved':True})

# Tickets
ticket, _ = Ticket.objects.get_or_create(user=student, subject='مشکل در دوره', defaults={'status':'open','priority':'medium'})
TicketMessage.objects.get_or_create(ticket=ticket, sender=student, body='پیام نمونه')

# Orders
order, _ = Order.objects.get_or_create(user=student, total_amount=1500000, defaults={'status':'paid'})
OrderItem.objects.get_or_create(order=order, course=course1, defaults={'price':1500000})
Transaction.objects.get_or_create(order=order, authority='AUTH123', defaults={'status':'success','amount':15000000})
Cart.objects.get_or_create(user=student)

print('Seed done.')
