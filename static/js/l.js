document.addEventListener("DOMContentLoaded", () => {
    // گرفتن اینپوت سرچ هدر
    const headerSearchInput = document.querySelector('[data-site-search]');
    const headerSearchResults = document.querySelector('[data-site-search-results]');
    const coursesGrid = document.querySelector('main.flex.flex-col'); // کانتینر اصلی دوره‌ها را اینجا انتخاب کنید

    if(headerSearchInput && coursesGrid) {
        let debounceTimer;
        
        headerSearchInput.addEventListener('input', (e) => {
            e.stopPropagation(); // جلوگیری از اجرای اسکریپت site-header.js
            if(headerSearchResults) headerSearchResults.hidden = true; // مخفی نگه داشتن پاپ‌آپ هدر
            
            clearTimeout(debounceTimer);
            const query = e.target.value.trim();
            
            debounceTimer = setTimeout(async () => {
                const response = await fetch(`/courses/courses/?q=${query}`, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                const data = await response.json();
                
                // رندر کردن مجدد گرید دوره‌ها
                if(data.courses && data.courses.length > 0) {
                    coursesGrid.innerHTML = data.courses.map(course => `
                        <div class="border p-4 rounded-md">
                            <h3><a href="/courses/${course.slug}/">${course.title}</a></h3>
                            <p>${course.price == '0' ? 'رایگان' : course.price + ' تومان'}</p>
                        </div>
                    `).join('');
                } else {
                    coursesGrid.innerHTML = '<p class="p-4">دوره‌ای برای این جستجو پیدا نشد.</p>';
                }
            }, 300);
        }, true); // Use capture phase
    }
});
