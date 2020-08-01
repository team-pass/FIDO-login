// Select all necessary DOM elements
const authForm = document.getElementById("auth-form");
const mainInputsContainer = document.getElementById("main-inputs-container");
const passwordInputs = document.getElementById("password-inputs");
const authMethodToggler = document.getElementById("auth-method-toggler");
const biometricInputs = document.getElementById("biometric-inputs");

// On page load, set the height of the auth form
window.addEventListener("load", adjustAuthFormHeight);

// Swap between password and biometric authentication when the auth method switch is pressed
authMethodToggler.addEventListener("click", () => {
  authForm.classList.toggle("using-biometrics");
  adjustAuthFormHeight();
});

// Choose the auth form's height base on the presence of the using-biometrics class
function adjustAuthFormHeight() {
  mainInputsContainer.style.height = `${
    authForm.classList.contains("using-biometrics")
      ? biometricInputs.offsetHeight
      : passwordInputs.offsetHeight
  }px`;
}