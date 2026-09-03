/* Car photo gallery.
 *
 * The gallery works without this file: the strip is a CSS scroll-snap
 * container you swipe, and the thumbnails are plain anchors that jump to
 * their photo. This adds the polish — tapping a thumbnail slides the strip
 * instead of jumping the page, and the active thumbnail and the counter
 * follow the photo you are on. */

(function () {
    'use strict';

    var stage = document.getElementById('gallery-stage');
    if (!stage) {
        return;
    }

    var slides = Array.prototype.slice.call(stage.querySelectorAll('.gallery__slide'));
    var thumbs = Array.prototype.slice.call(document.querySelectorAll('[data-gallery-thumb]'));
    var counter = document.querySelector('[data-gallery-current]');
    if (slides.length < 2) {
        return;
    }

    function show(index) {
        thumbs.forEach(function (thumb, i) {
            thumb.classList.toggle('is-active', i === index);
            thumb.setAttribute('aria-current', i === index ? 'true' : 'false');
        });
        if (counter) {
            counter.textContent = String(index + 1);
        }
    }

    thumbs.forEach(function (thumb, index) {
        thumb.addEventListener('click', function (event) {
            // Following the anchor would jump the whole page to the photo and
            // push the gallery off the top of the screen; scroll the strip.
            event.preventDefault();
            stage.scrollTo({
                left: slides[index].offsetLeft - slides[0].offsetLeft,
                behavior: 'smooth',
            });
            show(index);
        });
    });

    // Follow whichever photo the viewer swiped to.
    if ('IntersectionObserver' in window) {
        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    show(slides.indexOf(entry.target));
                }
            });
        }, { root: stage, threshold: 0.6 });

        slides.forEach(function (slide) {
            observer.observe(slide);
        });
    }
})();
