/**
 * Collects client-side timing data about every element that's tagged with a
 * `timed-element` attribute. 
 * 
 * Elements can specify a space-separated list of events that should be 
 * listened to using the `timed-events` attribute.
 * 
 * Otherwise, this script will listen for `focus` events.
 */
let interactions = [];
const timedElements = document.querySelectorAll("[timed-element]");
const form = document.querySelector(".primary-form");
timedElements.forEach(attachTimingListeners);
form.addEventListener("submit", submitInteractions);

/**
 * Attaches timing listeners to the given HTML element. It will attach events to
 * every event listed in the element's `timed-events` attribute.
 * 
 * @param {HTMLElement} element 
 */
function attachTimingListeners(element) {
    const timedEvents = getTimedEventsFor(element);

    timedEvents.forEach(event => {
        element.addEventListener(event, () => {
            interactions.push({
                timestampMs: Date.now(),
                element: element.id,
                page: window.location.pathname,
                event,
            });
        });
    });
}

/**
 * Returns a list of events that this element should listen for. That list
 * is either specified using the element"s `timed-events` attribute or 
 * using the default list of events.
 * 
 * @param {HTMLElement} element
 * @returns list of event types to listen on
 */
function getTimedEventsFor(element) {
    const DEFAULT_EVENTS = ["focus"];
    const customEvents = element.getAttribute("timed-events");

    return (customEvents && customEvents.split(" ")) || DEFAULT_EVENTS;
}

/**
 * Submits all interactions that were logged on this page.
 */
async function submitInteractions() {
    const url = "/interactions/submit";

    try {
        const response = await fetch(url, {
            method: "POST",
            body: JSON.stringify(interactions),
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": CSRF_TOKEN, // This value is injected by Flask
            },
        });

        if (!response.ok) {
            console.error("Posting the interactions didn't succeed. Response:", response);
        }

        // Clear interactions to prevent logging duplicate events
        interactions = [];
    } catch(e) {
        console.error("Couldn't submit:", e);
    }
}
