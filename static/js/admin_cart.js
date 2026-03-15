// admin_cart.js
function updateTotals() {
    let total = 0;
    document.querySelectorAll('li[data-product-id]').forEach(li => {
        const qty = parseFloat(li.querySelector('.quantity').value) || 0;
        const price = parseFloat(li.querySelector('.unit-price').value) || 0;
        const lineTotal = qty * price;
        li.querySelector('.line-total').textContent = '₹' + lineTotal.toFixed(2);
        total += lineTotal;
    });
    document.getElementById('cart-total').textContent = total.toFixed(2);
}

// Listen for changes
document.querySelectorAll('.quantity, .unit-price').forEach(input => {
    input.addEventListener('input', updateTotals);
});

// Optional: handle checkout AJAX/form submit here
// document.getElementById('checkout-form').addEventListener('submit', e => { ... });