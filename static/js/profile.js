document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('toggleAddAddress');
    const form = document.getElementById('addAddressForm');

    toggleBtn.addEventListener('click', () => {
        form.classList.toggle('visible');
        form.scrollIntoView({ behavior: 'smooth' });
    });
});