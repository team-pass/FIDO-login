/**
 * Defines the registration and login behavior for our app, which relies on the
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

/**
 * Ensures that the password and confirm password inputs have matching values
 * TODO: possibly add more stringent password requirements (like length and
 * character requirements)
 *
 * @returns whether the password fields are valid
 */
function checkPasswordValidity() {
  const isPasswordValid = password.value === confirmPassword.value;

  if (!isPasswordValid) {
    // Makes the confirm password field invalid
    confirmPassword.setCustomValidity("Passwords must match");
  } else {
    // Makes the confirm password field valid
    confirmPassword.setCustomValidity("");
  }

  return isPasswordValid;
}

// Ensure that the password and confirm password inputs have matching values
confirmPassword.addEventListener("blur", checkPasswordValidity);

// When the user submits the registration form, start the registration process
registrationForm.addEventListener("submit", (event) => {

  if (!checkPasswordValidity()) {
    event.preventDefault();
    return;
  }


  // TODO: comment this out once the biometric toggler request is merged
  // if (biometrics are active) {
  //   // If the user is using biometrics, use the WebAuthnApp to handle registration for us :)
  //   event.preventDefault();
  //   webAuthnConfig.username = email.value;
  //   new WebAuthnApp(webAuthnConfig).register();
  // }
});

// Handle biometric registration errors
document.addEventListener("webauthn-register-error", (err) => {
  alert("Registration error: " + err.detail.message); // TODO: Improve visuals
});