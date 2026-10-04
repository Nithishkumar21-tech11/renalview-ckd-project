let createMode = false;
const form = document.querySelector("#auth-form");
const feedback = document.querySelector("#auth-feedback");
const password = document.querySelector("#password");

function setMode(nextCreateMode) {
  createMode = nextCreateMode;
  document.querySelector("#auth-kicker").textContent = createMode ? "CREATE YOUR WORKSPACE" : "YOUR WORKSPACE";
  document.querySelector("#auth-title").textContent = createMode ? "Create account" : "Sign in";
  document.querySelector("#auth-intro").textContent = createMode ? "Use an email address or mobile number to create an account." : "Enter your email address or mobile number to continue.";
  document.querySelector("#auth-submit").innerHTML = createMode ? 'Create account <span>→</span>' : 'Sign in <span>→</span>';
  document.querySelector("#switch-copy").textContent = createMode ? "Already have an account?" : "New to RenalView?";
  document.querySelector("#switch-mode").textContent = createMode ? "Sign in" : "Create an account";
  password.autocomplete = createMode ? "new-password" : "current-password";
  password.minLength = createMode ? 8 : 1;
  document.querySelector("#auth-footnote").textContent = createMode ? "Create a password with at least 8 characters." : "Use your email or mobile number and password.";
  feedback.textContent = "";
  feedback.classList.remove("error");
}

document.querySelector("#switch-mode").addEventListener("click", () => setMode(!createMode));
document.querySelector("#toggle-password").addEventListener("click", (event) => {
  const visible = password.type === "text";
  password.type = visible ? "password" : "text";
  event.currentTarget.textContent = visible ? "Show" : "Hide";
  event.currentTarget.setAttribute("aria-label", visible ? "Show password" : "Hide password");
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  feedback.textContent = "";
  feedback.classList.remove("error");
  const button = document.querySelector("#auth-submit");
  const original = createMode ? 'Create account <span>→</span>' : 'Sign in <span>→</span>';
  button.disabled = true;
  button.innerHTML = `Please wait <span class="auth-spinner"></span>`;
  try {
    const response = await fetch(createMode ? "/api/auth/register" : "/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        identifier: document.querySelector("#identifier").value,
        password: password.value,
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Could not sign in.");
    feedback.textContent = createMode ? "Account created. Opening your workspace..." : "Signed in. Opening your workspace...";
    window.location.assign("/");
  } catch (error) {
    feedback.textContent = error.message || "Could not sign in.";
    feedback.classList.add("error");
  } finally {
    button.disabled = false;
    button.innerHTML = original;
  }
});

const art = document.querySelector("#signin-art");
const artImage = document.querySelector("#signin-image");
if (art && artImage && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
  art.addEventListener("pointermove", (event) => {
    const box = art.getBoundingClientRect();
    const x = (event.clientX - box.left) / box.width - 0.5;
    const y = (event.clientY - box.top) / box.height - 0.5;
    artImage.style.transform = `translate(${x * -10}px, ${y * -8}px) scale(1.04)`;
  });
  art.addEventListener("pointerleave", () => { artImage.style.transform = ""; });
}
