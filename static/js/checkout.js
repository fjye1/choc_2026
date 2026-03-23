const form = document.getElementById('payment-form');
if (form) {
  let stripe, elements;

  const csrfToken = document.querySelector('#payment-form input[name="csrf_token"]').value;

  fetch('/checkout/cart-data')
    .then(res => res.json())
    .then(data => {
      console.log('cart data:', data);
      return fetch('/checkout/create-payment-intent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        credentials: 'same-origin',
        body: JSON.stringify({ cart: data.items })
      });
    })
    .then(res => res.json())
    .then(({ clientSecret }) => {
      stripe = Stripe('pk_test_51RTLGdIB4LlFizy67MEzJaNLjWUUuzK0gjjz8cFImGmLnZ4ka468OHpf1dhQg7b25Hm180PfPh16BPEhVwq9Wcu100563RRNWV');

      elements = stripe.elements({
        clientSecret,
        appearance: { theme: 'flat' }
      });

      elements.create('payment').mount('#payment-element');
    });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('submit');
    btn.disabled = true;

    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: window.location.origin + '/checkout/success'
      }
    });

    if (error) {
      document.getElementById('payment-message').textContent = error.message;
      btn.disabled = false;
    }
  });
}