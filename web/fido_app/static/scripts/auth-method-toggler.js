const AUTH_METHOD = 'authentication-method';
const FIDO = 'fido';
const PASSWORDS = 'passwords';

const methodToggler = document.getElementById("auth-method-toggler");
const passwordInputs = document.querySelectorAll("#password-inputs input");

// Extract required password input fields into a map
const requiredPasswordInputMap = new Map([...passwordInputs].map(
    input => [input, input.getAttribute("required")]
));

/**
 * Sets the required password fields based on whether the user chose biometric
 * or password authentication
 */
function setRequiredFields() {
    // Note that this handler fires BEFORE the `aria-expanded` attribute changes.
    // That means that when the toggler WASN'T expanded, passwords WERE being used,
    // and biometrics will be used after the click event finishes propogating
    const willBeUsingBiometrics = methodToggler.getAttribute("aria-expanded") === "true";

    if (willBeUsingBiometrics) {
        // Turn off any required inputs
        passwordInputs.forEach(input => {
            input.removeAttribute("required")
        })
    } else {
        // Turn on any required inputs that were previously required
        passwordInputs.forEach(input => {
            if (requiredPasswordInputMap[input] !== null) {
                input.setAttribute("required", "true");
            }
        })
    }
}

/**
 * Saves the user's preferred authentication method to `window.localStorage`
 */
function saveAuthenticationPreference() {
    const authPreference = methodToggler.getAttribute("aria-expanded") === "true"
        ? FIDO
        : PASSWORDS;

    if (storageAvailable('localStorage')) {
        localStorage.setItem(AUTH_METHOD, authPreference);
        console.log("Setting auth preference to", localStorage.getItem(AUTH_METHOD));
    } else {
        console.warn("Unable to save authentication preference to local storage");
    }
}

/**
 * Sets the status of the authentication method toggle based on the user's
 * last-used sign in/registration method.
 */
function loadAuthenticationPreference() {
    if (!storageAvailable('localStorage')) {
        console.warn("Unable to load authentication preference from local storage");
        return;
    }

    const authMethod = localStorage.getItem(AUTH_METHOD);

    switch(authMethod) {
        case FIDO:
            methodToggler.click();
            break;

        case PASSWORDS:
            // Already in the default state
            break;

        default:
            console.error(`Invalid authentication preference ${authMethod}`);
    }

    console.log("Loaded preferred authentication method:", authMethod);
}

/**
 * Detects whether the browser supports the particular storage type. Taken from
 * https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API/Using_the_Web_Storage_API#testing_for_availability
 */
function storageAvailable(type) {
    var storage;
    try {
        storage = window[type];
        var x = '__storage_test__';
        storage.setItem(x, x);
        storage.removeItem(x);
        return true;
    }
    catch(e) {
        return e instanceof DOMException && (
            // everything except Firefox
            e.code === 22 ||
            // Firefox
            e.code === 1014 ||
            // test name field too, because code might not be present
            // everything except Firefox
            e.name === 'QuotaExceededError' ||
            // Firefox
            e.name === 'NS_ERROR_DOM_QUOTA_REACHED') &&
            // acknowledge QuotaExceededError only if there's something already stored
            (storage && storage.length !== 0);
    }
}


methodToggler.addEventListener("click", setRequiredFields);
methodToggler.addEventListener("click", saveAuthenticationPreference);

// Load authentication preference once when this script loads
loadAuthenticationPreference();