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
const loginForm = document.getElementById("login-form");
const email = document.getElementById("email");
const authMethodToggler = document.getElementById("auth-method-toggler");

/**
 * Based on the user's choice to use biometrics, send the request to log them in
 */
function sendLoginForm(formSubmissionEvent) {
    const isUsingBiometrics = authMethodToggler.getAttribute("aria-expanded") === "false";

    if (isUsingBiometrics) {
        formSubmissionEvent.preventDefault();

        // Use the WebAuthnApp to handle the biometric login flow 
        webAuthnConfig.username = email.value;
        new WebAuthnApp(webAuthnConfig).register();
    }

    // Otherwise (for passwords), just use the default form submission
}

// Bind event listeners
loginForm.addEventListener("submit", sendLoginForm);
document.addEventListener("webauthn-register-error", err => {
    alert("Registration error: " + err.detail.message); // TODO: Use a modal
});