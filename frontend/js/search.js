let currentQuery = "";
let currentPage = 1;

const CACHE_KEY = "searchCache";

function saveCache(query, page, data) {
  sessionStorage.setItem(CACHE_KEY, JSON.stringify({ query, page, data }));
}

function loadCache() {
  try {
    const raw = sessionStorage.getItem(CACHE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function renderResults(results, query, page, hasMore) {
  const grid = document.getElementById("properties-grid");

  const propPagination = document.getElementById("properties-pagination");
  if (propPagination) propPagination.style.display = "none";

  if (!results || results.length === 0) {
    grid.innerHTML =
      '<div class="col-12 text-center py-5"><p class="text-muted">No properties found.</p></div>';
    renderPagination(page, false);
    return;
  }

  grid.innerHTML = results
    .map(({ id, payload: p }) => {
      const imgUrl = (p.imgs && p.imgs[0])
        ? p.imgs[0].replace("https://file4.batdongsan.com.vn/",
                            "https://file4.batdongsan.com.vn/crop/393x222/")
        : "";
      return `
            <div class="col-xs-12 col-sm-6 col-md-6 col-lg-4">
                <div class="property-item mb-30">
                    <a href="property-single.html?id=${id}" class="img">
                        ${imgUrl ? `<img src="${imgUrl}" class="img-fluid" />` : ""}
                    </a>
                    <div class="property-content">
                        <div class="price mb-2"><span>${(p.price>0? p.price:"") + " " + p.price_unit}</span></div>
                        <span class="city d-block mb-3">${p.area + " m²"}</span>
                        <div>
                            <span class="d-block mb-2 text-black-50">${p.title}</span>
                        </div>
                        <div class="specs d-flex mb-4">
                            <span class="d-block d-flex align-items-center me-3">
                                <span class="caption">${p.address}</span>
                            </span>
                        </div>
                        <a href="property-single.html?id=${id}" class="btn btn-primary py-2 px-3">See details</a>
                    </div>
                </div>
            </div>`;
    })
    .join("");

  const searchInput = document.getElementById("search-input");
  if (searchInput) searchInput.value = query;

  renderPagination(page, hasMore);
}

async function fetchProperties(query, page) {
  window._searchActive = true;
  const grid = document.getElementById("properties-grid");
  grid.innerHTML =
    '<div class="col-12 text-center py-5"><div class="spinner-border text-primary" role="status"></div></div>';

  try {
    const res = await fetch(
      `http://127.0.0.1:8000/api/properties?s=${encodeURIComponent(query)}&page=${page}`,
    );
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail);
    }
    const data = await res.json();

    saveCache(query, page, data);
    renderResults(data.results, query, page, data.has_more);
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
    document.getElementById("properties-grid").insertAdjacentElement("afterend", container);
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
    currentPage--;
    fetchProperties(currentQuery, currentPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
  document.getElementById("btn-next").addEventListener("click", () => {
    currentPage++;
    fetchProperties(currentQuery, currentPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

document
  .getElementById("search-form")
  .addEventListener("submit", async function (e) {
    e.preventDefault();
    const query = document.getElementById("search-input").value.trim();
    if (!query) return;

    currentQuery = query;
    currentPage = 1;          
    fetchProperties(currentQuery, currentPage);
  });


(function restoreFromCache() {
  const navType = performance.getEntriesByType("navigation")[0]?.type;
  if (navType === "reload" || navType === "navigate") {
    sessionStorage.removeItem(CACHE_KEY);
    return;
  }
  const cache = loadCache();
  if (!cache) return;
  window._searchActive = true;   
  currentQuery = cache.query;
  currentPage = cache.page;
  renderResults(cache.data.results, cache.query, cache.page, cache.data.has_more);
})();
