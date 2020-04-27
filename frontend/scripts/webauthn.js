/**
 * Defines the registration and login behavior for our app, which relies on the
 * Web Authentication API to enable passwordless/biometric login (see
 * https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API).
 *
 * It relies on the WebAuthnApp example, provided here:
 * https://github.com/webauthn-open-source/webauthn-simple-app
 */

// Our app's endpoints
const LOGIN_PAGE = "./index.html";
const REGISTRATION_PAGE = "./registration.html";
const ACCOUNT_PAGE = "./account.html";

// Set up the web authentication library with information about our app
const { WebAuthnApp } = WebAuthnSimpleApp;
const webAuthnConfig = {
  registerChallengeEndpoint: "/register/challenge/",
  registerResponseEndpoint: "/register/response/",
  loginChallengeEndpoint: "/login/challenge/",
  loginResponseEndpoint: "/login/response",
  appName: "team-pass/fido-login",
};

// Find form elements in the DOM
const email = document.getElementById("email");
const loginForm = document.getElementById("login-form");
const registrationForm = document.getElementById("registration-form");

/**
 * Registration page event handling
 */
if (registrationForm) {
  // When the user submits the registration form, start the registration process
  registrationForm.addEventListener("submit", (event) => {
    event.preventDefault();
    webAuthnConfig.username = email.value;
    new WebAuthnApp(webAuthnConfig).register();
  });

  // Redirect the user to the login page if registration succeeds
  document.addEventListener("webauthn-register-success", () => {
    window.location = LOGIN_PAGE;
  });

  // Handle registration errors
  document.addEventListener("webauthn-register-error", (err) => {
    alert("Registration error: " + err.message); // TODO: Improve visuals
  });
}

/**
 * Login page event handling
 */
if (loginForm) {
  // When the user submits the login form, start the log in process
  loginForm.addEventListener("submit", (event) => {
    event.preventDefault();
    webAuthnConfig.username = email.value;
    new WebAuthnApp(webAuthnConfig).login();
  });

  // Redirect the user to the account page on success
  document.addEventListener("webauthn-login-success", () => {
    window.location = ACCOUNT_PAGE;
  });

  // Handle login errors
  document.addEventListener("webauthn-login-error", (err) => {
    alert("Log in error: " + err.message); // TODO: Improve visuals
  });

  // Remind the user to authenticate
  document.addEventListener("webauthn-user-presence-start", () => {
    alert("Please perform user verification on your authenticator now!");
  });
}
