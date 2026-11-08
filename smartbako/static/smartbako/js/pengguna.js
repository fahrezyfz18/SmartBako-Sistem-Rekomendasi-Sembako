/* ==================================================
   SMARTBAKO - PANEL PENGGUNA
   (Navbar dan menu HP ditangani Bootstrap.)
   1. Baki perbandingan produk (maks. 3, sesuai US-07)
   2. Penandaan harga termurah pada tabel perbandingan
   3. Pilihan cepat anggaran pada formulir preferensi
   ================================================== */

(function () {
    'use strict';

    var body = document.body;

    /* ---------- 1. Baki perbandingan ---------- */

    var STORAGE_KEY = 'smartbako_bandingkan';

    var tray = document.getElementById('compare-tray');
    var countEl = document.getElementById('compare-count');
    var listEl = document.getElementById('compare-list');
    var goEl = document.getElementById('compare-go');
    var clearEl = document.getElementById('compare-clear');
    var noteEl = document.getElementById('compare-note');
    var badgeEl = document.querySelector('[data-compare-badge]');

    var maxItems = tray ? parseInt(tray.getAttribute('data-max'), 10) || 3 : 3;
    var compareUrl = tray ? tray.getAttribute('data-url') : '';
    var items = [];

    function loadItems() {
        try {
            var raw = window.sessionStorage.getItem(STORAGE_KEY);
            var parsed = raw ? JSON.parse(raw) : [];
            return Array.isArray(parsed) ? parsed : [];
        } catch (error) {
            return [];
        }
    }

    function saveItems() {
        try {
            window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(items));
        } catch (error) {
            /* Penyimpanan tidak tersedia: pilihan hanya berlaku di halaman ini. */
        }
    }

    function indexOfItem(id) {
        for (var i = 0; i < items.length; i++) {
            if (String(items[i].id) === String(id)) {
                return i;
            }
        }
        return -1;
    }

    function buildCompareHref() {
        var query = items
            .map(function (item) {
                return 'produk=' + encodeURIComponent(item.id);
            })
            .join('&');

        return compareUrl + (query ? '?' + query : '');
    }

    function say(message) {
        if (noteEl) {
            noteEl.textContent = message || '';
        }
    }

    function syncCheckboxes() {
        var boxes = document.querySelectorAll('input[data-compare]');

        Array.prototype.forEach.call(boxes, function (box) {
            box.checked = indexOfItem(box.getAttribute('data-id')) !== -1;
        });
    }

    function renderTray() {
        var total = items.length;

        if (badgeEl) {
            badgeEl.textContent = total;
            badgeEl.hidden = total === 0;
        }

        if (!tray) {
            return;
        }

        var onComparePage = !!document.querySelector('[data-compare-page]');

        /* Baki disembunyikan jika kosong atau sedang di halaman perbandingan. */
        tray.hidden = total === 0 || onComparePage;
        body.classList.toggle('has-tray', !tray.hidden);

        if (countEl) {
            countEl.textContent = total;
        }

        if (listEl) {
            listEl.textContent = '';

            items.forEach(function (item) {
                var li = document.createElement('li');
                var label = document.createElement('span');
                var remove = document.createElement('button');

                label.textContent = item.name;
                label.title = item.name;

                remove.type = 'button';
                remove.textContent = '×';
                remove.setAttribute('aria-label', 'Hapus ' + item.name + ' dari perbandingan');
                remove.addEventListener('click', function () {
                    removeItem(item.id);
                });

                li.appendChild(label);
                li.appendChild(remove);
                listEl.appendChild(li);
            });
        }

        if (goEl) {
            var ready = total >= 2;
            goEl.setAttribute('aria-disabled', ready ? 'false' : 'true');
            goEl.setAttribute('href', ready ? buildCompareHref() : '#');
        }

        /* Tombol "Bandingkan" di navbar membawa pilihan aktif. */
        var navLink = badgeEl ? badgeEl.closest('a') : null;
        if (navLink) {
            navLink.setAttribute('href', buildCompareHref());
        }
    }

    function refresh() {
        saveItems();
        syncCheckboxes();
        renderTray();
    }

    function addItem(id, name) {
        if (indexOfItem(id) !== -1) {
            return true;
        }

        if (items.length >= maxItems) {
            say('Maksimal ' + maxItems + ' produk dapat dibandingkan sekaligus.');
            return false;
        }

        items.push({ id: String(id), name: name });
        say('');
        return true;
    }

    function removeItem(id) {
        var index = indexOfItem(id);

        if (index !== -1) {
            items.splice(index, 1);
        }

        say('');
        refresh();
    }

    function clearItems() {
        items = [];
        say('');
        refresh();
    }

    if (tray || badgeEl) {
        items = loadItems();

        /* Halaman perbandingan: URL adalah sumber kebenaran. */
        var cols = document.querySelectorAll('[data-compare-col]');
        if (cols.length) {
            items = Array.prototype.map.call(cols, function (col) {
                return {
                    id: col.getAttribute('data-id'),
                    name: col.getAttribute('data-name')
                };
            });
            saveItems();
        }

        /* Pilihan lama yang melebihi batas dipangkas. */
        if (items.length > maxItems) {
            items = items.slice(0, maxItems);
        }

        document.addEventListener('change', function (event) {
            var box = event.target;

            if (!box.matches || !box.matches('input[data-compare]')) {
                return;
            }

            var id = box.getAttribute('data-id');
            var name = box.getAttribute('data-name');

            if (box.checked) {
                if (!addItem(id, name)) {
                    box.checked = false;
                    return;
                }
            } else {
                var index = indexOfItem(id);
                if (index !== -1) {
                    items.splice(index, 1);
                }
                say('');
            }

            refresh();
        });

        if (clearEl) {
            clearEl.addEventListener('click', clearItems);
        }

        if (goEl) {
            goEl.addEventListener('click', function (event) {
                if (goEl.getAttribute('aria-disabled') === 'true') {
                    event.preventDefault();
                    say('Pilih minimal 2 produk untuk dibandingkan.');
                }
            });
        }

        /* Tombol "Hapus" pada kolom tabel perbandingan. */
        document.addEventListener('click', function (event) {
            var button = event.target.closest('[data-compare-remove]');

            if (!button) {
                return;
            }

            var id = button.getAttribute('data-compare-remove');
            var index = indexOfItem(id);

            if (index !== -1) {
                items.splice(index, 1);
            }

            saveItems();
            window.location.href = buildCompareHref();
        });

        refresh();
    }

    /* ---------- 2. Harga termurah ---------- */

    var bestRows = document.querySelectorAll('tr[data-best-row="min"]');

    Array.prototype.forEach.call(bestRows, function (row) {
        var cells = row.querySelectorAll('td[data-value]');
        var min = Infinity;

        Array.prototype.forEach.call(cells, function (cell) {
            var value = parseFloat(cell.getAttribute('data-value'));
            if (!isNaN(value) && value < min) {
                min = value;
            }
        });

        var sama = 0;
        Array.prototype.forEach.call(cells, function (cell) {
            if (parseFloat(cell.getAttribute('data-value')) === min) {
                sama++;
            }
        });

        /* Tidak ditandai jika semua harga sama. */
        if (sama === cells.length) {
            return;
        }

        Array.prototype.forEach.call(cells, function (cell) {
            if (parseFloat(cell.getAttribute('data-value')) === min) {
                cell.classList.add('is-best');
            }
        });
    });

    /* ---------- 3. Pilihan cepat anggaran ---------- */

    var budgetField = document.getElementById('id_budget_max');
    var chips = document.querySelectorAll('[data-set-budget]');

    Array.prototype.forEach.call(chips, function (chip) {
        chip.addEventListener('click', function () {
            if (budgetField) {
                budgetField.value = chip.getAttribute('data-set-budget');
                budgetField.focus();
            }
        });
    });
})();