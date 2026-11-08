/* ==================================================
   SMARTBAKO - LANDING PAGE DAN AUTENTIKASI
   1. Menu navigasi (layar kecil)
   2. Bayangan header saat halaman digulir
   3. Tombol lihat/sembunyikan kata sandi
   ================================================== */

(function () {
    'use strict';

    /* ---------- 1. Menu navigasi ---------- */

    var nav = document.getElementById('sb-nav');
    var toggle = document.querySelector('[data-nav-toggle]');

    function setMenu(open) {
        if (!nav || !toggle) {
            return;
        }

        nav.classList.toggle('is-open', open);
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        toggle.setAttribute('aria-label', open ? 'Tutup menu' : 'Buka menu');
    }

    if (toggle) {
        toggle.addEventListener('click', function () {
            setMenu(!nav.classList.contains('is-open'));
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && nav.classList.contains('is-open')) {
                setMenu(false);
                toggle.focus();
            }
        });

        window.addEventListener('resize', function () {
            if (window.innerWidth > 860) {
                setMenu(false);
            }
        });
    }

    /* ---------- 2. Bayangan header ---------- */

    if (nav) {
        var onScroll = function () {
            nav.classList.toggle('is-scrolled', window.scrollY > 8);
        };

        onScroll();
        window.addEventListener('scroll', onScroll, { passive: true });
    }

    /* ---------- 3. Lihat / sembunyikan kata sandi ---------- */

    var buttons = document.querySelectorAll('[data-toggle-password]');

    Array.prototype.forEach.call(buttons, function (button) {
        var input = document.getElementById(button.getAttribute('data-toggle-password'));

        if (!input) {
            return;
        }

        button.addEventListener('click', function () {
            var show = input.type === 'password';

            input.type = show ? 'text' : 'password';
            button.textContent = show ? 'Sembunyikan' : 'Lihat';
            button.setAttribute(
                'aria-label',
                show ? 'Sembunyikan kata sandi' : 'Tampilkan kata sandi'
            );
        });
    });
})();