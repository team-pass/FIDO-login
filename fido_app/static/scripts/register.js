/**
 * Defines the registration behavior for our app, which relies on the
 * Web Authentication API to enable passwordless/biometric login (see
 * https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API).
 *
 * It relies on the WebAuthnApp example, provided here:
 * https://github.com/webauthn-open-source/webauthn-simple-app
 */

// Set up the web authentication library with information about our app
const {
  WebAuthnApp
} = WebAuthnSimpleApp;
const webAuthnConfig = {
  registerChallengeEndpoint: "/register/challenge/",
  registerResponseEndpoint: "/register/response/",
  appName: "team-pass/fido-login",
};

// Find form elements in the DOM
const email = document.getElementById("email");
const password = document.getElementById("password");
const confirmPassword = document.getElementById("confirm-password");
const registrationForm = document.getElementById("registration-form");
const authMethodToggler = document.getElementById("auth-method-toggler")

/**
 * Ensures that the password and confirm password inputs have matching values
 * TODO: possibly add more stringent password requirements (like length and
 * character requirements)
 *
 * @returns whether the password fields are valid
 */
function checkPasswordValidity() {
  const isPasswordValid = password.value === confirmPassword.value;
  confirmPassword.setCustomValidity(isPasswordValid ? "" : "Passwords must match");
  console.log(isPasswordValid)

  return isPasswordValid;
}

/**
 * Based on the user's choice to use biometrics, send the request to register their account
 */
function submitRegistrationForm() {
  const isUsingBiometrics = authMethodToggler.getAttribute("aria-expanded") === "false"

  if (isUsingBiometrics) {
    // Use the WebAuthnApp to handle registration for us :)
    event.preventDefault();
    webAuthnConfig.username = email.value;
    new WebAuthnApp(webAuthnConfig).register();
  }

  // Otherwise, make sure the supplied password is valid
  if (!checkPasswordValidity()) {
    event.preventDefault();
  }
}

// Bind event listeners
confirmPassword.addEventListener("blur", checkPasswordValidity);
registrationForm.addEventListener("submit", submitRegistrationForm);
document.addEventListener("webauthn-register-error", (err) => {
  alert("Registration error: " + err.detail.message); // TODO: Improve visuals
});