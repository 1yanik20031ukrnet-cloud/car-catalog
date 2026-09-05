/* Live "Показать N" count in the filter panel.
 *
 * Works without this file too — the count just shows how many matched
 * the last submitted search until you press "Показать"/Enter again.
 * This makes it update as you change a field, before you submit,
 * by asking cars:filter_count for a fresh count in the background. */

(function () {
    'use strict';

    var panel = document.querySelector('.filters__panel');
    var countEl = document.getElementById('filters-count');
    if (!panel || !countEl) {
        return;
    }

    var countUrl = panel.getAttribute('data-filter-count-url');
    var form = panel.closest('form');
    if (!countUrl || !form) {
        return;
    }

    var timer = null;
    var pendingRequest = null;

    function scheduleUpdate() {
        window.clearTimeout(timer);
        timer = window.setTimeout(updateCount, 300);
    }

    function updateCount() {
        if (pendingRequest) {
            pendingRequest.abort();
        }

        var controller = new AbortController();
        pendingRequest = controller;

        var params = new URLSearchParams(new FormData(form));
        params.delete('sort'); // doesn't affect how many cars match

        fetch(countUrl + '?' + params.toString(), { signal: controller.signal })
            .then(function (response) {
                return response.ok ? response.json() : null;
            })
            .then(function (data) {
                if (data) {
                    countEl.textContent = data.count;
                }
            })
            .catch(function () {
                // Network hiccup or aborted by a newer edit — the button
                // just keeps showing the last count it had, harmless.
            })
            .finally(function () {
                if (pendingRequest === controller) {
                    pendingRequest = null;
                }
            });
    }

    panel.addEventListener('input', scheduleUpdate);
    panel.addEventListener('change', scheduleUpdate);
})();
