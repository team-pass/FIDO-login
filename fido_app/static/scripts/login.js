/**
 * Defines the login behavior for our app, which relies on the
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
  loginChallengeEndpoint: "/login/challenge/",
  loginResponseEndpoint: "/login/response",
  appName: "team-pass/fido-login",
};

// Find form elements in the DOM
const biometric = document.getElementById("biometric");
const biometricForm = document.getElementById("biometric-login-form");

// If the user is using biometrics, use the WebAuthnApp to handle login for us :)
// Otherwise, just use the regular login form
biometricForm.addEventListener("submit", event => {
  event.preventDefault();

  webAuthnConfig.username = biometric.value;
  new WebAuthnApp(webAuthnConfig).register();
})

// Handle biometric registration errors
document.addEventListener("webauthn-register-error", (err) => {
  alert("Registration error: " + err.detail.message); // TODO: Use a modal
});