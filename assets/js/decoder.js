// Drives the home page decoder: a 74HC139 with ~1E tied low.
// Output ~Yn goes LOW (and its LED lights) when the address A1A0 equals n.
// Works with any board SVG that provides the hooks listed in _includes/boards/decoder-hand.svg.
(function () {
  var svg = document.getElementById('pcb');
  if (!svg) return;

  var swA1 = document.getElementById('sw-a1');
  var swA0 = document.getElementById('sw-a0');
  var outs = Array.prototype.slice.call(svg.querySelectorAll('.out[data-addr]'));
  var navLinks = Array.prototype.slice.call(document.querySelectorAll('.decoder-nav a[data-addr]'));
  var truthRows = Array.prototype.slice.call(document.querySelectorAll('.truth tr[data-addr]'));
  var logic = document.getElementById('logic');
  var go = document.getElementById('go');
  var a1 = 0, a0 = 0;

  function byAddr(list, n) {
    return list.filter(function (node) { return +node.getAttribute('data-addr') === n; })[0];
  }
  function toggleClass(id, cls, on) {
    var node = document.getElementById(id);
    if (node) node.classList.toggle(cls, on);
  }

  function render() {
    var sel = a1 * 2 + a0;
    [[swA1, a1], [swA0, a0]].forEach(function (pair) {
      if (!pair[0]) return;
      pair[0].classList.toggle('on', !!pair[1]);
      pair[0].setAttribute('aria-checked', pair[1] ? 'true' : 'false');
    });
    toggleClass('n-a1', 'hi', !!a1);
    toggleClass('n-a0', 'hi', !!a0);
    for (var n = 0; n < 4; n++) {
      var on = n === sel;
      toggleClass('n-y' + n, 'active', on);
      toggleClass('n-k' + n, 'active', on);
      [byAddr(outs, n), byAddr(navLinks, n), byAddr(truthRows, n)].forEach(function (node) {
        if (node) node.classList.toggle('sel', on);
      });
    }
    var target = byAddr(outs, sel) || byAddr(navLinks, sel);
    var name = target ? target.getAttribute('data-name') : '';
    if (logic) {
      logic.innerHTML = 'A1 A0 = <b>' + a1 + a0 + '</b> → <em><span class="ol">Y' + sel + '</span> LOW</em> → D' + (sel + 1) + ' on → ' + name.toUpperCase();
    }
    if (go && target) {
      go.href = target.getAttribute('href');
      go.textContent = 'Go to ' + name + ' →';
    }
  }

  function setAddr(n) { a1 = (n >> 1) & 1; a0 = n & 1; render(); }
  function flip(which) { if (which === 'a1') a1 ^= 1; else a0 ^= 1; render(); }

  [[swA1, 'a1'], [swA0, 'a0']].forEach(function (pair) {
    if (!pair[0]) return;
    pair[0].addEventListener('click', function () { flip(pair[1]); });
    pair[0].addEventListener('keydown', function (e) {
      if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); flip(pair[1]); }
    });
  });

  // hovering or focusing any page (board row, nav button, truth table row) sets the address
  outs.concat(navLinks, truthRows).forEach(function (node) {
    var n = +node.getAttribute('data-addr');
    node.addEventListener('mouseenter', function () { setAddr(n); });
    node.addEventListener('focus', function () { setAddr(n); });
  });

  render();
})();
