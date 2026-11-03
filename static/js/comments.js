/* =========================================
ارسال دیدگاه با AJAX در دوره، مقاله و پادکست
(بدون رفرش صفحه؛ دیدگاه جدید و شمارنده‌ها همان‌جا به‌روز می‌شوند)
========================================= */
(function () {
  "use strict";

  var forms = document.querySelectorAll(".ajax-comment-form");
  if (!forms.length) return;

  var toFa = function (value) {
    return String(value).replace(/\d/g, function (digit) {
      return "۰۱۲۳۴۵۶۷۸۹"[Number(digit)];
    });
  };

  var notify = function (message, level) {
    if (window.showToast) window.showToast(message, level || "info");
  };

  var updateCounters = function (form, count) {
    if (count === undefined || count === null) return;
    var ids = (form.dataset.countIds || "").split(",");
    ids.forEach(function (id) {
      var element = document.getElementById(id.trim());
      if (element) element.textContent = toFa(count);
    });
  };

  Array.prototype.forEach.call(forms, function (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();

      var button = form.querySelector('button[type="submit"]') || form.querySelector("button");
      if (button && button.disabled) return;
      if (button) button.disabled = true;

      window
        .fetch(form.action, {
          method: "POST",
          body: new FormData(form),
          headers: { "X-Requested-With": "XMLHttpRequest" },
          credentials: "same-origin",
        })
        .then(function (response) {
          return response
            .json()
            .catch(function () {
              return {};
            })
            .then(function (data) {
              return { status: response.status, ok: response.ok, data: data };
            });
        })
        .then(function (result) {
          if (result.status === 401) {
            window.location.href = form.dataset.loginUrl || "/accounts/login/";
            return;
          }

          if (!result.ok || result.data.error) {
            notify(result.data.error || "ارسال دیدگاه ناموفق بود؛ دوباره تلاش کنید.", "error");
            return;
          }

          var textarea = form.querySelector("textarea");
          if (textarea) textarea.value = "";

          if (form.dataset.listId && result.data.html) {
            var list = document.getElementById(form.dataset.listId);
            if (list) {
              var emptyState = list.querySelector(".comment-empty");
              if (emptyState) emptyState.remove();
              list.insertAdjacentHTML("afterbegin", result.data.html);
            }
          }

          updateCounters(form, result.data.comment_count);
          notify(result.data.message || "دیدگاه شما ثبت شد.", result.data.level || "success");
        })
        .catch(function () {
          notify("ارسال دیدگاه ناموفق بود؛ دوباره تلاش کنید.", "error");
        })
        .finally(function () {
          if (button) button.disabled = false;
        });
    });
  });
})();
