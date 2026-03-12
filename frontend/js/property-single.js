var renderPropertySingle = async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const propertyId = urlParams.get("id");
  console.log("Property ID:", propertyId);

  const res = await fetch(
    "http://127.0.0.1:8000/api/properties/" + String(propertyId)
  );
  const property = await res.json();

  const heroGrid = document.getElementById("content-1");
  heroGrid.innerHTML = `
    <div class="col-lg-9 text-center mt-5">
      <h1 class="heading" data-aos="fade-up">
        ${property.title}
      </h1>
      <nav aria-label="breadcrumb">
        <ol class="breadcrumb text-center justify-content-center">
          <li class="breadcrumb-item"><a href="index.html">Home</a></li>
          <li class="breadcrumb-item">
            <a href="properties.html">Properties</a>
          </li>
          <li class="breadcrumb-item active text-white-50" aria-current="page">
            ${property.title}
          </li>
        </ol>
      </nav>
    </div>
  `;

  const imageSliderWrap = document.querySelector(".img-property-slide-wrap");
  if (imageSliderWrap && property.imgs && property.imgs.length > 0) {
    imageSliderWrap.innerHTML = '';
    imageSliderWrap.innerHTML = `
      <div class="img-property-slide">
        ${property.imgs
          .map(
            (imgUrl) => `
              <div style="width:614px;height:345px;overflow:hidden;flex-shrink:0;">
                <img 
                  src="${imgUrl}" 
                  alt="${property.title}" 
                  style="width:100%;height:100%;object-fit:cover;object-position:center;display:block;"
                />
              </div>
        `
          )
          .join("")}
      </div>
    `;


      tns({
        container: ".img-property-slide",
        mode: "carousel",
        speed: 700,
        items: 1,
        gutter: 0,
        autoplay: true,
        controls: false,
        nav: true,
        autoplayButtonOutput: false,
      });
    }
  // }

  const detailsSection = document.querySelector(".col-lg-4");
  if (detailsSection) {
    const priceDisplay = property.price
      ? `${(property.price>0) ? property.price : ''} ${property.price_unit || ""} ${property.price_ext || ""}`
      : "Liên hệ";
    const areaDisplay = property.area ? `${property.area} m²` : "";
    const directionDisplay = property.direction
      ? `<p class="meta"><strong>Hướng:</strong> ${property.direction}</p>`
      : "";
    const legalDisplay = property.legal
      ? `<p class="meta"><strong>Pháp lý:</strong> ${property.legal}</p>`
      : "";

    const formattedDescription = property.description
      ? property.description.replace(/\n/g, "<br>")
      : "";

    detailsSection.innerHTML = `
      <h2 class="heading text-primary">${property.title}</h2>
      <p class="meta">${property.address}</p>
      <div class="property-info mb-3">
        <p class="text-success fw-bold fs-4">${priceDisplay}</p>
        ${areaDisplay ? `<p class="meta"><strong>Diện tích:</strong> ${areaDisplay}</p>` : ""}
        ${directionDisplay}
        ${legalDisplay}
      </div>
      <div class="text-black-50 property-description">
        ${formattedDescription}
      </div>
    `;

    const mapContainer = document.getElementById("property-map");
    if (mapContainer && property.address) {
      const encodedAddress = encodeURIComponent(property.address);
      mapContainer.innerHTML = `
        <iframe
          width="100%"
          height="300"
          style="border:0; border-radius:8px;"
          loading="lazy"
          allowfullscreen
          referrerpolicy="no-referrer-when-downgrade"
          src="https://maps.google.com/maps?q=${encodedAddress}&output=embed">
        </iframe>
      `;
    }
  }
};

window.onload = renderPropertySingle;
