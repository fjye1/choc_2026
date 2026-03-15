// Build a JS map of product IDs to image URLs
const products = {
    {% for p in products %}
    {{ p.id|string }}: "{{ url_for('static', filename=p.image or 'default.png') }}"{{ "," if not loop.last else "" }}
    {% endfor %}
};

const select = document.getElementById('product-select');
const preview = document.getElementById('product-image-preview');

select.addEventListener('change', () => {
    const selected = select.value;
    if (selected && products[selected]) {
        preview.src = products[selected];
        preview.style.display = 'block';
    } else {
        preview.style.display = 'none';
    }
});
// Show initial image if dropdown has a value
select.dispatchEvent(new Event('change'));
