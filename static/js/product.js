// Price Chart initialization
function initPriceChart(dates, prices, sales) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: 'Price (₹)',
                data: prices,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const price = context.parsed.y;
                            const index = context.dataIndex;
                            return `₹${price.toFixed(2)} (Sales: ${sales[index]})`;
                        }
                    }
                }
            }
        }
    });
}

// Quantity buttons
function setupQuantityButtons() {
    const minusBtn = document.querySelector('.qty-btn.minus');
    const plusBtn = document.querySelector('.qty-btn.plus');
    const input = document.getElementById('quantity-input');

    minusBtn.addEventListener('click', () => {
        if (parseInt(input.value) > 1) input.value--;
    });

    plusBtn.addEventListener('click', () => {
        input.value = parseInt(input.value) + 1;
    });
}

// Star rating live update
function setupStarRating() {
    const stars = document.getElementById('stars');
    const ratingInput = document.getElementById('rating');

    ratingInput.addEventListener('input', () => {
        const value = parseInt(ratingInput.value);
        stars.textContent = '⭐'.repeat(value) + '☆'.repeat(5 - value);
    });
}

// Initialize all product JS functions
function initProductPage(dates, prices, sales) {
    initPriceChart(dates, prices, sales);
    setupQuantityButtons();
    setupStarRating();
}