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
    alert('Error getting registration data!');
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
    alert("Unsuccessful verification");
  }
} catch(e) {
  alert(e);
}


  // fetch("/webauthn/registration/start", {
  //   method: 'POST',
  //   body: formData,
  // }).then(function(response) {
  //   if(response.ok) return response.arrayBuffer();
  //   throw new Error('No credential available to authenticate!');
  // }).then(CBOR.decode).then(function(options) {
  //   return navigator.credentials.get(options);
  // }).then(function(assertion) {
  //   return fetch('/webauthn/registration/verify-credentials', {
  //     method: 'POST',
  //     headers: {
  //       'Content-Type': 'application/cbor',
  //       'X-CSRFToken': CSRF_TOKEN,
  //     },
  //     body: CBOR.encode({
  //       "credentialId": new Uint8Array(assertion.rawId),
  //       "authenticatorData": new Uint8Array(assertion.response.authenticatorData),
  //       "clientDataJSON": new Uint8Array(assertion.response.clientDataJSON),
  //       "signature": new Uint8Array(assertion.response.signature),
  //     })
  //   });
  // }).then(function(response) {
  //   var stat = response.ok ? 'successful' : 'unsuccessful';
  //   alert('Authentication ' + stat + ' More details in server log...');
  // }, function(reason) {
  //   alert(reason);
  // });
}

// /**
//  * Get PublicKeyCredentialRequestOptions for this user from the server
//  * formData of the registration form
//  * @param {FormData} formData 
//  */
// const getCredentialCreateOptionsFromServer = async (formData) => {
//   return await fetch_json(, {
//     method: "POST",
//     body: formData
//   });
// }

/**
 * Transforms items in the credentialCreateOptions generated on the server
 * into byte arrays expected by the navigator.credentials.create() call
 * @param {Object} credentialCreateOptionsFromServer 
 */
const transformCredentialCreateOptions = (credentialCreateOptionsFromServer) => {
  let {
    challenge,
    user
  } = credentialCreateOptionsFromServer;
  user.id = Uint8Array.from(
    atob(credentialCreateOptionsFromServer.user.id
      .replace(/\_/g, "/")
      .replace(/\-/g, "+")
    ),
    c => c.charCodeAt(0));

  challenge = Uint8Array.from(
    atob(credentialCreateOptionsFromServer.challenge
      .replace(/\_/g, "/")
      .replace(/\-/g, "+")
    ),
    c => c.charCodeAt(0));

  const transformedCredentialCreateOptions = Object.assign({}, credentialCreateOptionsFromServer, {
    challenge,
    user
  });

  return transformedCredentialCreateOptions;
}


/**
 * Transforms the binary data in the credential into base64 strings
 * for posting to the server.
 * @param {PublicKeyCredential} newAssertion 
 */
const transformNewAssertionForServer = (newAssertion) => {
  const attObj = new Uint8Array(
    newAssertion.response.attestationObject);
  const clientDataJSON = new Uint8Array(
    newAssertion.response.clientDataJSON);
  const rawId = new Uint8Array(
    newAssertion.rawId);

  const registrationClientExtensions = newAssertion.getClientExtensionResults();

  return {
    id: newAssertion.id,
    rawId: b64enc(rawId),
    type: newAssertion.type,
    attObj: b64enc(attObj),
    clientData: b64enc(clientDataJSON),
    registrationClientExtensions: JSON.stringify(registrationClientExtensions)
  };
}

/**
 * Posts the new credential data to the server for validation and storage.
 * @param {Object} credentialDataForServer 
 * @param {string} csrfToken the CSRF token for the request
 */
const postNewAssertionToServer = async (credentialDataForServer, csrfToken) => {
  const formData = new FormData();
  Object.entries(credentialDataForServer).forEach(([key, value]) => {
    formData.set(key, value);
  });

  // Add in CSRF token
  formData.set('csrf_token', csrfToken);


  return await fetch_json("/webauthn/registration/verify-credentials", {
    method: "POST",
    body: formData
  });
}


// Bind event listeners
confirmPassword.addEventListener("blur", checkPasswordValidity);
registrationForm.addEventListener("submit", submitRegistrationForm);