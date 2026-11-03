/* =========================================
پیام‌های شناور (Toast)
پیام‌های سرور در قالب رندر می‌شوند؛ این فایل بستن و حذف خودکار را مدیریت می‌کند
و showToast را برای پیام‌های AJAX در اختیار صفحات می‌گذارد.
========================================= */
(function () {
  "use strict";

  var container = document.getElementById("toast-container");
  if (!container) return;

  var LEVELS = {
    success: {
      icon: "check_circle",
      box: "border-green-200 bg-green-50 text-green-900",
      iconClass: "text-green-600",
    },
    error: {
      icon: "error",
      box: "border-red-200 bg-red-50 text-red-900",
      iconClass: "text-red-600",
    },
    warning: {
      icon: "warning",
      box: "border-amber-200 bg-amber-50 text-amber-900",
      iconClass: "text-amber-600",
    },
    info: {
      icon: "info",
      box: "border-sky-200 bg-sky-50 text-sky-900",
      iconClass: "text-sky-600",
    },
    debug: {
      icon: "bug_report",
      box: "border-border bg-card text-on-surface",
      iconClass: "text-outline",
    },
  };

  var dismissToast = function (toast) {
    toast.classList.add("toast-leaving");
    window.setTimeout(function () {
      toast.remove();
    }, 320);
  };

  var activateToast = function (toast, timeout) {
    var timer = window.setTimeout(function () {
      dismissToast(toast);
    }, timeout || 6500);

    var close = toast.querySelector(".toast-close");
    if (close) {
      close.addEventListener("click", function () {
        window.clearTimeout(timer);
        dismissToast(toast);
      });
    }

    toast.addEventListener("mouseenter", function () {
      window.clearTimeout(timer);
    });

    toast.addEventListener("mouseleave", function () {
      timer = window.setTimeout(function () {
        dismissToast(toast);
      }, 3000);
    });
  };

  var buildToast = function (text, level) {
    var config = LEVELS[level] || LEVELS.info;

    var toast = document.createElement("div");
    toast.className =
      "toast pointer-events-auto flex w-full items-start gap-3 rounded-2xl border px-4 py-3 shadow-xl backdrop-blur-sm";
    config.box.split(" ").forEach(function (className) {
      toast.classList.add(className);
    });
    toast.setAttribute("role", "status");

    var icon = document.createElement("span");
    icon.className = "material-symbols-outlined text-[22px] shrink-0 " + config.iconClass;
    icon.textContent = config.icon;
    icon.style.fontVariationSettings = '"FILL" 1';

    var body = document.createElement("p");
    body.className = "flex-1 text-body-sm leading-6";
    body.textContent = text;

    var close = document.createElement("button");
    close.type = "button";
    close.className = "toast-close shrink-0 text-outline hover:text-on-surface transition-colors";
    close.setAttribute("aria-label", "بستن پیام");
    close.innerHTML = '<span class="material-symbols-outlined text-[18px]">close</span>';

    toast.appendChild(icon);
    toast.appendChild(body);
    toast.appendChild(close);
    return toast;
  };

  var showToast = function (text, level, timeout) {
    if (!text) return null;
    var toast = buildToast(text, level);
    container.appendChild(toast);
    activateToast(toast, timeout);
    return toast;
  };

  window.showToast = showToast;

  Array.prototype.forEach.call(container.querySelectorAll(".toast"), function (toast) {
    activateToast(toast, 6500);
  });
})();
