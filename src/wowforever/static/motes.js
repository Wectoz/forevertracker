(function () {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var layer = document.createElement('div');
  layer.className = 'motes';
  layer.setAttribute('aria-hidden', 'true');
  for (var i = 0; i < 24; i++) {
    var m = document.createElement('span'), d = 12 + Math.random() * 16, size = 2 + Math.random() * 2;
    m.className = 'mote';
    m.style.left = (Math.random() * 100).toFixed(2) + 'vw';
    m.style.width = m.style.height = size.toFixed(1) + 'px';
    m.style.animationDuration = d.toFixed(1) + 's';
    m.style.animationDelay = (-Math.random() * d).toFixed(1) + 's';  // start mid-flight so the page isn't empty at load
    m.style.setProperty('--drift', (Math.random() * 80 - 40).toFixed(0) + 'px');
    layer.appendChild(m);
  }
  document.body.appendChild(layer);
})();
