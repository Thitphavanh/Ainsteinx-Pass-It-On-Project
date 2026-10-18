// ---------- release media on the desk: floppy 1991, CD 2000, USB 2008 ----------
const eras = new THREE.Group(); hero.add(eras);
const S4 = 4.22;
function labelTex(lines, w = 512, h = 256, bg = '#f4f1ea', fg = '#1b2b44') { return ctex(w, h, (g) => { g.fillStyle = bg; g.fillRect(0, 0, w, h); g.strokeStyle = 'rgba(40,80,160,0.25)'; for (let y = 60; y < h; y += 34) { g.beginPath(); g.moveTo(16, y); g.lineTo(w - 16, y); g.stroke(); }
  g.fillStyle = fg; g.textAlign = 'center'; lines.forEach(([txt, size, y, font]) => { g.font = `${font || 'bold'} ${size}px "DejaVu Sans", sans-serif`; g.fillText(txt, w / 2, y); }); }); }
const floppy = new THREE.Group(); eras.add(floppy);
{ const W = 0.09 * S4, D = 0.094 * S4, T = 0.0033 * S4; const body = new THREE.Mesh(new RoundedBoxGeometry(W, D, T, 3, 0.004), new THREE.MeshPhysicalMaterial({color: 0x1d2433, roughness: 0.38, clearcoat: 0.3})); body.position.z = T / 2; body.castShadow = body.receiveShadow = true; floppy.add(body);
  const shut = new THREE.Mesh(new RoundedBoxGeometry(W * 0.52, D * 0.3, T * 1.08, 2, 0.002), new THREE.MeshStandardMaterial({color: 0xc9cdd3, metalness: 0.95, roughness: 0.22})); shut.position.set(-W * 0.06, D * 0.33, T / 2); floppy.add(shut);
  const win = new THREE.Mesh(new THREE.BoxGeometry(W * 0.12, D * 0.18, T * 1.1), new THREE.MeshStandardMaterial({color: 0x0b0d12})); win.position.set(-W * 0.06, D * 0.34, T / 2 + 0.001); floppy.add(win);
  const lab = new THREE.Mesh(new THREE.PlaneGeometry(W * 0.8, D * 0.46), new THREE.MeshStandardMaterial({map: labelTex([['Python 0.9.0', 64, 110], ['alt.sources  ·  Feb 1991', 34, 170, 'normal'], ['CWI Amsterdam', 30, 220, 'italic']]), roughness: 0.8}));
  lab.position.set(0, -D * 0.2, T + 0.0012); floppy.add(lab); }
floppy.position.set(-1.05, -1.25, 0.004); floppy.rotation.z = 0.25;
const cd = new THREE.Group(); eras.add(cd);
{ const R = 0.06 * S4; const caseM = new THREE.MeshPhysicalMaterial({color: 0xffffff, transmission: 0.92, roughness: 0.05, thickness: 0.02, transparent: true, opacity: 0.35, clearcoat: 1});
  const cs = new THREE.Mesh(new RoundedBoxGeometry(0.142 * S4, 0.125 * S4, 0.01 * S4, 2, 0.006), caseM); cs.position.z = 0.005 * S4; cd.add(cs);
  const shape = new THREE.Shape(); shape.absarc(0, 0, R, 0, Math.PI * 2); const hole = new THREE.Path(); hole.absarc(0, 0, 0.0075 * S4, 0, Math.PI * 2, true); shape.holes.push(hole);
  const disc = new THREE.Mesh(new THREE.ExtrudeGeometry(shape, {depth: 0.0012 * S4, bevelEnabled: false, curveSegments: 96}), new THREE.MeshPhysicalMaterial({color: 0xdfe4ea, metalness: 1, roughness: 0.12, iridescence: 1, iridescenceIOR: 1.6, iridescenceThicknessRange: [200, 900]}));
  disc.position.set(0.04, 0.03, 0.0105 * S4); disc.rotation.z = 0.3; disc.castShadow = true; cd.add(disc);
  const top = new THREE.Mesh(new THREE.RingGeometry(0.02 * S4, R * 0.98, 96), new THREE.MeshStandardMaterial({map: ctex(512, 512, (g, w, h) => { const gr = g.createLinearGradient(0, 0, w, h); gr.addColorStop(0, '#2f5fa8'); gr.addColorStop(1, '#f2c84b'); g.fillStyle = gr; g.fillRect(0, 0, w, h);
    g.fillStyle = '#fff'; g.textAlign = 'center'; g.font = 'bold 56px "DejaVu Sans", sans-serif'; g.fillText('Python 2.0', w / 2, 120); g.font = '30px "DejaVu Sans", sans-serif'; g.fillText('October 2000', w / 2, 420); }), roughness: 0.5}));
  top.position.set(0.04, 0.03, 0.0105 * S4 + 0.0012 * S4 + 0.0005); top.rotation.z = 0.3; cd.add(top); }
cd.position.set(0.0, -1.35, 0.004); cd.rotation.z = -0.12;
const usb = new THREE.Group(); eras.add(usb);
{ const b = new THREE.Mesh(new RoundedBoxGeometry(0.058 * S4, 0.02 * S4, 0.009 * S4, 4, 0.012), new THREE.MeshPhysicalMaterial({color: 0x15161a, roughness: 0.3, clearcoat: 0.6})); b.position.z = 0.0045 * S4; b.castShadow = true; usb.add(b);
  const con = new THREE.Mesh(new THREE.BoxGeometry(0.012 * S4, 0.012 * S4, 0.0045 * S4), new THREE.MeshStandardMaterial({color: 0xd0d4da, metalness: 1, roughness: 0.2})); con.position.set(0.035 * S4, 0, 0.0045 * S4); usb.add(con);
  const led = glow(0x4aa0ff, 0.05, 0.9); led.position.set(-0.02 * S4, 0, 0.0095 * S4); usb.add(led);
  const lab = new THREE.Mesh(new THREE.PlaneGeometry(0.034 * S4, 0.013 * S4), new THREE.MeshBasicMaterial({map: ctex(512, 200, (g, w, h) => { g.fillStyle = '#15161a'; g.fillRect(0, 0, w, h); g.fillStyle = '#f2c84b'; g.font = 'bold 84px "DejaVu Sans", sans-serif'; g.textAlign = 'center'; g.fillText('Python 3.0', w / 2, 125); }), toneMapped: false}));
  lab.position.set(-0.004 * S4, 0, 0.0091 * S4); usb.add(lab); }
usb.position.set(1.0, -1.2, 0.004); usb.rotation.z = 0.35;

// ---------- app screens for "what Python can do" ----------
function drawApp(kind, k) { const {g, t: tx} = lapTex; const w = 1600, h = 1000; g.fillStyle = '#f5f6f8'; g.fillRect(0, 0, w, h);
  g.fillStyle = '#e4e6ea'; g.fillRect(0, 0, w, 56); for (const [i, c] of [[0, '#ff5f57'], [1, '#febc2e'], [2, '#28c840']]) { g.fillStyle = c; g.beginPath(); g.arc(30 + i * 30, 28, 9, 0, 7); g.fill(); }
  g.font = '26px "DejaVu Sans", sans-serif'; g.textAlign = 'left';
  if (kind === 'web') { g.fillStyle = '#fff'; g.fillRect(140, 12, 1300, 32); g.fillStyle = '#5b6170'; g.fillText('mysite.la   ·   Django', 160, 37); g.fillStyle = '#1e3a66'; g.fillRect(0, 56, w, 90); g.fillStyle = '#fff'; g.font = 'bold 36px "DejaVu Sans", sans-serif'; g.fillText('Uncle Coffee', 60, 115);
    g.font = '26px "DejaVu Sans", sans-serif'; ['Menu', 'Shop', 'About'].forEach((s, i) => g.fillText(s, 1150 + i * 140, 112)); const gr = g.createLinearGradient(0, 150, 0, 520); gr.addColorStop(0, '#d9a066'); gr.addColorStop(1, '#6b3f22'); g.fillStyle = gr; g.fillRect(60, 180, w - 120, 330);
    g.fillStyle = '#fff'; g.font = 'bold 64px "DejaVu Sans", sans-serif'; g.fillText('Fresh coffee, made with Python', 110, 340); for (let i = 0; i < 3; i++) { g.fillStyle = '#fff'; g.fillRect(60 + i * 500, 560, 460, 380); g.fillStyle = ['#c98a4b', '#3d7fd6', '#f2c84b'][i]; g.fillRect(80 + i * 500, 580, 420, 220); g.fillStyle = '#333'; g.fillText(['Latte', 'Order online', 'Rewards'][i], 90 + i * 500, 850); } }
  if (kind === 'data') { g.fillStyle = '#1f2430'; g.fillRect(0, 56, w, h); g.fillStyle = '#cfd6e4'; g.font = 'bold 34px "DejaVu Sans", sans-serif'; g.fillText('Sales dashboard  ·  pandas + matplotlib', 50, 115);
    const vals = [40, 62, 55, 78, 70, 92, 88, 105, 99, 120, 134, 150]; for (let i = 0; i < 12; i++) { const hh = vals[i] * 3.2 * k; g.fillStyle = i === 11 ? '#f2c84b' : '#3d7fd6'; g.fillRect(70 + i * 75, 900 - hh, 50, hh); }
    g.strokeStyle = '#50fa7b'; g.lineWidth = 5; g.beginPath(); for (let i = 0; i < 40; i++) { const x = 1030 + i * 13, y = 560 - Math.sin(i * 0.3) * 80 * k - i * 5 * k; i ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); g.fillStyle = '#cfd6e4'; g.font = '30px "DejaVu Sans", sans-serif'; g.fillText('+24%', 1300, 760);
    [['Users', '12,480'], ['Revenue', '$84k']].forEach(([a, b], i) => { g.fillStyle = '#2a3142'; g.fillRect(1030, 160 + i * 0, 0, 0); }); g.fillStyle = '#2a3142'; g.fillRect(1030, 160, 500, 150); g.fillStyle = '#9aa6bd'; g.fillText('Customers', 1060, 210); g.fillStyle = '#fff'; g.font = 'bold 56px "DejaVu Sans", sans-serif'; g.fillText(Math.round(12480 * k).toLocaleString('en-US'), 1060, 280); }
  if (kind === 'auto') { g.fillStyle = '#0f1218'; g.fillRect(0, 56, w, h); g.font = '30px "DejaVu Sans Mono", monospace'; const L = ['$ python organize_photos.py', 'scanning 1,240 files ...', '✓ renamed  IMG_0001.jpg → 2026-10-01_laos.jpg', '✓ resized  1,240 photos', '✓ backup → /Drive/Photos', '✓ report sent to email', 'done in 3.2 s'];
    const n = Math.floor(k * (L.length + 0.99)); L.slice(0, n).forEach((s, i) => { g.fillStyle = i === 0 ? '#8be9fd' : s.startsWith('✓') ? '#50fa7b' : '#e6e6e6'; g.fillText(s, 50, 140 + i * 56); });
    g.fillStyle = '#2a3142'; g.fillRect(50, 600, 1200, 28); g.fillStyle = '#50fa7b'; g.fillRect(50, 600, 1200 * Math.min(1, k * 1.1), 28); }
  if (kind === 'sci') { g.fillStyle = '#0b1020'; g.fillRect(0, 56, w, h); g.fillStyle = '#cfd6e4'; g.font = 'bold 34px "DejaVu Sans", sans-serif'; g.fillText('Orbit simulation  ·  NumPy', 50, 115);
    const cx = 800, cy = 560; g.fillStyle = '#f2c84b'; g.beginPath(); g.arc(cx, cy, 34, 0, 7); g.fill(); [[180, '#3d7fd6'], [280, '#50fa7b'], [380, '#ff79c6']].forEach(([r, c], j) => { g.strokeStyle = c; g.globalAlpha = 0.5; g.lineWidth = 2; g.beginPath(); g.ellipse(cx, cy, r, r * 0.62, 0, 0, 7); g.stroke(); g.globalAlpha = 1;
      const a = k * Math.PI * 2 * (1.6 - j * 0.4) + j; g.fillStyle = c; g.beginPath(); g.arc(cx + r * Math.cos(a), cy + r * 0.62 * Math.sin(a), 14, 0, 7); g.fill(); });
    const r = rnd(3); for (let i = 0; i < 160; i++) { g.fillStyle = 'rgba(255,255,255,0.5)'; g.fillRect(r() * w, 60 + r() * (h - 60), 2, 2); } }
  tx.needsUpdate = true; }
