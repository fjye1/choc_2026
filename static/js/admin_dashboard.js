console.log("admin.js loaded");

const ctx = document.getElementById('salesChart').getContext('2d');

const salesChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: dayLabels,
        datasets: [{
            label: 'Sales (₹)',
            data: salesValues,
            backgroundColor: 'rgba(135,206,235,0.2)',
            borderColor: 'skyblue',
            borderWidth: 2,
            fill: true,
            tension: 0.3
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: { beginAtZero: true }
        }
    }
});