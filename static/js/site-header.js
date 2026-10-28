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

  let input = document.querySelector("[data-site-search]");
  if (!input) {
    input = document.querySelector(
      'input[placeholder="جستجوی آموزش، مقاله..."]',
    );
    if (input) {
      input.dataset.siteSearch = "";
      input.dataset.searchUrl = "/search/";
      input.setAttribute("aria-label", "جست‌وجوی دوره و مقاله");
      input.setAttribute("aria-autocomplete", "list");
      input.setAttribute("aria-expanded", "false");
      input.autocomplete = "off";
      const wrapper = input.parentElement;
      wrapper.dataset.siteSearchContainer = "";
      wrapper.classList.remove("hidden");
      wrapper.classList.add(
        "flex",
        "relative",
        "w-32",
        "sm:w-44",
        "md:w-56",
        "lg:w-64",
        "shrink-0",
      );
      const results = document.createElement("ul");
      results.id = "site-search-results";
      results.className = "site-search-results";
      results.dataset.siteSearchResults = "";
      results.setAttribute("role", "listbox");
      results.hidden = true;
      wrapper.append(results);
      input.setAttribute("aria-controls", results.id);
    }
  }

  if (!document.querySelector("[data-mobile-menu]")) {
    const nav = document.querySelector("nav[data-path], header nav");
    const headerBar = nav?.parentElement;
    if (nav && headerBar) {
      nav.dataset.siteNav = "";
      nav.classList.add("site-nav");
      const button = document.createElement("button");
      button.type = "button";
      button.className =
        "xl:hidden h-10 w-10 rounded-xl bg-surface-container-high text-primary-container";
      button.setAttribute("aria-label", "بازکردن منو");
      button.setAttribute("aria-expanded", "false");
      button.dataset.mobileMenu = "";
      button.innerHTML = '<span class="material-symbols-outlined">menu</span>';
      headerBar.insertBefore(button, nav);
    }
  }

  if (!document.querySelector('link[href="/static/css/site-header.css"]')) {
    const stylesheet = document.createElement("link");
    stylesheet.rel = "stylesheet";
    stylesheet.href = "/static/css/site-header.css";
    document.head.append(stylesheet);
  }

  const resultsBox = document.querySelector("[data-site-search-results]");
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

        const items = results.map((result) => {
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

  document.querySelectorAll("[data-mobile-menu]").forEach((button) => {
    button.addEventListener("click", () => {
      const nav = document.querySelector("[data-site-nav]");
      const expanded = button.getAttribute("aria-expanded") === "true";
      button.setAttribute("aria-expanded", String(!expanded));
      if (nav) nav.classList.toggle("is-mobile-open", !expanded);
    });
  });
})();
