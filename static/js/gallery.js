/* Photo carousels: the big one on the car page, and the small one inside
 * every catalog card.
 *
 * Both work without this file — each strip is a CSS scroll-snap container
 * you swipe, and the car page's thumbnails are plain anchors that jump to
 * their photo. This adds the arrows, the eased slide and the indicators.
 * Arrows ship hidden and are revealed here, so they never sit there dead
 * when the script fails to load. */

(function () {
    'use strict';

    // Tells the stylesheet the fade-in is actually going to happen.
    document.documentElement.classList.add('js');

    /* Wires one scrolling strip. `parts` carries whatever this strip has:
     * prev/next buttons, a counter, dots, thumbnails. All are optional. */
    function carousel(stage, parts) {
        var slides = Array.prototype.slice.call(stage.children);
        if (slides.length < 2) {
            return;
        }

        var current = 0;

        function show(index) {
            current = index;

            if (parts.thumbs) {
                parts.thumbs.forEach(function (thumb, i) {
                    thumb.classList.toggle('is-active', i === index);
                    thumb.setAttribute('aria-current', i === index ? 'true' : 'false');
                });
            }
            if (parts.dots) {
                parts.dots.forEach(function (dot, i) {
                    dot.classList.toggle('is-active', i === index);
                });
            }
            if (parts.counter) {
                parts.counter.textContent = String(index + 1);
            }
            // Dimmed and unclickable at the ends, so the arrows say where you are.
            if (parts.prev) {
                parts.prev.disabled = index === 0;
            }
            if (parts.next) {
                parts.next.disabled = index === slides.length - 1;
            }
        }

        function goTo(index) {
            if (index < 0 || index > slides.length - 1) {
                return;
            }
            stage.scrollTo({
                left: slides[index].offsetLeft - slides[0].offsetLeft,
                behavior: 'smooth',
            });
            show(index);
        }

        if (parts.prev && parts.next) {
            parts.prev.hidden = false;
            parts.next.hidden = false;
            parts.prev.addEventListener('click', function (event) {
                // Inside a catalog card the click would otherwise reach the
                // link covering the photo and open the car.
                event.preventDefault();
                event.stopPropagation();
                goTo(current - 1);
            });
            parts.next.addEventListener('click', function (event) {
                event.preventDefault();
                event.stopPropagation();
                goTo(current + 1);
            });
        }

        if (parts.thumbs) {
            parts.thumbs.forEach(function (thumb, index) {
                thumb.addEventListener('click', function (event) {
                    // Following the anchor would jump the whole page to the
                    // photo and push the gallery off the top of the screen.
                    event.preventDefault();
                    goTo(index);
                });
            });
        }

        stage.addEventListener('keydown', function (event) {
            if (event.key === 'ArrowLeft') {
                event.preventDefault();
                goTo(current - 1);
            } else if (event.key === 'ArrowRight') {
                event.preventDefault();
                goTo(current + 1);
            }
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

        show(0);

        return {
            index: function () {
                return current;
            },
            // Used when opening and closing the viewer: the two carousels
            // hand their position to each other without an animation.
            jump: function (index) {
                if (index < 0 || index > slides.length - 1) {
                    return;
                }
                stage.scrollTo({
                    left: slides[index].offsetLeft - slides[0].offsetLeft,
                    behavior: 'auto',
                });
                show(index);
            },
        };
    }

    function list(root, selector) {
        return Array.prototype.slice.call(root.querySelectorAll(selector));
    }

    var gallery = null;
    var stage = document.getElementById('gallery-stage');
    if (stage) {
        gallery = carousel(stage, {
            prev: document.querySelector('[data-gallery-prev]'),
            next: document.querySelector('[data-gallery-next]'),
            counter: document.querySelector('[data-gallery-current]'),
            thumbs: list(document, '[data-gallery-thumb]'),
        });
    }

    /* Full-screen viewer. A native <dialog> brings Esc, the backdrop and
     * focus handling with it, so there is no library and no key handling of
     * our own to get wrong. */
    var box = document.getElementById('lightbox');
    var boxStage = document.getElementById('lightbox-stage');
    if (box && boxStage && typeof box.showModal === 'function') {
        var viewer = carousel(boxStage, {
            prev: box.querySelector('[data-lightbox-prev]'),
            next: box.querySelector('[data-lightbox-next]'),
            counter: box.querySelector('[data-lightbox-current]'),
        });

        var open = function () {
            box.showModal();
            // offsetLeft only means anything once the dialog is laid out, so
            // the jump to the current photo waits until after showModal.
            if (viewer && gallery) {
                viewer.jump(gallery.index());
            }
            document.documentElement.classList.add('is-locked');
        };

        var zoom = document.querySelector('[data-lightbox-open]');
        if (zoom) {
            zoom.hidden = false;
            zoom.addEventListener('click', open);
        }
        if (stage) {
            stage.addEventListener('click', function (event) {
                // The arrows sit on top and stop their own clicks.
                if (!event.target.closest('.gallery__nav')) {
                    open();
                }
            });
        }

        box.querySelector('[data-lightbox-close]').addEventListener('click', function () {
            box.close();
        });
        // Clicking the backdrop means clicking the dialog itself.
        box.addEventListener('click', function (event) {
            if (event.target === box) {
                box.close();
            }
        });
        box.addEventListener('close', function () {
            document.documentElement.classList.remove('is-locked');
            if (gallery && viewer) {
                gallery.jump(viewer.index());
            }
        });
    }

    /* Photos fade in over a shimmering placeholder instead of popping in as
     * bare grey boxes. Images already in cache are marked at once. */
    list(document, '.gallery__slide img, .car-card__photo, .gallery__thumb img').forEach(function (img) {
        var done = function () {
            img.classList.add('is-loaded');
        };
        if (img.complete && img.naturalWidth > 0) {
            done();
        } else {
            img.addEventListener('load', done);
            img.addEventListener('error', done);
        }
    });

    list(document, '[data-card-strip]').forEach(function (strip) {
        var card = strip.closest('.car-card');
        carousel(strip, {
            prev: card.querySelector('[data-card-prev]'),
            next: card.querySelector('[data-card-next]'),
            dots: list(card, '.card-dots__dot'),
        });
    });
})();
