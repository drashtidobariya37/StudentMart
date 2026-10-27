/**
 * Student Mart - Main Frontend JavaScript
 * Handles navigation, location switching, geolocation detection, modals, image previews, and alerts.
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Mobile Menu / Drawer Toggle
  const mobileToggleBtn = document.getElementById("mobileMenuToggle");
  const mobileDrawer = document.getElementById("mobileDrawer");
  const mobileCloseBtn = document.getElementById("mobileCloseBtn");

  if (mobileToggleBtn && mobileDrawer) {
    mobileToggleBtn.addEventListener("click", () => {
      mobileDrawer.classList.toggle("active");
    });
  }

  if (mobileCloseBtn && mobileDrawer) {
    mobileCloseBtn.addEventListener("click", () => {
      mobileDrawer.classList.remove("active");
    });
  }

  if (mobileDrawer) {
    mobileDrawer.addEventListener("click", (e) => {
      if (e.target === mobileDrawer) {
        mobileDrawer.classList.remove("active");
      }
    });
  }

  // 2. Campus Location Switcher Dropdown
  const locationBtn = document.getElementById("locationDropdownBtn");
  const locationDropdown = document.getElementById("locationDropdown");

  if (locationBtn && locationDropdown) {
    locationBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      locationDropdown.classList.toggle("show");
      const isExpanded = locationDropdown.classList.contains("show");
      locationBtn.setAttribute("aria-expanded", isExpanded);
    });

    document.addEventListener("click", (e) => {
      if (!locationDropdown.contains(e.target) && e.target !== locationBtn) {
        locationDropdown.classList.remove("show");
        locationBtn.setAttribute("aria-expanded", "false");
      }
    });
  }

  // 2b. Desktop "More" Navigation Dropdown
  const moreDropdown = document.getElementById("moreNavDropdown");
  const moreDropdownBtn = document.getElementById("moreNavDropdownBtn");

  if (moreDropdown && moreDropdownBtn) {
    moreDropdownBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      moreDropdown.classList.toggle("show");
      const isExpanded = moreDropdown.classList.contains("show");
      moreDropdownBtn.setAttribute("aria-expanded", isExpanded);
    });

    document.addEventListener("click", (e) => {
      if (!moreDropdown.contains(e.target) && e.target !== moreDropdownBtn) {
        moreDropdown.classList.remove("show");
        moreDropdownBtn.setAttribute("aria-expanded", "false");
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && moreDropdown.classList.contains("show")) {
        moreDropdown.classList.remove("show");
        moreDropdownBtn.setAttribute("aria-expanded", "false");
        moreDropdownBtn.focus();
      }
    });
  }

  // 3. Optional Client-side Geolocation Detector
  const detectLocationBtn = document.getElementById("detectLocationBtn");
  if (detectLocationBtn) {
    detectLocationBtn.addEventListener("click", () => {
      if (!navigator.geolocation) {
        alert("Geolocation is not supported by your current browser.");
        return;
      }

      detectLocationBtn.disabled = true;
      detectLocationBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Detecting...';

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude;
          const lon = position.coords.longitude;

          // Known city coordinates in Gujarat
          const knownHubs = [
            { name: "Ahmedabad", state: "Gujarat", lat: 23.0225, lon: 72.5714 },
            { name: "Gandhinagar", state: "Gujarat", lat: 23.2156, lon: 72.6369 },
            { name: "Vadodara", state: "Gujarat", lat: 22.3072, lon: 73.1812 },
            { name: "Surat", state: "Gujarat", lat: 21.1702, lon: 72.8311 },
            { name: "Rajkot", state: "Gujarat", lat: 22.3039, lon: 70.8022 },
            { name: "Anand", state: "Gujarat", lat: 22.5645, lon: 72.9289 }
          ];

          // Compute closest hub by Euclidean distance
          let closestHub = knownHubs[0];
          let minDistance = Infinity;

          knownHubs.forEach((hub) => {
            const dist = Math.sqrt(Math.pow(lat - hub.lat, 2) + Math.pow(lon - hub.lon, 2));
            if (dist < minDistance) {
              minDistance = dist;
              closestHub = hub;
            }
          });

          // Post to /set-location
          const csrf = getCsrfToken();
          const formData = new FormData();
          formData.append("csrf_token", csrf);
          formData.append("city", closestHub.name);
          formData.append("state", closestHub.state);

          fetch("/set-location", {
            method: "POST",
            body: formData,
            headers: { "X-Requested-With": "XMLHttpRequest" }
          })
            .then(() => {
              window.location.reload();
            })
            .catch(() => {
              window.location.reload();
            });
        },
        (error) => {
          detectLocationBtn.disabled = false;
          detectLocationBtn.innerHTML = '<i class="bi bi-crosshair"></i> Detect My Campus / City';
          alert("Location permission was not granted or timed out. You can manually pick your city from the list.");
        },
        { timeout: 10000, enableHighAccuracy: false }
      );
    });
  }

  // 4. Alert Dismissal
  document.querySelectorAll(".alert-close").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const alert = e.target.closest(".alert");
      if (alert) {
        alert.style.opacity = "0";
        setTimeout(() => alert.remove(), 250);
      }
    });
  });

  // 5. Modal Open / Close System
  document.querySelectorAll("[data-modal-target]").forEach((trigger) => {
    trigger.addEventListener("click", (e) => {
      e.preventDefault();
      const targetId = trigger.getAttribute("data-modal-target");
      const modal = document.getElementById(targetId);
      if (modal) {
        modal.classList.add("active");
      }
    });
  });

  document.querySelectorAll(".modal-close-btn, .modal-backdrop").forEach((closeEl) => {
    closeEl.addEventListener("click", (e) => {
      if (e.target === closeEl) {
        const modal = closeEl.closest(".modal-backdrop") || closeEl;
        modal.classList.remove("active");
      }
    });
  });

  // 6. Image Upload File Preview
  const imageInput = document.getElementById("listingImageInput");
  const previewContainer = document.getElementById("imagePreviewContainer");
  if (imageInput && previewContainer) {
    imageInput.addEventListener("change", (e) => {
      previewContainer.innerHTML = "";
      const files = e.target.files;
      if (files && files.length > 0) {
        Array.from(files).forEach((file) => {
          if (file.type.startsWith("image/")) {
            const reader = new FileReader();
            reader.onload = (event) => {
              const imgWrap = document.createElement("div");
              imgWrap.className = "gallery-thumb-item";
              imgWrap.innerHTML = `<img src="${event.target.result}" alt="Preview">`;
              previewContainer.appendChild(imgWrap);
            };
            reader.readAsDataURL(file);
          }
        });
      }
    });
  }

  // 7. Global Confirmation Dialogs for destructive actions
  document.querySelectorAll("[data-confirm]").forEach((el) => {
    el.addEventListener("click", (e) => {
      const msg = el.getAttribute("data-confirm") || "Are you sure you want to proceed?";
      if (!confirm(msg)) {
        e.preventDefault();
      }
    });
  });
});

/**
 * Helper to fetch CSRF token from DOM
 */
function getCsrfToken() {
  const tokenMeta = document.querySelector('meta[name="csrf-token"]');
  if (tokenMeta) return tokenMeta.getAttribute("content");
  const tokenInput = document.querySelector('input[name="csrf_token"]');
  return tokenInput ? tokenInput.value : "";
}
