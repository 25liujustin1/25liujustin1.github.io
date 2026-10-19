// Home page circuit: a 74HC139 decoder drawn and animated the way Falstad's CircuitJS draws circuits.
// Switches A1 A0 pick one active-low output ~Yn; that LED lights and links to page n.
// Wires are colored by node voltage (0 V gray, 5 V green), and yellow dots move at a speed set by the
// branch current. Page names and links come from the nav buttons (_data/nav.yml), in address order.
// Two drawings of the same circuit: "wide" for desktop, "tall" for phones.
(function () {
  var svg = document.getElementById('sch');
  if (!svg) return;
  var NS = 'http://www.w3.org/2000/svg';

  var navLinks = Array.prototype.slice.call(document.querySelectorAll('.decoder-nav a[data-addr]'));
  var pages = navLinks.map(function (a) {
    return { name: a.getAttribute('data-name').toUpperCase(), href: a.getAttribute('href') };
  });
  var go = document.getElementById('go');
  var clock = document.getElementById('clock');

  // ---------------- circuit values
  var VCC = 5, VF = 2.0, VOL = 0.2, R_LED = 470, R_PD = 10000;
  var I_LED = (VCC - VF - VOL) / R_LED;   // ≈ 5.96 mA
  var I_PD = VCC / R_PD;                  // 0.5 mA

  // ---------------- drawing helpers (everything drawn lands in these lists)
  var wires, grads, leds, switches, defs, info, dotLayer, pool, layout, gradId;

  function el(name, attrs, parent) {
    var n = document.createElementNS(NS, name);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    (parent || svg).appendChild(n);
    return n;
  }
  function pts(list) { return list.map(function (p) { return p[0] + ',' + p[1]; }).join(' '); }
  function text(x, y, str, cls, parent, extra) {
    var attrs = { 'class': cls, x: x, y: y };
    for (var k in extra) attrs[k] = extra[k];
    el('text', attrs, parent).textContent = str;
  }
  // a wire belongs to a node, so it can be colored by that node's voltage
  function wire(node, list) {
    wires.push({ node: node, el: el('polyline', { points: pts(list), fill: 'none', 'stroke-width': 3, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }) });
  }
  function junction(x, y, node) { wires.push({ node: node, fill: true, el: el('circle', { cx: x, cy: y, r: 4.5 }) }); }
  // two-terminal parts shade from one end's voltage color to the other's, like Falstad
  function gradient(n1, n2, x1, y1, x2, y2) {
    var id = 'g' + (gradId++);
    var g = el('linearGradient', { id: id, gradientUnits: 'userSpaceOnUse', x1: x1, y1: y1, x2: x2, y2: y2 }, defs);
    grads.push({ a: el('stop', { offset: '0' }, g), b: el('stop', { offset: '1' }, g), n1: n1, n2: n2 });
    return 'url(#' + id + ')';
  }
  function hot(key, tag, attrs) {
    attrs = attrs || {};
    attrs['class'] = 'hot';
    attrs['data-info'] = key;
    return el(tag || 'g', attrs);
  }
  function hit(parent, x, y, w, h) { el('rect', { 'class': 'hit', x: x, y: y, width: w, height: h, rx: 4 }, parent); }
  function resistor(x1, y1, x2, y2, n1, n2, parent) {
    var dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy), px = -dy / len * 8, py = dx / len * 8;
    var d = 'M' + x1 + ' ' + y1, steps = 8;
    for (var i = 1; i < steps; i++) {
      var s = i % 2 ? 1 : -1;
      d += ' L' + (x1 + dx * i / steps + px * s) + ' ' + (y1 + dy * i / steps + py * s);
    }
    d += ' L' + x2 + ' ' + y2;
    el('path', { d: d, fill: 'none', stroke: gradient(n1, n2, x1, y1, x2, y2), 'stroke-width': 3, 'stroke-linejoin': 'round' }, parent);
  }
  function ground(x, y) {
    el('path', { 'class': 'sym gnd', d: 'M' + (x - 12) + ' ' + y + ' H' + (x + 12) + ' M' + (x - 8) + ' ' + (y + 5) + ' H' + (x + 8) + ' M' + (x - 4) + ' ' + (y + 10) + ' H' + (x + 4) });
  }
  // SPST switch to +5 V: fixed contact at yTop, lever pivots at yBot
  function spst(key, x, yTop, yBot) {
    var name = key.toUpperCase();
    var g = el('g', { 'class': 'hot', tabindex: 0, role: 'switch', 'aria-label': 'Address bit ' + name, 'data-info': 'sw-' + key });
    hit(g, x - 26, yTop - 10, 52, yBot - yTop + 20);
    el('circle', { cx: x, cy: yTop, r: 3.5, 'class': 'term' }, g);
    el('circle', { cx: x, cy: yBot, r: 3.5, 'class': 'term' }, g);
    var lever = el('line', { 'stroke-width': 3, 'stroke-linecap': 'round', x1: x, y1: yBot, x2: x, y2: yTop }, g);
    text(x - 30, (yTop + yBot) / 2 + 4, name, 't', g, { 'text-anchor': 'end' });
    switches[key] = { g: g, lever: lever, x: x, yTop: yTop };
  }
  // LED drawn anode at (0,0), cathode at (0,24); placed with translate + rotate
  function led(n, x, y, rot, parent, nodeK, nodeY) {
    var g = el('g', { transform: 'translate(' + x + ' ' + y + ') rotate(' + rot + ')' }, parent);
    var glow = el('circle', { cx: 0, cy: 12, r: 26, fill: 'url(#ledglow)', opacity: 0 }, g);
    var tri = el('path', { d: 'M-12 0 H12 L0 24 Z', 'stroke-width': 2.5, 'stroke-linejoin': 'round', stroke: gradient(nodeK, nodeY, 0, 0, 0, 24) }, g);
    el('line', { x1: -12, y1: 24, x2: 12, y2: 24, 'stroke-width': 2.5, stroke: gradient(nodeY, nodeY, -12, 24, 12, 24) }, g);
    el('path', { 'class': 'sym', d: 'M14 5 l8 -8 m-5 0 h5 v5 M14 15 l8 -8 m-5 0 h5 v5', 'stroke-width': 1.5 }, g);
    leds[n] = { tri: tri, glow: glow };
  }
  function pageLink(n) {
    return hot('led-' + n, 'a', { href: pages[n].href, 'data-addr': n, 'aria-label': pages[n].name + ' (address ' + n.toString(2).padStart(2, '0') + ')' });
  }

  // ---------------- the two drawings
  var LAYOUTS = {
    // desktop: rail on top, LEDs hang down from it into U1's outputs
    wide: {
      viewBox: '0 0 1000 470',
      info: [560, 400],
      draw: function () {
        var RAIL = 50, COLS = [528, 654, 780, 906], ROWS = [200, 240, 280, 320], A1 = 160, A0 = 250;
        text(30, RAIL + 4, '+5V', 't');
        wire('VCC', [[66, RAIL], [COLS[3], RAIL]]);
        el('circle', { cx: 66, cy: RAIL, r: 4, 'class': 'term' });

        // address switches with 10k pull-downs
        [['a1', A1], ['a0', A0]].forEach(function (s) { wire('VCC', [[s[1], RAIL], [s[1], 80]]); spst(s[0], s[1], 80, 120); });
        wire('A0', [[A0, 120], [A0, 225]]);
        wire('A0', [[A0, 200], [340, 200]]);
        junction(A0, 200, 'A0');
        var r2 = hot('r-a0'); hit(r2, A0 - 16, 222, 70, 56);
        resistor(A0, 225, A0, 275, 'A0', 'GND', r2);
        text(A0 + 14, 248, 'R2', 't', r2); text(A0 + 14, 262, '10k', 't-dim', r2);
        wire('GND', [[A0, 275], [A0, 290]]); ground(A0, 290);
        wire('A1', [[A1, 120], [A1, 365]]);
        wire('A1', [[A1, 340], [290, 340], [290, 280], [340, 280]]);
        junction(A1, 340, 'A1');
        var r1 = hot('r-a1'); hit(r1, A1 - 16, 362, 70, 56);
        resistor(A1, 365, A1, 415, 'A1', 'GND', r1);
        text(A1 + 14, 388, 'R1', 't', r1); text(A1 + 14, 402, '10k', 't-dim', r1);
        wire('GND', [[A1, 415], [A1, 430]]); ground(A1, 430);

        // U1
        var u1 = hot('u1'); hit(u1, 316, 124, 168, 250);
        el('rect', { 'class': 'sym', x: 340, y: 140, width: 120, height: 220 }, u1);
        text(400, 168, '74HC139', 't', u1, { 'text-anchor': 'middle' });
        text(400, 184, 'U1', 't-dim', u1, { 'text-anchor': 'middle' });
        text(347, 204, 'A0', 't-dim', u1); text(347, 284, 'A1', 't-dim', u1);
        ROWS.forEach(function (y, n) { text(453, y + 4, 'Y' + n, 't-dim ol', u1, { 'text-anchor': 'end' }); });
        text(370, 352, 'E', 't-dim ol', u1, { 'text-anchor': 'middle' });
        text(430, 352, 'GND', 't-dim', u1, { 'text-anchor': 'middle' });
        wire('VCC', [[400, RAIL], [400, 140]]);
        text(406, 132, 'VCC', 't-dim');
        wire('GND', [[370, 360], [370, 385]]); ground(370, 385);
        wire('GND', [[430, 360], [430, 385]]); ground(430, 385);

        // outputs: +5V → R → LED → ~Yn
        COLS.forEach(function (x, n) {
          var row = ROWS[n], K = 'K' + n, Y = 'Y' + n;
          wire('VCC', [[x, RAIL], [x, 70]]);
          var r = hot('r-led-' + n); hit(r, x - 16, 66, 66, 58);
          resistor(x, 70, x, 120, 'VCC', K, r);
          text(x + 14, 93, 'R' + (3 + n), 't', r); text(x + 14, 107, '470', 't-dim', r);
          wire(K, [[x, 120], [x, 145]]);
          var a = pageLink(n); hit(a, x - 20, 128, 98, 56);
          led(n, x, 145, 0, a, K, Y);
          text(x + 26, 150, 'D' + (n + 1), 't-dim', a);
          text(x + 26, 172, pages[n].name, 't-page', a);
          wire(Y, [[x, 169], [x, row], [460, row]]);
        });

        return function paths(sel, a1, a0) {
          var x = COLS[sel];
          var list = [
            [[[66, RAIL], [A1, RAIL]], I_LED + (a1 + a0) * I_PD],
            [[[A1, RAIL], [A0, RAIL]], I_LED + a0 * I_PD],
            [[[A0, RAIL], [x, RAIL]], I_LED],
            [[[x, RAIL], [x, ROWS[sel]], [460, ROWS[sel]]], I_LED],
            [[[430, 360], [430, 385]], I_LED]
          ];
          if (a0) list.push([[[A0, RAIL], [A0, 290]], I_PD]);
          if (a1) list.push([[[A1, RAIL], [A1, 430]], I_PD]);
          return list;
        };
      }
    },

    // phone: rail across the top and down the right side, LEDs lie sideways into U1's outputs
    tall: {
      viewBox: '0 0 400 600',
      info: [12, 522],
      draw: function () {
        var RAIL = 30, RIGHT = 370, ROWS = [230, 290, 350, 410], A1 = 70, A0 = 140;
        text(8, RAIL + 4, '+5V', 't');
        wire('VCC', [[40, RAIL], [RIGHT, RAIL], [RIGHT, ROWS[3]]]);
        el('circle', { cx: 40, cy: RAIL, r: 4, 'class': 'term' });

        [['a1', A1], ['a0', A0]].forEach(function (s) { wire('VCC', [[s[1], RAIL], [s[1], 60]]); spst(s[0], s[1], 60, 100); });
        wire('A0', [[A0, 100], [A0, 240]]);
        wire('A0', [[A0, 220], [180, 220]]);
        junction(A0, 220, 'A0');
        var r2 = hot('r-a0'); hit(r2, A0 - 16, 237, 56, 56);
        resistor(A0, 240, A0, 290, 'A0', 'GND', r2);
        text(A0 + 14, 263, 'R2', 't', r2); text(A0 + 14, 277, '10k', 't-dim', r2);
        wire('GND', [[A0, 290], [A0, 302]]); ground(A0, 302);
        wire('A1', [[A1, 100], [A1, 400]]);
        wire('A1', [[A1, 380], [180, 380]]);
        junction(A1, 380, 'A1');
        var r1 = hot('r-a1'); hit(r1, A1 - 16, 397, 56, 56);
        resistor(A1, 400, A1, 450, 'A1', 'GND', r1);
        text(A1 + 14, 423, 'R1', 't', r1); text(A1 + 14, 437, '10k', 't-dim', r1);
        wire('GND', [[A1, 450], [A1, 462]]); ground(A1, 462);

        var u1 = hot('u1'); hit(u1, 176, 166, 78, 288);
        el('rect', { 'class': 'sym', x: 180, y: 170, width: 70, height: 280 }, u1);
        text(215, 196, '74HC139', 't', u1, { 'text-anchor': 'middle' });
        text(215, 212, 'U1', 't-dim', u1, { 'text-anchor': 'middle' });
        text(186, 224, 'A0', 't-dim', u1); text(186, 384, 'A1', 't-dim', u1);
        ROWS.forEach(function (y, n) { text(244, y + 4, 'Y' + n, 't-dim ol', u1, { 'text-anchor': 'end' }); });
        text(197, 442, 'E', 't-dim ol', u1, { 'text-anchor': 'middle' });
        text(233, 442, 'GND', 't-dim', u1, { 'text-anchor': 'middle' });
        wire('VCC', [[215, RAIL], [215, 170]]);
        text(221, 162, 'VCC', 't-dim');
        wire('GND', [[197, 450], [197, 470]]); ground(197, 470);
        wire('GND', [[233, 450], [233, 470]]); ground(233, 470);

        // outputs: rail → R → LED → ~Yn, right to left
        ROWS.forEach(function (y, n) {
          var K = 'K' + n, Y = 'Y' + n;
          if (n < 3) junction(RIGHT, y, 'VCC');
          wire('VCC', [[350, y], [RIGHT, y]]);
          var r = hot('r-led-' + n); hit(r, 302, y - 12, 54, 46);
          resistor(350, y, 304, y, 'VCC', K, r);
          text(327, y + 28, 'R' + (3 + n) + ' 470', 't-dim', r, { 'text-anchor': 'middle' });
          wire(K, [[296, y], [304, y]]);
          var a = pageLink(n); hit(a, 256, y - 32, 96, 22); hit(a, 256, y - 12, 44, 46);
          led(n, 296, y, 90, a, K, Y);
          text(262, y - 16, pages[n].name, 't-page', a);
          text(274, y + 30, 'D' + (n + 1), 't-dim', a, { 'text-anchor': 'middle' });
          wire(Y, [[250, y], [272, y]]);
        });

        return function paths(sel, a1, a0) {
          var y = ROWS[sel];
          var list = [
            [[[40, RAIL], [A1, RAIL]], I_LED + (a1 + a0) * I_PD],
            [[[A1, RAIL], [A0, RAIL]], I_LED + a0 * I_PD],
            [[[A0, RAIL], [RIGHT, RAIL], [RIGHT, y], [250, y]], I_LED],
            [[[233, 450], [233, 470]], I_LED]
          ];
          if (a0) list.push([[[A0, RAIL], [A0, 302]], I_PD]);
          if (a1) list.push([[[A1, RAIL], [A1, 462]], I_PD]);
          return list;
        };
      }
    }
  };

  // ---------------- state, solved into node voltages and branch currents
  var a1 = 0, a0 = 0, hoverInfo = null, V = {}, paths = [], pathsFor;

  function solve() {
    var sel = a1 * 2 + a0;
    V.VCC = VCC; V.GND = 0; V.A0 = a0 ? VCC : 0; V.A1 = a1 ? VCC : 0;
    for (var n = 0; n < 4; n++) {
      var on = n === sel;
      V['Y' + n] = on ? VOL : VCC;
      V['K' + n] = on ? VOL + VF : VCC;   // anode drops to Vol + Vf while conducting
    }
    paths = pathsFor(sel, a1, a0).map(function (p) { return { list: p[0], i: p[1], len: lengthOf(p[0]) }; });
    return sel;
  }

  function color(v) {
    // Falstad's scale: 0 V gray, positive voltages toward green
    var f = Math.max(0, Math.min(1, v / VCC));
    return 'rgb(' + Math.round(127 * (1 - f)) + ',' + Math.round(127 + 128 * f) + ',' + Math.round(127 * (1 - f)) + ')';
  }

  function mA(i) { return (i * 1000).toFixed(2) + ' mA'; }
  function describe(key, sel) {
    var m, on;
    if (!key || key === 'u1') {
      return ['U1 74HC139 (one half, ~E = 0 V)',
        'A1 A0 = ' + a1 + a0 + '  →  ~Y' + sel + ' = ' + VOL.toFixed(1) + ' V, others 5 V',
        'sinking ' + mA(I_LED) + ' through D' + (sel + 1)];
    }
    if ((m = key.match(/^sw-(a[01])$/))) {
      on = m[1] === 'a1' ? a1 : a0;
      return ['switch ' + m[1].toUpperCase() + ' (' + (on ? 'closed' : 'open') + ')',
        m[1].toUpperCase() + ' = ' + (on ? '5.00 V' : '0.00 V (pulled down)'),
        'I = ' + (on ? mA(I_PD) : '0 mA') + ' · click to toggle'];
    }
    if ((m = key.match(/^r-(a[01])$/))) {
      on = m[1] === 'a1' ? a1 : a0;
      return ['resistor ' + (m[1] === 'a1' ? 'R1' : 'R2') + ' 10 kΩ (pull-down)',
        'Vd = ' + (on ? '5.00' : '0.00') + ' V', 'I = ' + (on ? mA(I_PD) : '0 mA')];
    }
    if ((m = key.match(/^r-led-(\d)$/))) {
      on = +m[1] === sel;
      return ['resistor R' + (3 + +m[1]) + ' 470 Ω',
        'Vd = ' + (on ? (VCC - VF - VOL).toFixed(2) : '0.00') + ' V', 'I = ' + (on ? mA(I_LED) : '0 mA')];
    }
    if ((m = key.match(/^led-(\d)$/))) {
      var n = +m[1];
      on = n === sel;
      return ['LED D' + (n + 1) + ' → ' + pages[n].name,
        on ? 'Vf = ' + VF.toFixed(2) + ' V, I = ' + mA(I_LED) : 'off (both ends at 5 V)',
        'address ' + n.toString(2).padStart(2, '0') + ' · click to open'];
    }
    return [];
  }

  function render() {
    var sel = solve();
    wires.forEach(function (w) { w.el.setAttribute(w.fill ? 'fill' : 'stroke', color(V[w.node])); });
    grads.forEach(function (g) {
      g.a.setAttribute('stop-color', color(V[g.n1]));
      g.b.setAttribute('stop-color', color(V[g.n2]));
    });
    ['a1', 'a0'].forEach(function (k) {
      var on = k === 'a1' ? a1 : a0, s = switches[k];
      s.lever.setAttribute('x2', on ? s.x : s.x + 20);
      s.lever.setAttribute('y2', on ? s.yTop : s.yTop + 8);
      s.lever.setAttribute('stroke', color(V[k.toUpperCase()]));
      s.g.setAttribute('aria-checked', on ? 'true' : 'false');
    });
    leds.forEach(function (l, n) {
      l.tri.setAttribute('fill', n === sel ? '#3dff7a' : 'none');
      l.glow.setAttribute('opacity', n === sel ? 1 : 0);
    });
    navLinks.forEach(function (a, n) { a.classList.toggle('sel', n === sel); });
    var lines = describe(hoverInfo, sel);
    info.forEach(function (t, i) { t.textContent = lines[i] || ''; });
    if (go) {
      go.href = pages[sel].href;
      go.textContent = 'Go to ' + navLinks[sel].getAttribute('data-name') + ' →';
    }
  }

  function setAddr(n) { a1 = (n >> 1) & 1; a0 = n & 1; render(); }

  function build(name) {
    layout = LAYOUTS[name];
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    svg.setAttribute('viewBox', layout.viewBox);
    svg.setAttribute('class', name);
    wires = []; grads = []; leds = []; switches = {}; pool = []; gradId = 0;
    defs = el('defs', {});
    var lg = el('radialGradient', { id: 'ledglow' }, defs);
    el('stop', { offset: '0', 'stop-color': '#7dffa6', 'stop-opacity': 0.9 }, lg);
    el('stop', { offset: '1', 'stop-color': '#3dff7a', 'stop-opacity': 0 }, lg);
    pathsFor = layout.draw();
    info = [0, 1, 2].map(function (i) { return el('text', { 'class': 'info', x: layout.info[0], y: layout.info[1] + i * 18 }); });
    dotLayer = el('g', { 'aria-hidden': 'true' });

    ['a1', 'a0'].forEach(function (k) {
      var g = switches[k].g;
      function flip() { if (k === 'a1') a1 ^= 1; else a0 ^= 1; render(); }
      g.addEventListener('click', flip);
      g.addEventListener('keydown', function (e) { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); flip(); } });
    });
    svg.querySelectorAll('[data-info]').forEach(function (node) {
      node.addEventListener('mouseenter', function () { hoverInfo = node.getAttribute('data-info'); render(); });
      node.addEventListener('mouseleave', function () { hoverInfo = null; render(); });
    });
    svg.querySelectorAll('a[data-addr]').forEach(function (a) {
      var n = +a.getAttribute('data-addr');
      a.addEventListener('mouseenter', function () { setAddr(n); });
      a.addEventListener('focus', function () { setAddr(n); });
    });
    render();
  }

  navLinks.forEach(function (a, n) {
    a.addEventListener('mouseenter', function () { setAddr(n); });
    a.addEventListener('focus', function () { setAddr(n); });
  });

  var phone = window.matchMedia('(max-width: 640px)');
  function pick() { build(phone.matches ? 'tall' : 'wide'); }
  if (phone.addEventListener) phone.addEventListener('change', pick); else phone.addListener(pick);
  pick();

  // ---------------- current dots: speed follows current, like Falstad
  var SPACING = 16;
  function speed(i) { return 18 + 30 * Math.log2(1 + i * 1000 * 2); }   // px/s from amps
  function lengthOf(list) {
    var s = 0;
    for (var i = 1; i < list.length; i++) s += Math.hypot(list[i][0] - list[i - 1][0], list[i][1] - list[i - 1][1]);
    return s;
  }
  function along(list, d) {
    for (var i = 1; i < list.length; i++) {
      var dx = list[i][0] - list[i - 1][0], dy = list[i][1] - list[i - 1][1], len = Math.hypot(dx, dy);
      if (d <= len) return [list[i - 1][0] + dx * d / len, list[i - 1][1] + dy * d / len];
      d -= len;
    }
    return list[list.length - 1];
  }
  var still = window.matchMedia('(prefers-reduced-motion: reduce)');
  var t0 = performance.now();
  function frame(now) {
    var t = (now - t0) / 1000, used = 0;
    if (!still.matches) {
      paths.forEach(function (p) {
        for (var d = (t * speed(p.i)) % SPACING; d < p.len; d += SPACING) {
          var xy = along(p.list, d);
          var c = pool[used] || (pool[used] = el('circle', { 'class': 'dot', r: 2.6 }, dotLayer));
          c.setAttribute('cx', xy[0]); c.setAttribute('cy', xy[1]); c.style.display = '';
          used++;
        }
      });
    }
    for (var k = used; k < pool.length; k++) pool[k].style.display = 'none';
    // sim time runs 1000x slower than real time, like Falstad, and is shown with SI units the way Falstad does
    var sim = t * 1e-3;
    if (clock) clock.textContent = 't = ' + (sim < 1 ? (sim * 1e3).toFixed(2) + ' ms' : sim.toFixed(4) + ' s');
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
