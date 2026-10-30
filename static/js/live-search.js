(() => {
  const initSearch = (wrapper) => {
    const input = wrapper.querySelector("[data-live-search]");
    const resultsBox = wrapper.querySelector("[data-live-search-results]");
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

    const kindLabel = () => {
      const kind = input.dataset.searchKind || "";
      return kind || (input.dataset.searchUrl.includes("/courses/") ? "دوره" : "مقاله");
    };

    const buildItem = (result) => {
      const item = document.createElement("li");
      item.className = "border-b border-border last:border-0";
      const link = document.createElement("a");
      link.className = "block px-4 py-3 hover:bg-surface-container-low";
      link.href = result.url;
      const title = document.createElement("strong");
      title.className = "block text-sm text-on-surface";
      title.textContent = result.title;
      const kind = document.createElement("span");
      kind.className = "ml-2 text-xs text-primary-container";
      kind.textContent = result.kind || kindLabel();
      const summary = document.createElement("span");
      summary.className = "mt-1 block text-xs text-on-surface-variant";
      summary.textContent = result.summary || "";
      title.prepend(kind);
      link.append(title, summary);
      item.append(link);
      return item;
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
          let results = [];
          if (Array.isArray(data.results)) results = data.results;
          else if (Array.isArray(data.courses)) {
            results = data.courses.map((c) => ({
              kind: "دوره",
              title: c.title,
              url: `/courses/${c.slug}/`,
              summary: c.price == 0 ? "رایگان" : `${c.price.toLocaleString()} تومان · ${c.level}`,
            }));
          } else if (Array.isArray(data.posts)) {
            results = data.posts.map((p) => ({
              kind: "مقاله",
              title: p.title,
              url: `/blog/${p.slug}/`,
              summary: p.summary || "",
            }));
          }
          if (!results.length) {
            showMessage("نتیجه‌ای پیدا نشد.");
            return;
          }
          const displayResults = results.slice(0, 5);
          resultsBox.replaceChildren(...displayResults.map(buildItem));
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
      if (!event.target.closest("[data-live-search-container]")) closeResults();
    });
  };

  document.querySelectorAll("[data-live-search-container]").forEach(initSearch);
})();
