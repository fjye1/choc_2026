document.addEventListener("DOMContentLoaded", () => {
    const logo = document.getElementById("logo");

    if (!sessionStorage.getItem("logoPlayed")) {
        // first load, animate
        logo.classList.add("animate");
        sessionStorage.setItem("logoPlayed", "true");
    } else {
        // subsequent loads: show last frame
        logo.classList.remove("animate"); // just in case
        logo.style.backgroundPosition = "-2800px 0"; // last frame
        logo.style.display = "block"; // ensure visible
    }
});