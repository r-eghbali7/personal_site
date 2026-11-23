/*
 * واترمارک ویدیو: شماره موبایل خریدار را روی تصویر ویدیو نمایش می‌دهد و
 * هر ۵ ثانیه جایش را تغییر می‌دهد (برای حفظ حق نشر در برابر ضبط صفحه).
 *
 * علاوه بر واترمارک:
 *   - دکمه‌ی تمام‌صفحه می‌سازد که کل ناحیه‌ی ویدیو را تمام‌صفحه می‌کند،
 *     بنابراین واترمارک در حالت تمام‌صفحه هم دیده می‌شود.
 *   - منوی کلیک راست، درگ کردن و دکمه‌ی دانلود پخش‌کننده را غیرفعال می‌کند.
 *
 * استفاده در قالب:
 *   <video controls data-watermark="{{ request.user.phone_number }}">...</video>
 */
(function () {
  "use strict";

  var STEP_MS = 5000; // فاصله جابه‌جایی
  var PADDING = 12; // فاصله از لبه‌های ویدیو
  var STYLE_ID = "video-watermark-style";
  // آیکون‌ها به‌صورت SVG درون‌خطی هستند تا مستقل از فونت آیکون نمایش داده شوند.
  var ICON_FULL =
    '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false">' +
    '<path fill="currentColor" d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>' +
    "</svg>";
  var ICON_EXIT =
    '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false">' +
    '<path fill="currentColor" d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/>' +
    "</svg>";

  var STYLE =
    ".vw-frame{position:relative;display:block;line-height:0;max-width:100%}" +
    ".video-watermark{" +
    "position:absolute;z-index:30;pointer-events:none;user-select:none;" +
    "margin:0;padding:3px 8px;border-radius:6px;" +
    "font-family:Vazirmatn,system-ui,sans-serif;font-size:13px;font-weight:600;" +
    "letter-spacing:.6px;line-height:20px;direction:ltr;white-space:nowrap;" +
    "color:rgba(255,255,255,.78);background:rgba(0,0,0,.22);" +
    "text-shadow:0 1px 3px rgba(0,0,0,.9);" +
    "opacity:0;transition:left .4s ease,top .4s ease,opacity .3s ease;" +
    "}" +
    ".video-watermark.is-visible{opacity:1}" +
    ".video-fs{" +
    "position:absolute;top:8px;left:8px;z-index:31;display:flex;align-items:center;" +
    "justify-content:center;width:36px;height:36px;padding:0;border:0;border-radius:8px;" +
    "background:rgba(0,0,0,.45);color:#fff;line-height:1;cursor:pointer;" +
    "opacity:.8;transition:opacity .2s ease,background .2s ease;" +
    "}" +
    ".video-fs:hover,.video-fs:focus-visible{opacity:1;background:rgba(0,0,0,.72)}" +
    ".video-fs svg{display:block;width:20px;height:20px;fill:currentColor}" +
    ".vw-frame:fullscreen{background:#000;display:flex;align-items:center;" +
    "justify-content:center;border-radius:0}" +
    ".vw-frame:fullscreen video{width:100%;height:100%;max-height:100%!important;" +
    "object-fit:contain;border-radius:0!important}" +
    ".vw-frame:-webkit-full-screen{background:#000;display:flex;align-items:center;" +
    "justify-content:center;border-radius:0}" +
    ".vw-frame:-webkit-full-screen video{width:100%;height:100%;max-height:100%!important;" +
    "object-fit:contain;border-radius:0!important}" +
    "video[data-watermark]::-webkit-media-controls-fullscreen-button{display:none!important}" +
    "video[data-watermark]::-webkit-media-controls-download-button{display:none!important}" +
    "@media print{.video-watermark,.video-fs{display:none!important}}";

  function injectStyle() {
    if (document.getElementById(STYLE_ID)) return;
    var style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = STYLE;
    (document.head || document.documentElement).appendChild(style);
  }

  function fullscreenElement() {
    return (
      document.fullscreenElement || document.webkitFullscreenElement || null
    );
  }

  function exitFullscreen() {
    var exit = document.exitFullscreen || document.webkitExitFullscreen;
    if (exit) exit.call(document);
  }

  function attach(video) {
    var label = (video.getAttribute("data-watermark") || "").trim();
    if (!label || video.getAttribute("data-vw-ready") === "1") return;
    video.setAttribute("data-vw-ready", "1");

    var parent = video.parentElement;
    if (!parent) return;

    // قاب اختصاصی ویدیو تا تمام‌صفحه‌شدن، واترمارک را هم شامل شود.
    var frame = document.createElement("div");
    frame.className = "vw-frame";
    parent.insertBefore(frame, video);
    frame.appendChild(video);

    var badge = document.createElement("span");
    badge.className = "video-watermark";
    badge.setAttribute("aria-hidden", "true");
    badge.textContent = label;
    frame.appendChild(badge);

    var button = document.createElement("button");
    button.type = "button";
    button.className = "video-fs";
    button.setAttribute("aria-label", "تمام‌صفحه");
    button.innerHTML = ICON_FULL;
    frame.appendChild(button);

    // جلوگیری از ذخیره/دانلود ساده‌ی ویدیو
    video.setAttribute("controlslist", "nodownload");
    video.addEventListener("contextmenu", function (event) {
      event.preventDefault();
    });
    video.addEventListener("dragstart", function (event) {
      event.preventDefault();
    });

    var timer = null;
    var visible = false;
    var lastX = -1;
    var lastY = -1;

    // موقعیت تصادفی جدید، نسبت به ناحیه‌ی خود ویدیو (نه نوار کنترل‌ها).
    function move() {
      var frameRect = frame.getBoundingClientRect();
      var videoRect = video.getBoundingClientRect();
      var badgeRect = badge.getBoundingClientRect();

      var maxX = videoRect.width - badgeRect.width - PADDING;
      var maxY = videoRect.height - badgeRect.height - PADDING;
      if (maxX <= PADDING || maxY <= PADDING) return;

      var x = PADDING;
      var y = PADDING;
      for (var i = 0; i < 8; i++) {
        var nextX = PADDING + Math.random() * (maxX - PADDING);
        var nextY = PADDING + Math.random() * (maxY - PADDING);
        x = nextX;
        y = nextY;
        var farEnough =
          Math.abs(nextX - lastX) > maxX * 0.3 ||
          Math.abs(nextY - lastY) > maxY * 0.3;
        if (lastX < 0 || farEnough) break;
      }
      lastX = x;
      lastY = y;

      badge.style.left =
        videoRect.left - frameRect.left + frame.scrollLeft + x + "px";
      badge.style.top =
        videoRect.top - frameRect.top + frame.scrollTop + y + "px";
    }

    function start() {
      if (!visible) {
        move();
        badge.classList.add("is-visible");
        visible = true;
      }
      if (timer) window.clearInterval(timer);
      timer = window.setInterval(move, STEP_MS);
    }

    function stop() {
      if (timer) {
        window.clearInterval(timer);
        timer = null;
      }
    }

    function toggleFullscreen() {
      if (fullscreenElement() === frame) {
        exitFullscreen();
        return;
      }
      if (frame.requestFullscreen) {
        var request = frame.requestFullscreen();
        if (request && request.catch) {
          request.catch(function () {
            if (video.webkitEnterFullscreen) video.webkitEnterFullscreen();
          });
        }
      } else if (frame.webkitRequestFullscreen) {
        frame.webkitRequestFullscreen();
      } else if (video.webkitEnterFullscreen) {
        // iOS: فقط تمام‌صفحه‌ی بومی خود ویدیو در دسترس است.
        video.webkitEnterFullscreen();
      }
    }

    button.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      toggleFullscreen();
    });

    function syncFullscreen() {
      button.innerHTML = fullscreenElement() === frame ? ICON_EXIT : ICON_FULL;
      button.setAttribute(
        "aria-label",
        fullscreenElement() === frame ? "خروج از تمام‌صفحه" : "تمام‌صفحه"
      );
      if (visible) move();
    }

    document.addEventListener("fullscreenchange", syncFullscreen);
    document.addEventListener("webkitfullscreenchange", syncFullscreen);

    video.addEventListener("play", start);
    video.addEventListener("playing", start);
    video.addEventListener("pause", stop);
    video.addEventListener("ended", stop);
    video.addEventListener("loadedmetadata", function () {
      if (visible) move();
    });

    if (!video.paused && !video.ended) start();

    window.addEventListener("resize", function () {
      if (visible) move();
    });
  }

  function init() {
    injectStyle();
    var videos = document.querySelectorAll("video[data-watermark]");
    for (var i = 0; i < videos.length; i++) attach(videos[i]);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
