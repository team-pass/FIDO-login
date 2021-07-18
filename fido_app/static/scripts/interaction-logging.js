/**
 * Collects client-side timing data about every element that's tagged with a
 * `timed-element` attribute. 
 * 
 * Elements can specify a space-separated list of events that should be 
 * listened to using the `timed-events` attribute.
 * 
 * Otherwise, this script will listen for `focus` events.
 */
const interactions = [];
const timedElements = document.querySelectorAll("[timed-element]");
const form = document.querySelector(".primary-form");
timedElements.forEach(attachTimingListeners);
form.addEventListener('submit', submitInteractions);

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
                timestamp: Date.now(),
                element: element.id,
                event,
            });
        });
    });
}

/**
 * Returns a list of events that this element should listen for. That list
 * is either specified using the element's `timed-events` attribute or 
 * using the default list of events.
 * 
 * @param {HTMLElement} element
 * @returns list of event types to listen on
 */
function getTimedEventsFor(element) {
    const DEFAULT_EVENTS = ['focus'];
    const customEvents = element.getAttribute("timed-events");

    return (customEvents && customEvents.split(" ")) || DEFAULT_EVENTS;
}

/**
 * Submits all interactions that were logged on this page.
 * @param {Event} event the form submit event
 */
async function submitInteractions(event) {
    event.preventDefault();
    const url = "/interactions/submit/";

    try {
        const response = await fetch(url, {
            method: 'post',
            body: JSON.stringify(interactions),
        });

        if (!response.ok) {
            console.error("Posting the interactions didn't succeed. Response:", response);
            return;
        }

        // Clear interactions object (to prevent duplicate interactions)
        interactions = [];
    } catch(e) {
        console.error("Couldn't submit:", e);
    }
}