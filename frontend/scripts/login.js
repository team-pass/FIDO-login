/**
 * Defines the login behavior for our app, which relies on the
 * Web Authentication API to enable passwordless/biometric login (see
 * https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API).
 *
 * It relies on the WebAuthnApp example, provided here:
 * https://github.com/webauthn-open-source/webauthn-simple-app
 */

// Set up the web authentication library with information about our app
const { WebAuthnApp } = WebAuthnSimpleApp;
const webAuthnConfig = {
  loginChallengeEndpoint: "/login/challenge/",
  loginResponseEndpoint: "/login/response",
  appName: "team-pass/fido-login",
};

// Find form elements in the DOM
const email = document.getElementById("email");
const loginForm = document.getElementById("login-form");
const passwordTab = document.getElementById("password-tab");

// When the user submits the registration form, start the registration process
loginForm.addEventListener("submit", (event) => {
  event.preventDefault();

  if (passwordTab.classList.contains("active")) {
    const formData = new FormData(loginForm);

    console.log([...formData.entries()]);

    // If the user is using password auth, send the form data with fetch
    fetch("/registration/password", {
      method: "POST",
      body: new FormData(loginForm),
    })
      .then((response) => {
        // Ensure the response comes back ok
        if (!response.ok) {
          throw new Error(
            `Error with the network request (HTTP ${response.status})`
          );
        }
      })
      .catch((error) => {
        alert(`Registration error: ${error.message}`);
      });
  } else {
    // If the user is using biometrics, use the WebAuthnApp to handle login for us :)
    webAuthnConfig.username = email.value;
    new WebAuthnApp(webAuthnConfig).register();
  }
});

// Handle biometric registration errors
document.addEventListener("webauthn-register-error", (err) => {
  alert("Registration error: " + err.message); // TODO: Improve visuals
});
