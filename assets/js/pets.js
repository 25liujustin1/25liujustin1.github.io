// Easter egg: desktop pets, run by eSheep (assets/vendor/esheep, GPL-3.0), that walk on the site's panels and cards.
// The chip button, or typing "555", releases a 555 timer; about 1 in 10 button presses gives a 16-pin 74HC139
// (the home page's decoder) instead, but only one, and it's guaranteed by the last slot. Typing "139" asks for one. Both are drawn by tools/make_ic_pet.py into
// assets/pets/. Like bugs, they scurry in stop-and-go bursts, scatter from the cursor (spooking each other), and
// stop face to face when they meet. Released pets follow the visitor to other pages for the rest of the browser
// session; reloading the page clears them. Off on phones, where a pet would sit on top of the text.
(function () {
  var script = document.currentScript;
  var VENDOR = script.getAttribute('data-vendor');   // folder holding esheep.js
  var PETS = {
    ic555: script.getAttribute('data-pets') + 'ic555.xml',
    hc139: script.getAttribute('data-pets') + 'hc139.xml'
  };
  var RARE = 0.1;   // chance that the button gives a 74HC139 instead of a 555
  var KEY = 'pets', MAX = 8;
  // what pets can walk on, as CSS selectors
  var GROUND = ['main.wrap', '.ds', '.card', '.frame', '.decoder-nav a', '.status .go', '.btn', '.contact > div'];

  var phone = window.matchMedia('(max-width: 640px)');
  if (phone.matches) return;

  function released() { try { return JSON.parse(sessionStorage.getItem(KEY)) || []; } catch (e) { return []; } }
  function save(list) { try { sessionStorage.setItem(KEY, JSON.stringify(list)); } catch (e) {} }

  var loading = null;
  function load() {
    return loading || (loading = new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = VENDOR + 'esheep.js';
      s.onload = resolve; s.onerror = reject;
      document.head.appendChild(s);
    }));
  }
  var pets = [];
  function spawn(name) {
    return load().then(function () {
      /* global eSheep */
      var pet = new eSheep({ allowPopup: 'no', collisions: GROUND });
      pet.Start(PETS[name]);
      pets.push(pet);
    });
  }

  // Like bugs, pets scatter when the cursor comes close: they run the other way, then freeze.
  // Only while they're up and about; one that's falling, knocked out or playing dead stays put.
  // A pet that runs spooks the others near it, which run the same way (and can spook more), like cockroaches.
  var NEAR = 80, SPOOK = 130, CALM_MS = 1200;
  var CAN_FLEE = /^(walk|scurry|freeze|idle|turn|sleep|wake|magic smoke|startled|meet)/;
  var pending = null;
  function anim(pet) { return pet.animationNode ? pet.animationNode.getElementsByTagName('name')[0].textContent : ''; }
  function centre(pet) { return [pet.imageX + pet.imageW / 2, pet.imageY + pet.imageH / 2]; }
  function flee(pet, dir, now) {
    if (pet.dragging || now - (pet.fledAt || 0) < CALM_MS || !CAN_FLEE.test(anim(pet))) return false;
    if (!pet.Play('flee ' + dir)) return false;
    pet.fledAt = now;
    return true;
  }
  function scatter(cx, cy) {
    var now = Date.now(), running = [];
    pets.forEach(function (pet) {
      var c = centre(pet);
      if (Math.hypot(cx - c[0], cy - c[1]) <= NEAR && flee(pet, cx > c[0] ? 'left' : 'right', now)) {
        running.push([pet, cx > c[0] ? 'left' : 'right']);
      }
    });
    while (running.length) {
      var r = running.shift(), a = centre(r[0]);
      pets.forEach(function (pet) {
        var b = centre(pet);
        if (pet !== r[0] && Math.hypot(a[0] - b[0], a[1] - b[1]) <= SPOOK && flee(pet, r[1], now)) running.push([pet, r[1]]);
      });
    }
  }

  // Two pets walking into each other on the same ledge stop face to face, reach out like ants, and turn back.
  var MOVING = /^(walk|scurry) (left|right)$/, PAD = 4, MEET_MS = 4000;
  function meetings() {
    var now = Date.now();
    pets.forEach(function (a) {
      pets.forEach(function (b) {
        if (a === b || a.imageX > b.imageX) return;                       // a is the one on the left
        var ma = MOVING.exec(anim(a)), mb = MOVING.exec(anim(b));
        if (!ma || !mb || ma[2] !== 'right' || mb[2] !== 'left') return;  // only when walking toward each other
        if (Math.abs((a.imageY + a.imageH) - (b.imageY + b.imageH)) > 3) return;   // on the same ledge
        var gap = (b.imageX + PAD) - (a.imageX + a.imageW - PAD);
        if (gap > 6 || gap < -12) return;
        if (now - (a.metAt || 0) < MEET_MS || now - (b.metAt || 0) < MEET_MS) return;
        a.metAt = b.metAt = now;
        a.Play('meet right');
        b.Play('meet left');
      });
    });
  }
  setInterval(function () { if (pets.length > 1) meetings(); }, 100);
  document.addEventListener('mousemove', function (e) {
    if (!pets.length || pending) return;
    pending = requestAnimationFrame(function () { pending = null; scatter(e.clientX, e.clientY); });
  });
  function release(name) {
    var list = released();
    if (list.length >= MAX) return;
    list.push(name);
    save(list);
    spawn(name);
  }

  // Bring back the pets released on earlier pages, but not after a reload: reloading is how people clear them.
  var nav = performance.getEntriesByType && performance.getEntriesByType('navigation')[0];
  if (nav && nav.type === 'reload') save([]);
  released().forEach(function (name) { if (PETS[name]) spawn(name); });

  // The button gives at most one 139, and always one by the time the pets are at their limit:
  // if none has turned up by the last free slot, that one is the 139.
  function fromButton() {
    var list = released();
    if (list.indexOf('hc139') >= 0) return 'ic555';
    return list.length === MAX - 1 || Math.random() < RARE ? 'hc139' : 'ic555';
  }
  document.querySelectorAll('[data-pet]').forEach(function (b) {
    b.hidden = false;
    b.addEventListener('click', function () { release(fromButton()); });
  });

  var typed = '';
  document.addEventListener('keydown', function (e) {
    if (e.target.closest && e.target.closest('input, textarea, [contenteditable]')) return;
    typed = (typed + e.key.toLowerCase()).slice(-3);
    if (typed === '555') { typed = ''; release('ic555'); }
    if (typed === '139') { typed = ''; release('hc139'); }
  });
})();
