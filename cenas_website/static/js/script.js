document.addEventListener('DOMContentLoaded', () => {
  const track = document.querySelector('.carousel-track');
  const slides = Array.from(track.children);
  const prevBtn = document.querySelector('.carousel-btn.prev');
  const nextBtn = document.querySelector('.carousel-btn.next');

  let currentIndex = 0;
  let interval;
  let slideWidth;

  // Duplicate first and last slides in JS for fake looping
  const firstClone = slides[0].cloneNode(true);
  const lastClone = slides[slides.length - 1].cloneNode(true);

  track.appendChild(firstClone);
  track.insertBefore(lastClone, slides[0]);

  const allSlides = Array.from(track.children);
  currentIndex = 1; // Start on real first slide

  function setSlidePositions() {
    slideWidth = allSlides[0].getBoundingClientRect().width;
    allSlides.forEach((slide, i) => {
      slide.style.left = `${i * slideWidth}px`;
    });
    track.style.transition = 'none';
    track.style.transform = `translateX(-${currentIndex * slideWidth}px)`;
  }

  function lazyLoad(index, callback) {
    const slide = allSlides[index];
    if (!slide) return callback();
    const img = slide.querySelector('img[data-src]');
    if (!img) return callback();

    img.src = img.dataset.src;
    img.removeAttribute('data-src');
    img.complete ? callback() : img.addEventListener('load', callback, { once: true });
  }

  function moveTo(index) {
    lazyLoad(index, () => {
      track.style.transition = 'transform 1.5s ease-in-out';
      track.style.transform = `translateX(-${index * slideWidth}px)`;
      currentIndex = index;
    });
  }

  // After transition: if we're on a clone, jump to real
  track.addEventListener('transitionend', () => {
    if (allSlides[currentIndex] === firstClone) {
      track.style.transition = 'none';
      currentIndex = 1;
      track.style.transform = `translateX(-${currentIndex * slideWidth}px)`;
    } else if (allSlides[currentIndex] === lastClone) {
      track.style.transition = 'none';
      currentIndex = allSlides.length - 2;
      track.style.transform = `translateX(-${currentIndex * slideWidth}px)`;
    }
  });

  function nextSlide() {
    moveTo(currentIndex + 1);
  }

  function prevSlide() {
    moveTo(currentIndex - 1);
  }

  function startCarousel() {
    interval = setInterval(() => {
      nextSlide();
    }, 5000);
  }

  function stopCarousel() {
    clearInterval(interval);
  }

  function resetCarousel() {
    stopCarousel();
    startCarousel();
  }

  document.addEventListener('visibilitychange', () => {
    document.hidden ? stopCarousel() : resetCarousel();
  });

  window.addEventListener('resize', setSlidePositions);


  // INIT
  setSlidePositions();
  lazyLoad(currentIndex, () => {
    track.style.transform = `translateX(-${currentIndex * slideWidth}px)`;
    startCarousel();
  });
});
// Global toast — called by this file and cart-ajax.js / cart-page.js
function showToast(message, type) {
  const colors = {
    success: '#2e7d32',
    error:   '#c62828',
    danger:  '#c62828',
    warning: '#e65100',
    info:    '#01579b',
  };
  let container = document.getElementById('ck-toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'ck-toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = 'ck-toast';
  toast.style.background = colors[type] || colors.info;
  toast.textContent = message;
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('ck-toast--show'));
  setTimeout(() => {
    toast.classList.remove('ck-toast--show');
    toast.addEventListener('transitionend', () => toast.remove(), { once: true });
  }, 3000);
}

// Convert server-rendered flash banners to toasts
document.addEventListener('DOMContentLoaded', () => {
  const container = document.querySelector('.flash-container');
  if (!container) return;
  container.querySelectorAll('.flash').forEach((flash, i) => {
    const type = [...flash.classList]
      .find(c => c.startsWith('flash-') && c !== 'flash')
      ?.replace('flash-', '') || 'info';
    const message = flash.querySelector('.flash-message')?.textContent?.trim()
      || flash.textContent.trim();
    setTimeout(() => showToast(message, type), i * 200);
  });
  container.remove();
});

document.addEventListener('DOMContentLoaded', () => {
const toggle = document.querySelector('.mobile-nav-toggle') || document.querySelector('.mobile-nav-toggle-base');
const navLinks = document.querySelector('.nav-links') || document.querySelector('.nav-links-base');

if (toggle && navLinks) {
  toggle.addEventListener('click', () => {
    navLinks.classList.toggle('active');
  });
}})

document.addEventListener('DOMContentLoaded', () => {
  const isMobile = window.matchMedia("(max-width: 768px)").matches;

  if (isMobile) {
    const dropdownLinks = document.querySelectorAll('.has-submenu');

    dropdownLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        const parent = link.parentElement;
        const dropdown = parent.querySelector('.dropdown-content');

        if (!parent.classList.contains('open')) {
          e.preventDefault(); // stop navigating
          parent.classList.add('open');
        } else {
          // second click navigates
          window.location.href = link.href;
        }
      });
    });
  }
});





