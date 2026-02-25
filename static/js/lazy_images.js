window.addEventListener("load", () => {
  const images = document.querySelectorAll(".lazy-swap");

  images.forEach(img => {
    img.src = img.src.replace("_small", "_large");
  });
});