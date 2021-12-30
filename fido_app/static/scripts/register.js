/**
 * Defines the registration behavior for our app, which relies on the
 * Web Authentication API to enable passwordless/biometric login (see
 * https://developer.mozilla.org/en-US/docs/Web/API/Web_Authentication_API).
 *
 * It relies on the WebAuthnApp example, provided here:
 * https://github.com/webauthn-open-source/webauthn-simple-app
 */

// Find form elements in the DOM
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
    startBiometricRegistration(new FormData(registrationForm));
  }

  // Otherwise, make sure the supplied password is valid
  if (!checkPasswordValidity()) {
    event.preventDefault();
  }
}

/**
 * This code is a slightly modified version of the client for Duo Labs' Flask demo for their 
 * py_webauthn library. It can be found at 
 * https://github.com/duo-labs/py_webauthn/tree/master/flask_demo
 */


/**
 * Callback after the registration form is submitted.
 * @param {FormData} formData
 */
const startBiometricRegistration = async (formData) => {
  try {
    
    const response = await fetch("/webauthn/registration/start", {
      method: 'POST',
      body: formData,
    });
    
    if(!response.ok) {
      const json = await response.json();
      window.location.replace(json['redirect']);
      return;
    }

    const credentialCreationData = await response.arrayBuffer();
    const options = CBOR.decode(credentialCreationData);

    const attestation = await navigator.credentials.create(options);

    const verficationResponse = await fetch('/webauthn/registration/verify-credentials', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/cbor',
        'X-CSRFToken': CSRF_TOKEN,
      },
      redirect: 'follow',
      body: CBOR.encode({
        "attestationObject": new Uint8Array(attestation.response.attestationObject),
        "clientDataJSON": new Uint8Array(attestation.response.clientDataJSON),
      })
    });
    
    if (!verficationResponse.ok) {
      const json = await verficationResponse.json();
      window.location.replace(json['redirect']);
    }
  } catch(e) {
    alert(e);
  }
}

// Bind event listeners
confirmPassword.addEventListener("blur", checkPasswordValidity);
registrationForm.addEventListener("submit", submitRegistrationForm);