"""بهینه‌سازی تصاویر موجود در MEDIA_ROOT (کاهش اندازه برای سرعت بارگذاری).

این دستور برای اصلاح تصاویر آپلودشده‌ی قبلی است: عرض تصویر را به ``--max-width``
محدود می‌کند و فایل را با کیفیت معقول دوباره ذخیره می‌کند، فقط اگر خروجی از
فایل فعلی کوچک‌تر باشد. بدون ``--apply`` فقط گزارش می‌دهد.
"""

import io
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from PIL import Image

SUPPORTED_SUFFIXES = {'.webp', '.jpg', '.jpeg', '.png'}


class Command(BaseCommand):
    help = 'تصاویر media را تغییر اندازه و فشرده می‌کند تا حجم صفحه کاهش یابد.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            default=str(settings.MEDIA_ROOT),
            help='مسیر شروع جست‌وجو (پیش‌فرض: MEDIA_ROOT)',
        )
        parser.add_argument('--max-width', type=int, default=1600, help='حداکثر عرض تصویر')
        parser.add_argument('--quality', type=int, default=78, help='کیفیت خروجی WebP/JPEG')
        parser.add_argument(
            '--apply',
            action='store_true',
            help='تغییرات را روی فایل‌ها اعمال کن (بدون این گزینه فقط گزارش می‌دهد).',
        )

    def handle(self, *args, **options):
        root = Path(options['path'])
        if not root.exists():
            raise CommandError(f'مسیر پیدا نشد: {root}')

        max_width = options['max_width']
        quality = options['quality']
        apply_changes = options['apply']
        total_before = total_after = 0
        touched = 0

        for file_path in sorted(root.rglob('*')):
            if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            before = file_path.stat().st_size
            payload = self._optimize(file_path, max_width, quality)
            if payload is None:
                continue
            total_before += before
            total_after += len(payload)
            touched += 1
            self.stdout.write(
                f"{file_path.relative_to(root)}: {before // 1024} KiB -> {len(payload) // 1024} KiB"
            )
            if apply_changes:
                file_path.write_bytes(payload)

        saved = total_before - total_after
        self.stdout.write(
            self.style.SUCCESS(
                f'{touched} تصویر، {total_before // 1024} KiB -> {total_after // 1024} KiB '
                f'(صرفه‌جویی {saved // 1024} KiB)'
            )
        )
        if not apply_changes and touched:
            self.stdout.write('برای اعمال تغییرات همین دستور را با --apply اجرا کنید.')

    def _optimize(self, file_path, max_width, quality):
        """نسخه‌ی بهینه‌ی تصویر را برمی‌گرداند یا اگر سودی نداشت None."""
        try:
            with Image.open(file_path) as image:
                image.load()
                source = image.copy()
        except Exception as exc:  # noqa: BLE001 - فایل خراب نباید کل دستور را متوقف کند
            self.stderr.write(f'رد شد {file_path}: {exc}')
            return None

        width, height = source.size
        if width > max_width:
            new_height = max(1, round(height * max_width / width))
            source = source.resize((max_width, new_height), Image.LANCZOS)

        buffer = io.BytesIO()
        suffix = file_path.suffix.lower()
        try:
            if suffix == '.webp':
                source.save(buffer, format='WEBP', quality=quality, method=6)
            elif suffix == '.png':
                if source.mode not in ('RGB', 'RGBA'):
                    source = source.convert('RGBA')
                source.save(buffer, format='PNG', optimize=True)
            else:
                if source.mode != 'RGB':
                    source = source.convert('RGB')
                source.save(buffer, format='JPEG', quality=quality, optimize=True, progressive=True)
        except Exception as exc:  # noqa: BLE001
            self.stderr.write(f'خطا در ذخیره {file_path}: {exc}')
            return None

        payload = buffer.getvalue()
        if len(payload) >= file_path.stat().st_size:
            return None
        return payload
