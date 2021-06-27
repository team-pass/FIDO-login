/**
 * Collects client-side timing data about every element that's tagged with a
 * `timed-element` attribute. 
 * 
 * Elements can specify a space-separated list of events that should be 
 * listened to using the `timed-events` attribute.
 * 
 * Otherwise, this script will listen for `focus` events.
 */
const DEFAULT_EVENTS = ['focus'];
const interactions = [];
const timedElements = document.querySelectorAll("[timed-element]");
timedElements.forEach(attachListeners);

/**
 * Attaches timing listeners to the given HTML element. It will attach events to
 * every event listed in the element's `timed-events` attribute.
 * 
 * @param {HTMLElement} element 
 */
function attachListeners(element) {
    const timedEvents = getTimedEventsFor(element);

    timedEvents.forEach(event => {
        element.addEventListener(event, () => {
            interactions.push({
                timestamp: Date.now(),
                element: element.id,
                page: window.location.pathname, // Should this be determined client or server side?
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
    const customEvents = element.getAttribute("timed-events");

    return (customEvents && customEvents.split(" ")) || DEFAULT_EVENTS;
}

// TODO: possibly add interactions on page refresh