from django.db import migrations, models
from django.db.models import Q


INCLUDED_FEATURES = [
    {'icon': 'videocam', 'text': '۵۸ ساعت آموزش ویدیویی عمیق با کیفیت 4K'},
    {'icon': 'support', 'text': 'پشتیبانی مستقیم و تیکتینگ توسط مهندس طاهری'},
    {'icon': 'sync', 'text': 'دسترسی همیشگی به تمام آپدیت‌های آینده Next.js'},
    {'icon': 'terminal', 'text': 'مخزن خصوصی گیت‌هاب با تمام کامیت‌های آموزشی'},
    {'icon': 'assignment_turned_in', 'text': 'تمرین‌های هفتگی و آزمون‌های آنلاین سنجش مهارت'},
    {'icon': 'workspace_premium', 'text': 'اعطای گواهینامه معتبر با کد رهگیری بین‌المللی'},
]


def populate_course_detail_content(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    Course.objects.filter(
        Q(title__icontains='next') | Q(slug__icontains='next')
    ).update(
        detail_badge='آپدیت ۲۰۲۵ (Next.js 15.2 Ready)',
        level_description='متوسط تا Senior',
        project_focus='پروژه‌محور و انترپرایز',
        language='فارسی روان',
        prerequisites='تسلط نسبی بر JavaScript ES6+',
        access_details='مادام‌العمر به محتوا و سورس‌کد گیت‌هاب',
        included_features=INCLUDED_FEATURES,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_course_intro_video'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='detail_badge',
            field=models.CharField(blank=True, max_length=100, verbose_name='برچسب صفحه جزئیات'),
        ),
        migrations.AddField(
            model_name='course',
            name='level_description',
            field=models.CharField(blank=True, max_length=100, verbose_name='شرح سطح دوره'),
        ),
        migrations.AddField(
            model_name='course',
            name='project_focus',
            field=models.CharField(blank=True, max_length=100, verbose_name='نوع پروژه‌های دوره'),
        ),
        migrations.AddField(
            model_name='course',
            name='language',
            field=models.CharField(blank=True, max_length=100, verbose_name='زبان دوره'),
        ),
        migrations.AddField(
            model_name='course',
            name='prerequisites',
            field=models.TextField(blank=True, verbose_name='پیش‌نیازهای دوره'),
        ),
        migrations.AddField(
            model_name='course',
            name='access_details',
            field=models.TextField(blank=True, verbose_name='جزئیات دسترسی دوره'),
        ),
        migrations.AddField(
            model_name='course',
            name='included_features',
            field=models.JSONField(blank=True, default=list, help_text='فهرستی از موارد با کلیدهای icon و text.', verbose_name='موارد شامل دوره'),
        ),
        migrations.RunPython(populate_course_detail_content, migrations.RunPython.noop),
    ]
