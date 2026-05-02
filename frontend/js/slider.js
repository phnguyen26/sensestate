

var propertySlide = async () => {
  const res = await fetch("/api/data");
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
                                <img src="${encodeURI(imgUrl)}" alt="${p.title}"  />
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

propertySlide();