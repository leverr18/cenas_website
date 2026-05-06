document.addEventListener('DOMContentLoaded', () => {
    const shopUrl = document.querySelector('.cart-shell')?.dataset.shopUrl || '/shop';

    // AJAX remove
    document.querySelectorAll('.js-remove-form').forEach(form => {
        form.addEventListener('submit', async e => {
            e.preventDefault();
            const row = form.closest('tr');
            const name = row?.querySelector('.item-name')?.textContent?.trim() || 'Item';
            const btn = form.querySelector('.btn-remove');

            if (btn) btn.disabled = true;
            try {
                const res = await fetch(form.action, {
                    method: 'POST',
                    body: new FormData(form),
                    headers: { 'X-Requested-With': 'fetch' }
                });
                const result = await res.json();
                if (!result.ok) throw new Error();

                row?.remove();
                recalcTotal();
                showToast(`${name} removed`, 'info');
                checkEmpty(shopUrl);
            } catch {
                if (btn) btn.disabled = false;
                showToast('Failed to remove item — please refresh', 'error');
            }
        });
    });

    // AJAX qty update (triggered by +/- buttons via requestSubmit in baselogin.html)
    document.querySelectorAll('.qty-edit-form').forEach(form => {
        form.addEventListener('submit', async e => {
            e.preventDefault();
            const row = form.closest('tr');
            const input = form.querySelector('.qty-input');
            const name = row?.querySelector('.item-name')?.textContent?.trim() || 'Item';

            try {
                const res = await fetch(form.action, {
                    method: 'POST',
                    body: new FormData(form),
                    headers: { 'X-Requested-With': 'fetch' }
                });
                const result = await res.json();
                if (!result.ok) throw new Error();

                if (result.removed) {
                    row?.remove();
                    showToast(`${name} removed`, 'info');
                    checkEmpty(shopUrl);
                } else if (input) {
                    input.value = result.quantity;
                }
                recalcTotal();
            } catch {
                showToast('Failed to update quantity — please refresh', 'error');
            }
        });
    });
});

function recalcTotal() {
    let total = 0;
    document.querySelectorAll('.qty-input').forEach(el => {
        total += parseInt(el.value || 0);
    });
    const el = document.querySelector('.cart-total');
    if (el) el.textContent = `Total items: ${total}`;
}

function checkEmpty(shopUrl) {
    const tbody = document.querySelector('.cart-table tbody');
    if (!tbody || tbody.rows.length > 0) return;
    const card = document.querySelector('.cart-card');
    if (!card) return;
    card.innerHTML = `
        <h1>Your Cart</h1>
        <p class="cart-empty">Your cart is empty.</p>
        <a href="${shopUrl}" class="btn-back">← Back to Shop</a>
    `;
}
