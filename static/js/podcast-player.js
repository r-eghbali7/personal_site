/* =========================================
پخش‌کننده اپیزودهای پادکست
نوار پیشرفت، پرش ۱۰ ثانیه‌ای و سرعت پخش
========================================= */
(function () {
  "use strict";

  var SPEEDS = [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2];

  var toFa = function (value) {
    return String(value)
      .replace(/\d/g, function (digit) {
        return "۰۱۲۳۴۵۶۷۸۹"[Number(digit)];
      })
      .replace(".", "٫");
  };

  var formatTime = function (seconds) {
    var total = Number.isFinite(seconds) && seconds > 0 ? Math.floor(seconds) : 0;
    var minutes = Math.floor(total / 60);
    var rest = total % 60;
    return toFa(minutes + ":" + String(rest).padStart(2, "0"));
  };

  var cards = Array.prototype.slice.call(document.querySelectorAll(".podcast-card"));
  if (!cards.length) return;

  var pauseOthers = function (activeCard) {
    cards.forEach(function (card) {
      if (card === activeCard) return;
      var audio = card.querySelector(".podcast-audio");
      var icon = card.querySelector(".podcast-play-icon");
      if (audio && !audio.paused) audio.pause();
      if (icon) icon.textContent = "play_arrow";
      card.classList.remove("is-active");
    });
  };

  cards.forEach(function (card) {
    var audio = card.querySelector(".podcast-audio");
    var playButton = card.querySelector(".podcast-play");
    if (!audio || !playButton) return;

    var icon = playButton.querySelector(".podcast-play-icon");
    var seek = card.querySelector(".podcast-seek");
    var timeCurrent = card.querySelector(".podcast-time-current");
    var timeTotal = card.querySelector(".podcast-time-total");
    var rateLabel = card.querySelector(".podcast-rate-label");

    var paintSeek = function () {
      if (!seek) return;
      var percent = Number(seek.value) || 0;
      var styles = window.getComputedStyle(seek);
      var fill = (styles.getPropertyValue("--seek-fill") || "").trim() || "#26b2e8";
      var track = (styles.getPropertyValue("--seek-track") || "").trim() || "rgba(255, 255, 255, 0.2)";
      seek.style.background =
        "linear-gradient(to left, " + fill + " " + percent + "%, " + track + " " + percent + "%)";
    };

    var applyRate = function (rate) {
      audio.playbackRate = rate;
      if (rateLabel) rateLabel.textContent = toFa(rate) + "×";
    };

    var rateIndex = function () {
      var found = SPEEDS.findIndex(function (rate) {
        return Math.abs(rate - audio.playbackRate) < 0.001;
      });
      return found === -1 ? 2 : found;
    };

    playButton.addEventListener("click", function () {
      if (audio.paused) {
        pauseOthers(card);
        card.classList.add("is-active");
        audio.play().catch(function () {});
        if (icon) icon.textContent = "pause";
      } else {
        audio.pause();
        if (icon) icon.textContent = "play_arrow";
      }
    });

    audio.addEventListener("loadedmetadata", function () {
      if (timeTotal) timeTotal.textContent = formatTime(audio.duration);
    });

    audio.addEventListener("timeupdate", function () {
      if (timeCurrent) timeCurrent.textContent = formatTime(audio.currentTime);
      if (seek && audio.duration > 0) {
        seek.value = String((audio.currentTime / audio.duration) * 100);
        paintSeek();
      }
    });

    audio.addEventListener("ended", function () {
      if (icon) icon.textContent = "play_arrow";
      if (seek) {
        seek.value = "0";
        paintSeek();
      }
      if (timeCurrent) timeCurrent.textContent = formatTime(0);
    });

    if (seek) {
      seek.addEventListener("input", function () {
        if (!audio.duration) return;
        audio.currentTime = (Number(seek.value) / 100) * audio.duration;
        paintSeek();
      });
    }

    card.querySelectorAll(".podcast-skip").forEach(function (skipButton) {
      skipButton.addEventListener("click", function () {
        if (!audio.duration) return;
        var delta = Number(skipButton.dataset.skip || 0);
        audio.currentTime = Math.min(Math.max(audio.currentTime + delta, 0), audio.duration);
      });
    });

    var slower = card.querySelector(".podcast-rate-down");
    var faster = card.querySelector(".podcast-rate-up");

    if (slower) {
      slower.addEventListener("click", function () {
        applyRate(SPEEDS[Math.max(0, rateIndex() - 1)]);
      });
    }

    if (faster) {
      faster.addEventListener("click", function () {
        applyRate(SPEEDS[Math.min(SPEEDS.length - 1, rateIndex() + 1)]);
      });
    }

    applyRate(1);
    paintSeek();
  });
})();
