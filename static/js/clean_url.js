// static/js/clean_url.js

document.addEventListener('DOMContentLoaded', () => {
    // Clean sensitive parameters from URL
    if (window.location.search.includes('payment_intent_client_secret')) {
        const cleanUrl = window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
    }
});