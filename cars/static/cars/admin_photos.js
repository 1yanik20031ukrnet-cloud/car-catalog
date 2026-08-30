/* Instant preview of photos picked in the "Загрузить фотографии" field
 * of the car admin form — purely client-side, nothing is uploaded or
 * saved to the site until the person actually clicks "Сохранить".
 */
(function () {
    function setupPreview() {
        var input = document.getElementById('id_photos');
        var preview = document.getElementById('id_photos-preview');
        if (!input || !preview) {
            return;
        }

        input.addEventListener('change', function () {
            preview.innerHTML = '';
            Array.from(input.files || []).forEach(function (file) {
                if (!file.type || file.type.indexOf('image/') !== 0) {
                    return;
                }
                var img = document.createElement('img');
                img.src = URL.createObjectURL(file);
                img.alt = file.name;
                img.onload = function () {
                    URL.revokeObjectURL(img.src);
                };
                preview.appendChild(img);
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupPreview);
    } else {
        setupPreview();
    }
})();
