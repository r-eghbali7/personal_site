(() => {
  const routes = {
    home: "/",
    courses: "/courses/",
    blog: "/blog/",
    podcasts: "/#podcasts",
    "online-quiz": "/quizzes/",
    "support-tickets": "/tickets/",
    cart: "/orders/cart/",
    "user-profile": "/accounts/profile/",
  };
  document.querySelectorAll("[data-path]").forEach((link) => {
    const route = routes[link.dataset.path];
    if (route) link.href = route;
  });

  const initSearch = (wrapper) => {
    const input = wrapper.querySelector("[data-site-search]");
    const resultsBox = wrapper.querySelector("[data-site-search-results]");
    if (!input || !resultsBox) return;

    let debounceTimer;
    let activeRequest;

    const closeResults = () => {
      resultsBox.hidden = true;
      resultsBox.replaceChildren();
      input.setAttribute("aria-expanded", "false");
    };

    const showMessage = (message) => {
      const item = document.createElement("li");
      item.className = "px-4 py-3 text-sm text-on-surface-variant";
      item.textContent = message;
      resultsBox.replaceChildren(item);
      resultsBox.hidden = false;
      input.setAttribute("aria-expanded", "true");
    };

    input.addEventListener("input", () => {
      window.clearTimeout(debounceTimer);
      activeRequest?.abort();
      const query = input.value.trim();
      if (query.length < 2) {
        closeResults();
        return;
      }
      debounceTimer = window.setTimeout(async () => {
        activeRequest = new AbortController();
        showMessage("در حال جست‌وجو...");
        try {
          const url = new URL(input.dataset.searchUrl, window.location.origin);
          url.searchParams.set("q", query);
          const response = await fetch(url, {
            headers: { "X-Requested-With": "XMLHttpRequest" },
            signal: activeRequest.signal,
          });
          if (!response.ok) throw new Error("Search request failed");
          const data = await response.json();
          const results = Array.isArray(data.results) ? data.results : [];
          if (!results.length) {
            showMessage("نتیجه‌ای پیدا نشد.");
            return;
          }
          // Limit to 3 items maximum
          const displayResults = results.slice(0, 3);
          const items = displayResults.map((result) => {
            const item = document.createElement("li");
            const link = document.createElement("a");
            const title = document.createElement("strong");
            const summary = document.createElement("span");
            const kind = document.createElement("span");
            item.className = "border-b border-border last:border-0";
            link.className = "block px-4 py-3 hover:bg-surface-container-low";
            link.href = result.url;
            title.className = "block text-sm text-on-surface";
            title.textContent = result.title;
            kind.className = "ml-2 text-xs text-primary-container";
            kind.textContent = result.kind;
            summary.className = "mt-1 block text-xs text-on-surface-variant";
            summary.textContent = result.summary || "";
            title.prepend(kind);
            link.append(title, summary);
            item.append(link);
            return item;
          });
          resultsBox.replaceChildren(...items);
          resultsBox.hidden = false;
          input.setAttribute("aria-expanded", "true");
        } catch (error) {
          if (error.name !== "AbortError")
            showMessage("جست‌وجو با خطا مواجه شد. دوباره تلاش کنید.");
        }
      }, 250);
    });

    input.addEventListener("keydown", (event) => {
      if (event.key === "Escape") closeResults();
      if (event.key === "ArrowDown" && !resultsBox.hidden) {
        resultsBox.querySelector("a")?.focus();
      }
    });

    document.addEventListener("click", (event) => {
      if (!event.target.closest("[data-site-search-container]")) closeResults();
    });
  };

  document.querySelectorAll("[data-site-search-container]").forEach(initSearch);

  // Mobile panel toggle
  document.querySelectorAll("[data-mobile-menu]").forEach((button) => {
    const panel = document.querySelector("[data-mobile-panel]");
    if (!panel) return;
    const closePanel = () => {
      panel.removeAttribute("open");
      panel.hidden = true;
      button.setAttribute("aria-expanded", "false");
    };
    button.addEventListener("click", () => {
      const open = panel.hasAttribute("open");
      if (open) {
        closePanel();
      } else {
        panel.setAttribute("open", "");
        panel.hidden = false;
        panel.classList.remove("hidden");
        button.setAttribute("aria-expanded", "true");
      }
    });
    // Clicking a nav link closes the panel
    panel.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", closePanel);
    });
    // Close when clicking outside
    document.addEventListener("click", (event) => {
      if (!panel.hasAttribute("open")) return;
      if (!event.target.closest("[data-mobile-panel]") && !event.target.closest("[data-mobile-menu]")) {
        closePanel();
      }
    });
  });

  // Mobile search toggle - show search input when search button is clicked
  document.querySelectorAll("[data-mobile-search-toggle]").forEach((button) => {
    const panel = document.querySelector("[data-mobile-panel]");
    const searchContainer = panel?.querySelector("[data-site-search-container]");
    if (!searchContainer) return;

    button.addEventListener("click", () => {
      // Open mobile panel if not open
      if (!panel?.hasAttribute("open")) {
        panel?.setAttribute("open", "");
        panel?.hidden = false;
        const menuBtn = document.querySelector("[data-mobile-menu]");
        menuBtn?.setAttribute("aria-expanded", "true");
      }
      // Focus on search input after panel opens
      setTimeout(() => {
        const searchInput = searchContainer.querySelector("[data-site-search]");
        searchInput?.focus();
      }, 300);
    });
  });
})();
