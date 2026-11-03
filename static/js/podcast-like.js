/* =========================================
پسندیدن اپیزود پادکست به‌صورت AJAX
(بدون رفرش صفحه؛ فقط قلب و شمارنده تغییر می‌کند)
========================================= */
(function () {
  "use strict";

  var forms = document.querySelectorAll(".podcast-like-form");
  if (!forms.length) return;

  var toFa = function (value) {
    return String(value).replace(/\d/g, function (digit) {
      return "۰۱۲۳۴۵۶۷۸۹"[Number(digit)];
    });
  };

  var paintButton = function (button, liked, count) {
    button.dataset.liked = liked ? "true" : "false";

    button.classList.toggle("border-red-200", liked);
    button.classList.toggle("bg-red-50", liked);
    button.classList.toggle("text-red-600", liked);
    button.classList.toggle("border-border", !liked);
    button.classList.toggle("bg-surface-container-low", !liked);
    button.classList.toggle("text-outline", !liked);

    var icon = button.querySelector(".podcast-like-icon");
    if (icon) {
      icon.textContent = "favorite";
      icon.style.fontVariationSettings = liked ? '"FILL" 1' : '"FILL" 0';
    }

    var counter = button.querySelector(".podcast-like-count");
    if (counter) counter.textContent = toFa(count);

    var label = liked ? "برداشتن پسندیدن" : "پسندیدن";
    button.setAttribute("aria-pressed", liked ? "true" : "false");
    button.setAttribute("aria-label", label);
    button.title = label;
  };

  Array.prototype.forEach.call(forms, function (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();

      var button = form.querySelector(".podcast-like-button");
      if (!button || button.disabled) return;

      button.disabled = true;

      window
        .fetch(form.action, {
          method: "POST",
          body: new FormData(form),
          headers: { "X-Requested-With": "XMLHttpRequest" },
          credentials: "same-origin",
        })
        .then(function (response) {
          if (response.status === 401) {
            window.location.href = form.dataset.loginUrl;
            return null;
          }
          if (!response.ok) throw new Error("request failed");
          return response.json();
        })
        .then(function (data) {
          if (!data) return;
          paintButton(button, Boolean(data.liked), data.like_count);
          if (window.showToast) window.showToast(data.message, data.level);
        })
        .catch(function () {
          if (window.showToast) {
            window.showToast("ثبت پسندیدن ناموفق بود؛ دوباره تلاش کنید.", "error");
          }
        })
        .finally(function () {
          button.disabled = false;
        });
    });
  });
})();
