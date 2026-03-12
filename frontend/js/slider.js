

var propertySlide = async () => {
  const res = await fetch("http://127.0.0.1:8000/api/data");
  const data = await res.json();
  const slider = document.getElementById("property-slider");
  if (!slider) return;
  console.log("ok");
  slider.innerHTML ='';
  slider.innerHTML = data.results
    .map(({ id, payload: p }) => {
      const imgUrl = p.imgs[0].replace(
        "https://file4.batdongsan.com.vn/",
        "https://file4.batdongsan.com.vn/crop/393x222/",
      );
      return `
                            <div class="property-item">
                              <a href="property-single.html?id=${id}" class="img">
                                <img src="${encodeURI(imgUrl)}" alt="${p.title}" class="img-fluid" />
                              </a>
                              <div class="property-content">
                                <div class="price mb-2"><span>${(p.price>0? p.price:"") + " " + p.price_unit}</span></div>
                                <div>
                                  <span class="d-block mb-2 text-black-50">${p.title}</span>
                                  <span class="city d-block mb-3">${p.area + " m²"}</span>
                                  <a href="property-single.html?id=${id}" class="btn btn-primary py-2 px-3">See details</a>
                                </div>
                              </div>
                            </div>`;
    })
    .join("");
  tns({
    container: "#property-slider",
    mode: "carousel",
    speed: 700,
    gutter: 30,
    items: 3,
    autoplay: true,
    autoplayButtonOutput: false,
    controlsContainer: "#property-nav",
    responsive: {
      0: { items: 1 },
      700: { items: 2 },
      900: { items: 3 },
    },
  });
};

var currentPropertiesPage = 1;

var fetchPropertiesPage = async (page) => {
  const grid = document.getElementById("properties-grid");
  if (!grid) return;

  const searchPagination = document.getElementById("pagination-container");
  if (searchPagination) searchPagination.style.display = "none";

  grid.innerHTML =
    '<div class="col-12 text-center py-5"><div class="spinner-border text-primary" role="status"></div></div>';

  try {
    const res = await fetch(`http://127.0.0.1:8000/api/data?page=${page}`);
    const data = await res.json();

    if (window._searchActive) return;

    grid.innerHTML = data.results
      .map(({ id, payload: p }) => {
        const imgUrl = p.imgs[0].replace(
          "https://file4.batdongsan.com.vn/",
          "https://file4.batdongsan.com.vn/crop/393x222/",
        );
        return `
          <div class="col-xs-12 col-sm-6 col-md-6 col-lg-4">
            <div class="property-item mb-30">
              <a href="property-single.html?id=${id}" class="img data-id=${id}">
                <img src="${encodeURI(imgUrl)}" alt="${p.title}" class="img-fluid" />
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

    renderPropertiesPagination(page, data.has_more);
  } catch (err) {
    grid.innerHTML =
      '<div class="col-12 text-center py-5"><p class="text-danger">Error loading properties.</p></div>';
    console.error(err);
  }
};

var renderPropertiesPagination = (page, hasMore) => {
  let container = document.getElementById("properties-pagination");
  if (!container) {
    container = document.createElement("div");
    container.id = "properties-pagination";
    container.className = "col-12 text-center mt-4";
    document.getElementById("properties-grid").insertAdjacentElement("afterend", container);
  }

  container.innerHTML = `
    <nav aria-label="Properties pagination">
      <ul class="pagination justify-content-center">
        <li class="page-item ${page <= 1 ? "disabled" : ""}">
          <button class="page-link" id="props-btn-prev" ${page <= 1 ? "disabled" : ""}>Previous</button>
        </li>
        <li class="page-item active">
          <span class="page-link">${page}</span>
        </li>
        <li class="page-item ${!hasMore ? "disabled" : ""}">
          <button class="page-link" id="props-btn-next" ${!hasMore ? "disabled" : ""}>Next</button>
        </li>
      </ul>
    </nav>
  `;

  document.getElementById("props-btn-prev").addEventListener("click", () => {
    currentPropertiesPage--;
    fetchPropertiesPage(currentPropertiesPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
  document.getElementById("props-btn-next").addEventListener("click", () => {
    currentPropertiesPage++;
    fetchPropertiesPage(currentPropertiesPage);
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
};

propertySlide();
fetchPropertiesPage(currentPropertiesPage);
