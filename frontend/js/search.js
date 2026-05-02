const DEFAULT_FILTERS = {
  type: "",
  price_from: "",
  price_to: "",
  area_from: "",
  area_to: "",
  address: "",
};

const CACHE_KEY = "propertyFilterCache";

let currentFilters = { ...DEFAULT_FILTERS };
let currentPage = 1;

const searchForm = document.getElementById("search-form");
if (!searchForm) {
  console.warn("Filter form not found");
} else {
  window._searchActive = true;

  function loadCache() {
    try {
      const raw = sessionStorage.getItem(CACHE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  }

  function saveCache(filters, page, data) {
    sessionStorage.setItem(CACHE_KEY, JSON.stringify({ filters, page, data }));
  }

  function normalizeNumberString(value) {
    if (value == null) return "";
    const raw = String(value).trim();
    if (!raw) return "";
    const parsed = Number(raw);
    if (!Number.isFinite(parsed) || parsed < 0) return "";
    return String(parsed);
  }

  function normalizeFilters(rawFilters) {
    const filters = {
      type: String(rawFilters.type || "").trim(),
      price_from: normalizeNumberString(rawFilters.price_from),
      price_to: normalizeNumberString(rawFilters.price_to),
      area_from: normalizeNumberString(rawFilters.area_from),
      area_to: normalizeNumberString(rawFilters.area_to),
      address: String(rawFilters.address || "").trim(),
    };

    if (
      filters.price_from &&
      filters.price_to &&
      Number(filters.price_from) > Number(filters.price_to)
    ) {
      [filters.price_from, filters.price_to] = [filters.price_to, filters.price_from];
    }

    if (
      filters.area_from &&
      filters.area_to &&
      Number(filters.area_from) > Number(filters.area_to)
    ) {
      [filters.area_from, filters.area_to] = [filters.area_to, filters.area_from];
    }

    return filters;
  }

  function collectFiltersFromForm() {
    return normalizeFilters({
      type: document.getElementById("type-input")?.value,
      price_from: document.getElementById("price-from")?.value,
      price_to: document.getElementById("price-to")?.value,
      area_from: document.getElementById("area-from")?.value,
      area_to: document.getElementById("area-to")?.value,
      address: document.getElementById("address-input")?.value,
    });
  }

  function fillFilterForm(filters) {
    const typeInput = document.getElementById("type-input");
    const priceFrom = document.getElementById("price-from");
    const priceTo = document.getElementById("price-to");
    const areaFrom = document.getElementById("area-from");
    const areaTo = document.getElementById("area-to");
    const addressInput = document.getElementById("address-input");
    if (typeInput) typeInput.value = filters.type;
    if (priceFrom) priceFrom.value = filters.price_from;
    if (priceTo) priceTo.value = filters.price_to;
    if (areaFrom) areaFrom.value = filters.area_from;
    if (areaTo) areaTo.value = filters.area_to;
    if (addressInput) addressInput.value = filters.address;
  }

  function buildQueryString(filters, page) {
    const params = new URLSearchParams();
    params.set("page", String(page));

    if (filters.type) params.set("type", filters.type);
    if (filters.price_from) params.set("price_from", filters.price_from);
    if (filters.price_to) params.set("price_to", filters.price_to);
    if (filters.area_from) params.set("area_from", filters.area_from);
    if (filters.area_to) params.set("area_to", filters.area_to);
    if (filters.address) params.set("address", filters.address);

    if (filters.price_from || filters.price_to) {
      params.set("price_unit", "tỷ");
    }

    return params.toString();
  }

  function renderResults(results, filters, page, hasMore) {
    const grid = document.getElementById("properties-grid");

    const propPagination = document.getElementById("properties-pagination");
    if (propPagination) propPagination.style.display = "none";

    fillFilterForm(filters);

    if (!results || results.length === 0) {
      grid.innerHTML =
        '<div class="col-12 text-center py-5"><p class="text-muted">No properties found.</p></div>';
      renderPagination(page, false);
      return;
    }

    grid.innerHTML = results
      .map(({ id, payload: p }) => {
        const rawImage = p.imgs && p.imgs[0] ? p.imgs[0] : "";
        const imgUrl = rawImage
          ? rawImage.replace(
              "https://file4.batdongsan.com.vn/",
              "https://file4.batdongsan.com.vn/crop/393x222/",
            )
          : "";

        const priceLabel = p.price > 0
          ? `${p.price} ${p.price_unit || ""}`.trim()
          : (p.price_unit || "Thỏa thuận");

        const areaLabel = p.area ? `${p.area} m²` : "";

        return `
            <div class="col-xs-12 col-sm-6 col-md-6 col-lg-4">
                <div class="property-item mb-30">
                    <a href="property-single.html?id=${id}" class="img">
                        ${imgUrl ? `<img src="${encodeURI(imgUrl)}" alt="${p.title || "Property image"}" />` : ""}
                    </a>
                    <div class="property-content">
                        <div class="price mb-2"><span>${priceLabel}</span></div>
                        <span class="city d-block mb-3">${areaLabel}</span>
                        <div>
                            <span class="d-block mb-2 text-black-50">${p.title || "Untitled property"}</span>
                        </div>
                        <div class="specs d-flex mb-4">
                            <span class="d-block d-flex align-items-center me-3">
                                <span class="caption">${p.address || ""}</span>
                            </span>
                        </div>
                        <a href="property-single.html?id=${id}" class="btn btn-primary py-2 px-3">See details</a>
                    </div>
                </div>
            </div>`;
      })
      .join("");

    renderPagination(page, hasMore);
  }

  async function fetchProperties(filters, page) {
    const normalizedFilters = normalizeFilters(filters);
    currentFilters = normalizedFilters;
    window._searchActive = true;

    const grid = document.getElementById("properties-grid");
    grid.innerHTML =
      '<div class="col-12 text-center py-5"><div class="spinner-border text-primary" role="status"></div></div>';

    try {
      const res = await fetch(`/api/properties?${buildQueryString(normalizedFilters, page)}`);
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(JSON.stringify(errorData));
      }

      const data = await res.json();
      saveCache(normalizedFilters, page, data);
      renderResults(data.results, normalizedFilters, page, data.has_more);
    } catch (err) {
      grid.innerHTML =
        '<div class="col-12 text-center py-5"><p class="text-danger">Error loading results. Please try again.</p></div>';
      console.error(err);
    }
  }

  function renderPagination(page, hasMore) {
    let container = document.getElementById("pagination-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "pagination-container";
      container.className = "col-12 text-center mt-4";
      document
        .getElementById("properties-grid")
        .insertAdjacentElement("afterend", container);
    }

    const prevDisabled = page <= 1 ? "disabled" : "";
    const nextDisabled = !hasMore ? "disabled" : "";

    container.innerHTML = `
      <nav aria-label="Property pagination">
        <ul class="pagination justify-content-center">
          <li class="page-item ${prevDisabled}">
            <button class="page-link" id="btn-prev" ${prevDisabled}>Previous</button>
          </li>
          <li class="page-item active">
            <span class="page-link">${page}</span>
          </li>
          <li class="page-item ${nextDisabled}">
            <button class="page-link" id="btn-next" ${nextDisabled}>Next</button>
          </li>
        </ul>
      </nav>
    `;

    document.getElementById("btn-prev").addEventListener("click", () => {
      currentPage -= 1;
      fetchProperties(currentFilters, currentPage);
      window.scrollTo({ top: 0, behavior: "smooth" });
    });

    document.getElementById("btn-next").addEventListener("click", () => {
      currentPage += 1;
      fetchProperties(currentFilters, currentPage);
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    currentFilters = collectFiltersFromForm();
    currentPage = 1;
    fetchProperties(currentFilters, currentPage);
  });

  const resetButton = document.getElementById("reset-filters");
  if (resetButton) {
    resetButton.addEventListener("click", () => {
      searchForm.reset();
      currentFilters = { ...DEFAULT_FILTERS };
      currentPage = 1;
      sessionStorage.removeItem(CACHE_KEY);
      fetchProperties(currentFilters, currentPage);
    });
  }

  (function bootstrapFilters() {
    const navType = performance.getEntriesByType("navigation")[0]?.type;
    if (navType === "reload" || navType === "navigate") {
      sessionStorage.removeItem(CACHE_KEY);
    }

    const cache = loadCache();
    if (!cache || !cache.data) {
      fetchProperties(currentFilters, currentPage);
      return;
    }

    currentFilters = normalizeFilters(cache.filters || DEFAULT_FILTERS);
    currentPage = Number(cache.page) || 1;
    renderResults(cache.data.results, currentFilters, currentPage, cache.data.has_more);
  })();
}
