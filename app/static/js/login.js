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

// Prefer the server's own explanation (e.g. "not on the invite list")
// over a generic fallback.
async function errorFrom(res, fallback) {
  try {
    const body = await res.json();
    if (body && typeof body.detail === "string") return body.detail;
  } catch (_) {
    /* not JSON — fall through */
  }
  return fallback;
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
    showError(await errorFrom(res, "Could not send login code. Try again."));
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
    showError(await errorFrom(res, "Invalid or expired code."));
    return;
  }

  window.location.href = "/player";
});
