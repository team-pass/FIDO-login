/**
 * Defines the login behavior for our app
 */

// Find form elements in the DOM
const loginForm = document.getElementById("login-form");
const authMethodToggler = document.getElementById("auth-method-toggler");

/**
 * Based on the user's choice to use biometrics, send the request to log them in
 */
function sendLoginForm(formSubmissionEvent) {
  const isUsingBiometrics = authMethodToggler.getAttribute("aria-expanded") === "false";

  if (isUsingBiometrics) {
    formSubmissionEvent.preventDefault();

    startBiometricLogin(new FormData(loginForm));
  }

  // Otherwise (for passwords), just use the default form submission
}

/**
 * This code is a slightly modified version of the client for Duo Labs' Flask demo for their 
 * py_webauthn library. It can be found at 
 * https://github.com/duo-labs/py_webauthn/tree/master/flask_demo
 */


/**
 * Callback executed after submitting login form
 * @param {FormData} formData
 */
const startBiometricLogin = async (formData) => {

  // post the login data to the server to retrieve the PublicKeyCredentialRequestOptions
  let credentialRequestOptionsFromServer;
  try {
    credentialRequestOptionsFromServer = await getCredentialRequestOptionsFromServer(formData);
  } catch (err) {
    return console.error("Error when getting request options from server:", err);
  }

  // convert certain members of the PublicKeyCredentialRequestOptions into
  // byte arrays as expected by the spec.    
  const transformedCredentialRequestOptions = transformCredentialRequestOptions(
    credentialRequestOptionsFromServer);

  // request the authenticator to create an assertion signature using the
  // credential private key
  let assertion;
  try {
    assertion = await navigator.credentials.get({
      publicKey: transformedCredentialRequestOptions,
    });
  } catch (err) {
    return console.error("Error when creating credential:", err);
  }

  // we now have an authentication assertion! encode the byte arrays contained
  // in the assertion data as strings for posting to the server
  const transformedAssertionForServer = transformAssertionForServer(assertion);

  // post the assertion to the server for verification.
  try {
    await postAssertionToServer(transformedAssertionForServer, formData.get('csrf_token'));
  } catch (err) {
    return console.error("Error when validating assertion on server:", err);
  }
};


/**
 * Get PublicKeyCredentialRequestOptions for this user from the server
 * formData of the registration form
 * @param {FormData} formData 
 */
const getCredentialRequestOptionsFromServer = async (formData) => {
  return await fetch_json("/webauthn/login/start", {
    method: "POST",
    body: formData,
  });
}

/**
 * Transforms items in the credentialCreateOptions generated on the server
 * into byte arrays expected by the navigator.credentials.create() call
 * @param {Object} credentialRequestOptionsFromServer 
 */
const transformCredentialRequestOptions = (credentialRequestOptionsFromServer) => {
  let {
    challenge,
    allowCredentials
  } = credentialRequestOptionsFromServer;

  challenge = Uint8Array.from(
    atob(challenge.replace(/_/g, "/").replace(/-/g, "+")), c => c.charCodeAt(0));

  allowCredentials = allowCredentials.map(credentialDescriptor => {
    let {
      id
    } = credentialDescriptor;
    id = id.replace(/_/g, "/").replace(/-/g, "+");
    id = Uint8Array.from(atob(id), c => c.charCodeAt(0));
    return Object.assign({}, credentialDescriptor, {
      id
    });
  });

  const transformedCredentialRequestOptions = Object.assign({},
    credentialRequestOptionsFromServer, {
      challenge,
      allowCredentials
    });

  return transformedCredentialRequestOptions;
};


/**
 * Encodes the binary data in the assertion into strings for posting to the server.
 * @param {PublicKeyCredential} assertion 
 */
const transformAssertionForServer = (assertion) => {
  const authData = new Uint8Array(assertion.response.authenticatorData);
  const clientDataJSON = new Uint8Array(assertion.response.clientDataJSON);
  const userHandle = new Uint8Array(assertion.response.userHandle);
  const rawId = new Uint8Array(assertion.rawId);
  const sig = new Uint8Array(assertion.response.signature);
  const assertionClientExtensions = assertion.getClientExtensionResults();

  return {
    id: assertion.id,
    rawId: b64enc(rawId),
    response: {
      authenticatorData: b64RawEnc(authData),
      clientDataJSON: b64RawEnc(clientDataJSON),
      signature: b64RawEnc(sig),
      userHandle: b64RawEnc(userHandle),
    },
    type: assertion.type,
    clientExtensionResults: JSON.stringify(assertionClientExtensions)
  };
};

/**
 * Post the assertion to the server for validation and logging the user in. 
 * @param {Object} assertionDataForServer 
 * @param {string} csrfToken the CSRF token for the request
 */
const postAssertionToServer = async (assertionDataForServer, csrfToken) => {
  return await fetch_json("/webauthn/login/verify-assertion", {
    method: "POST",
    headers: {
      "X-CSRFToken": csrfToken,
      "Content-Type": "text/plain"
    },
    body: JSON.stringify(assertionDataForServer)
  });
}

// Bind event listeners
loginForm.addEventListener("submit", sendLoginForm);
document.addEventListener("webauthn-register-error", err => {
  alert("Registration error: " + err.detail.message); // TODO: Use a modal
});