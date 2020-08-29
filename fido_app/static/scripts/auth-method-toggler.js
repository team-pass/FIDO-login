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

methodToggler.addEventListener("click", setRequiredFields);