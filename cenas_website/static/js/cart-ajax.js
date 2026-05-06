document.addEventListener("DOMContentLoaded", () => {
    const addForms = document.querySelectorAll(".js-add-to-cart");

    addForms.forEach(form => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();

            const submitButton = form.querySelector("button[type='submit']");
            const qtyInput = form.querySelector(".qty-input");
            const productId = form.dataset.productId;
            const endpoint = form.action;

            const formData = new FormData(form);
            formData.append("_ajax", "1");

            submitButton.disabled = true;

            try {
                const response = await fetch(endpoint, {
                    method: "POST",
                    body: formData,
                    headers: { "X-Requested-With": "fetch" }
                });

                const result = await response.json();
                if (!result.ok) throw new Error("Server rejected add-to-cart");

                // Update in-cart badge
                if (productId) {
                    const badge = document.querySelector(`.in-cart-badge[data-product-id="${productId}"]`);
                    if (badge) {
                        badge.textContent = `${result.quantity} in cart`;
                        badge.classList.remove("hidden");
                    }
                }

                const productName = form.closest('article')?.querySelector('.menu-card-title')?.textContent?.trim() || 'Item';
                showToast(`${result.quantity}× ${productName} added to cart`, 'success');

                qtyInput.value = 1;
                submitButton.disabled = false;

            } catch (error) {
                console.error("Add to cart failed:", error);
                submitButton.disabled = false;
                submitButton.textContent = "Add";
            }
        });
    });
});
