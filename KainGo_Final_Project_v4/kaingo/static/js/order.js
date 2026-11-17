// Self-ordering kiosk: start -> menu -> food -> review -> details -> place order.
// Prices and choices are checked again by the server, so changing them in the browser does nothing.
var MENU = JSON.parse(document.getElementById('menuData').textContent);
var start = JSON.parse(document.getElementById('startData').textContent);
var cart = [];                                   // lines: {id, qty, picks: {Group: Option}}
var category = null;
var orderType = start.type === 'Pickup' ? 'Pickup' : 'Delivery';
var form = document.getElementById('orderForm');

function $(id) { return document.getElementById(id); }
function money(n) { return '₱' + n.toFixed(2); }
function findFood(id) { return MENU.find(function (f) { return f.id === Number(id); }); }
function el(tag, className, text) {
    var e = document.createElement(tag);
    if (className) { e.className = className; }
    if (text !== undefined) { e.textContent = text; }          // textContent keeps menu names safe from XSS
    return e;
}
function button(className, text, onclick) {
    var b = el('button', className, text);
    b.type = 'button';
    b.onclick = onclick;
    return b;
}
function picksText(picks) { return Object.keys(picks).map(function (g) { return g + ': ' + picks[g]; }).join(' · '); }

// the dish photo (or the emoji when there is no photo)
function picture(food, className) {
    var box = el('div', className);
    if (food.image) {
        var img = document.createElement('img');
        img.src = start.img + food.image;
        img.alt = food.name;
        img.loading = 'lazy';
        img.onerror = function () { box.removeChild(img); box.textContent = food.emoji; };
        box.appendChild(img);
    } else {
        box.textContent = food.emoji;
    }
    return box;
}

// ---------- cart ----------
// keep only lines for foods that still exist (a page shown again after an error may carry old lines)
JSON.parse(document.getElementById('cartData').textContent).forEach(function (line) {
    if (line && findFood(line.id)) { cart.push({ id: Number(line.id), qty: Math.min(Number(line.qty) || 1, 20), picks: line.picks || {} }); }
});

function addToCart(id, qty, picks) {
    var key = JSON.stringify(picks);
    var same = cart.find(function (l) { return l.id === id && JSON.stringify(l.picks) === key; });
    if (same) { same.qty = Math.min(same.qty + qty, 20); } else { cart.push({ id: id, qty: qty, picks: picks }); }
    updateBar();
    toast('Added: ' + findFood(id).name);
}
function cartTotal() { return cart.reduce(function (sum, l) { return sum + findFood(l.id).price * l.qty; }, 0); }
function countOf(id) { return cart.reduce(function (n, l) { return n + (l.id === id ? l.qty : 0); }, 0); }

function updateBar() {
    var count = cart.reduce(function (n, l) { return n + l.qty; }, 0);
    $('cartCount').textContent = count;
    $('cartCount').style.display = count > 0 ? 'flex' : 'none';
    $('cartTotal').textContent = money(cartTotal());
    $('viewOrder').disabled = count === 0;
    document.querySelectorAll('.product').forEach(function (card) {        // number badge on each food in the cart
        var n = countOf(Number(card.dataset.id));
        var badge = card.querySelector('.pcount');
        badge.textContent = n;
        badge.style.display = n > 0 ? 'flex' : 'none';
    });
}

function toast(message) {
    var t = $('toast');
    t.textContent = message;
    t.classList.remove('d-none');
    clearTimeout(toast.timer);
    toast.timer = setTimeout(function () { t.classList.add('d-none'); }, 1300);
}

// ---------- screens ----------
function show(view) {
    ['Start', 'Menu', 'Item', 'Review', 'Details'].forEach(function (name) { $('view' + name).classList.toggle('d-none', name !== view); });
    $('kBar').classList.toggle('d-none', view === 'Start');
    if (view === 'Review') { drawReview(); }
    window.scrollTo(0, 0);
}
document.querySelectorAll('[data-go]').forEach(function (b) {
    b.onclick = function () {
        if (b.dataset.go === 'details' && cart.length === 0) { toast('Your order is empty'); return; }
        show({ menu: 'Menu', review: 'Review', details: 'Details' }[b.dataset.go]);
    };
});
$('viewOrder').onclick = function () { show('Review'); };
$('cancelOrder').onclick = function () {
    if (cart.length === 0 || confirm('Cancel this order and remove everything from your cart?')) { cart = []; updateBar(); show('Start'); }
};

// ---------- start screen: Delivery / Pickup ----------
function setType(type) {
    orderType = type;
    $('typeChip').textContent = type === 'Delivery' ? '🛵 Delivery · pay COD' : '🏪 Pickup · pay Cash';
    form.querySelectorAll('input[name=order_type]').forEach(function (r) { r.checked = r.value === type; });
    $('addressBox').style.display = type === 'Delivery' ? 'block' : 'none';
}
document.querySelectorAll('.start-btn').forEach(function (b) { b.onclick = function () { setType(b.dataset.type); show('Menu'); }; });
form.querySelectorAll('input[name=order_type]').forEach(function (r) { r.onchange = function () { setType(r.value); }; });
$('changeType').onclick = function () { show('Start'); };

// ---------- menu screen: category photos + food tiles ----------
function drawMenu() {
    var cats = [];
    MENU.forEach(function (f) { if (cats.indexOf(f.category) === -1) { cats.push(f.category); } });
    if (cats.indexOf(category) === -1) { category = cats[0]; }

    var side = $('cats');
    side.innerHTML = '';
    cats.forEach(function (cat) {
        var first = MENU.find(function (f) { return f.category === cat && f.image; }) || MENU.find(function (f) { return f.category === cat; });
        var b = button('k-cat' + (cat === category ? ' active' : ''), '', function () { category = cat; drawMenu(); });
        b.appendChild(picture(first, 'k-cat-pic'));
        b.appendChild(el('span', 'k-cat-name', cat));
        side.appendChild(b);
    });

    var grid = $('grid');
    grid.innerHTML = '';
    MENU.filter(function (f) { return f.category === category; }).forEach(function (food) {
        var card = el('div', 'product');
        card.dataset.id = food.id;
        card.appendChild(picture(food, 'pimg'));
        card.appendChild(el('div', 'pname', food.name));
        card.appendChild(el('div', 'pprice', money(food.price)));
        card.appendChild(el('span', 'pcount', '0'));
        card.appendChild(el('span', 'pplus', food.groups.length ? '›' : '+'));
        card.onclick = function () {                       // foods with choices open the food screen first
            if (food.groups.length) { openItem(food.id); } else { addToCart(food.id, 1, {}); }
        };
        grid.appendChild(card);
    });
    updateBar();
}

// ---------- food screen ----------
function openItem(id) {
    var food = findFood(id);
    var picks = {};
    var qty = 1;
    var view = $('viewItem');
    view.innerHTML = '';

    var pad = el('div', 'k-pad');
    pad.appendChild(button('k-back', '← Go Back to Menu', function () { show('Menu'); }));

    var layout = el('div', 'k-item');
    layout.appendChild(picture(food, 'k-item-img'));

    var info = el('div', 'k-item-info');
    info.appendChild(el('h2', '', food.name));
    info.appendChild(el('div', 'k-item-price', money(food.price)));
    if (food.description) { info.appendChild(el('p', 'text-muted', food.description)); }

    food.groups.forEach(function (group) {                       // "choose and match" options
        var box = el('div', 'k-group');
        box.appendChild(el('h6', '', group.name.toUpperCase() + ' (choose one)'));
        group.options.forEach(function (option) {
            var label = el('label', 'k-opt');
            var radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = 'pick_' + food.id + '_' + group.name;
            radio.onchange = function () { picks[group.name] = option; };
            label.appendChild(radio);
            label.appendChild(el('span', '', option));
            box.appendChild(label);
        });
        info.appendChild(box);
    });

    var qtyRow = el('div', 'k-qty-row');
    qtyRow.appendChild(el('strong', '', 'Quantity'));
    var stepper = el('div', 'k-stepper');
    var number = el('strong', '', '1');
    var addBtn = el('button', 'k-addbig');
    addBtn.type = 'button';
    function refresh() { number.textContent = qty; addBtn.textContent = 'Add To Order   ' + money(food.price * qty); }
    stepper.appendChild(button('qty-btn', '−', function () { qty = Math.max(1, qty - 1); refresh(); }));
    stepper.appendChild(number);
    stepper.appendChild(button('qty-btn', '+', function () { qty = Math.min(20, qty + 1); refresh(); }));
    qtyRow.appendChild(stepper);
    info.appendChild(qtyRow);

    addBtn.onclick = function () {
        var missing = food.groups.filter(function (g) { return !picks[g.name]; });
        if (missing.length) { toast('Please choose: ' + missing.map(function (g) { return g.name; }).join(', ')); return; }
        addToCart(food.id, qty, picks);
        show('Menu');
    };
    refresh();
    info.appendChild(addBtn);

    layout.appendChild(info);
    pad.appendChild(layout);
    view.appendChild(pad);
    show('Item');
}

// ---------- review screen ----------
function drawReview() {
    var box = $('cartLines');
    box.innerHTML = '';
    if (cart.length === 0) { box.appendChild(el('p', 'text-muted', 'Your order is empty. Go back to the menu and tap some food.')); }

    cart.forEach(function (line, i) {
        var food = findFood(line.id);
        var row = el('div', 'cart-line');
        row.appendChild(picture(food, 'cart-pic'));

        var name = el('div', 'flex-grow-1');
        name.appendChild(el('div', 'fw-bold', food.name));
        if (Object.keys(line.picks).length) { name.appendChild(el('small', 'text-muted', picksText(line.picks))); }

        row.appendChild(name);
        row.appendChild(button('qty-btn', '−', function () { line.qty--; if (line.qty <= 0) { cart.splice(i, 1); } updateBar(); drawReview(); }));
        row.appendChild(el('strong', '', line.qty));
        row.appendChild(button('qty-btn', '+', function () { line.qty = Math.min(20, line.qty + 1); updateBar(); drawReview(); }));
        row.appendChild(el('div', 'cart-price', money(food.price * line.qty)));
        box.appendChild(row);
    });
    $('cartSum').textContent = money(cartTotal());
}

// ---------- send the order ----------
form.addEventListener('submit', function (e) {
    var box = $('clientError');
    if (cart.length === 0) {
        e.preventDefault();
        box.textContent = 'Please tap at least one food to add it to your order.';
        box.classList.remove('d-none');
        show('Menu');
        return;
    }
    box.classList.add('d-none');
    $('cartJson').value = JSON.stringify(cart);
});

setType(orderType);
drawMenu();
show(start.cart ? 'Details' : 'Start');
