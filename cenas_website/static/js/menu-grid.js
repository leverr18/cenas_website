document.addEventListener("DOMContentLoaded", function () {
  const cards = Array.from(document.querySelectorAll(".menu-card"));
  if (!cards.length) return; // nothing to do on pages without cards

  /* ======================
   * FILTER LOGIC
   * ====================== */
  const pills = Array.from(document.querySelectorAll(".menu-filter-pill"));
  const select = document.getElementById("menu-filter-select");

  function applyFilter(value) {
    cards.forEach(card => {
      const cat = card.dataset.category;
      const show = (value === "all") || (cat === value);
      card.style.display = show ? "" : "none";
    });
  }

  function setActivePill(value) {
    pills.forEach(btn => {
      btn.classList.toggle("is-active", btn.dataset.filter === value || (value === "all" && btn.dataset.filter === "all"));
    });
  }

  pills.forEach(btn => {
    btn.addEventListener("click", () => {
      const value = btn.dataset.filter || "all";
      setActivePill(value);
      if (select) select.value = value;
      applyFilter(value);
    });
  });

  if (select) {
    select.addEventListener("change", () => {
      const value = select.value || "all";
      applyFilter(value);
      setActivePill(value);
    });
  }

  // Start with "all" visible
  applyFilter("all");

  /* ======================
   * MODAL LOGIC
   * ====================== */
  const modal = document.getElementById("menu-modal");
  const modalImg = document.getElementById("modal-img");
  const modalTitle = document.getElementById("modal-title");
  const modalDetails = document.getElementById("modal-details");
  let lastFocus = null;

  const hasModal = modal && modalImg && modalTitle && modalDetails;

if (hasModal) {
  function openModal(card) {
    if (!card) return;

    const imgEl = card.querySelector("img");
    const titleEl = card.querySelector(".menu-card-title");
    const detailsEl = card.querySelector(".menu-details");

    if (imgEl) {
      modalImg.src = imgEl.currentSrc || imgEl.src || "";
      modalImg.alt = imgEl.alt || "";
      modalImg.style.display = "";
    } else {
      modalImg.src = "";
      modalImg.alt = "";
      modalImg.style.display = "none";
    }

    modalTitle.textContent = titleEl ? titleEl.textContent.trim() : "";

    if (detailsEl) {
      modalDetails.innerHTML = detailsEl.innerHTML;
    } else {
      modalDetails.innerHTML = "<p>No description available.</p>";
    }

    lastFocus = document.activeElement;
    modal.removeAttribute("hidden");
    modal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = "hidden";

    const closeBtn = modal.querySelector(".menu-modal__close");
    if (closeBtn) closeBtn.focus();
  }

  function closeModal() {
    modal.setAttribute("aria-hidden", "true");
    modal.setAttribute("hidden", "");
    document.body.style.overflow = "";
    modalImg.src = "";
    modalImg.alt = "";
    modalTitle.textContent = "";
    modalDetails.innerHTML = "";
    if (lastFocus) lastFocus.focus();
  }

  // Trigger open from image button
  document.querySelectorAll(".menu-card-image-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const card = btn.closest(".menu-card");
      openModal(card);
    });

    btn.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        const card = btn.closest(".menu-card");
        openModal(card);
      }
    });
  });

  // Close modal with backdrop or X
  modal.addEventListener("click", (e) => {
    if (e.target.hasAttribute("data-close")) {
      closeModal();
    }
  });

  document.addEventListener("keydown", (e) => {
    if (modal.getAttribute("aria-hidden") === "false" && e.key === "Escape") {
      closeModal();
    }
  });
}});
