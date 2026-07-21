const emailForm = document.getElementById("email-form");
const pinForm = document.getElementById("pin-form");
const errorEl = document.getElementById("error");
const pinEmailEl = document.getElementById("pin-email");

let currentEmail = "";

function showError(message) {
  errorEl.textContent = message;
  errorEl.classList.remove("hidden");
}

function clearError() {
  errorEl.classList.add("hidden");
}

emailForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();

  currentEmail = document.getElementById("email").value.trim();

  const res = await fetch("/auth/request-pin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: currentEmail }),
  });

  if (!res.ok) {
    showError("Could not send login code. Try again.");
    return;
  }

  pinEmailEl.textContent = currentEmail;
  emailForm.classList.add("hidden");
  pinForm.classList.remove("hidden");
});

pinForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearError();

  const pin = document.getElementById("pin").value.trim();

  const res = await fetch("/auth/verify-pin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: currentEmail, pin }),
  });

  if (!res.ok) {
    showError("Invalid or expired code.");
    return;
  }

  window.location.href = "/player";
});
