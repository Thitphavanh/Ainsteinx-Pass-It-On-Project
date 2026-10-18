// ---------- black MacBook-style laptop (Space Black, no logo) + desk + realistic python ----------
const hero = new THREE.Group(); scene.add(hero);
const lapTex = dynTex(1600, 1000);
const SB = new THREE.MeshPhysicalMaterial({color: 0x2c2e32, metalness: 0.88, roughness: 0.34, clearcoat: 0.25, clearcoatRoughness: 0.4, envMapIntensity: 1.0});
const keyMat = new THREE.MeshStandardMaterial({color: 0x0c0c0e, roughness: 0.62, metalness: 0.05});
const glassBlack = new THREE.MeshPhysicalMaterial({color: 0x050506, roughness: 0.06, metalness: 0.0, clearcoat: 1, clearcoatRoughness: 0.03});
const grilleTex = ctex(256, 1024, (g, w, h) => { g.fillStyle = '#2c2e32'; g.fillRect(0, 0, w, h); g.fillStyle = '#060607'; for (let y = 8; y < h; y += 14) for (let x = 8 + ((y / 14) % 2) * 7; x < w; x += 14) { g.beginPath(); g.arc(x, y, 3.2, 0, 7); g.fill(); } });
function makeMacbook(scr) {
  const S = 4.22; const g = new THREE.Group(); const W0 = 0.3557 * S, D0 = 0.2481 * S, T0 = 0.0095 * S;
  const base = new THREE.Mesh(new RoundedBoxGeometry(W0, D0, T0, 6, 0.02), SB); base.position.z = T0 / 2 + 0.006; base.castShadow = base.receiveShadow = true; g.add(base);
  const well = new THREE.Mesh(new RoundedBoxGeometry(W0 * 0.78, D0 * 0.43, 0.006, 3, 0.004), new THREE.MeshStandardMaterial({color: 0x1b1c1f, roughness: 0.7})); well.position.set(0, D0 * 0.17, T0 + 0.004); g.add(well);
  const kw = 0.0165 * S, gap = 0.0026 * S; const rows = [[14, 0.62], [14, 1], [14, 1], [13, 1], [12, 1], [10, 1]]; let n = 0; rows.forEach(r => n += r[0]);
  const keys = new THREE.InstancedMesh(new RoundedBoxGeometry(kw, kw, 0.012, 3, 0.006), keyMat, n + 1); const m = new THREE.Matrix4(); let k = 0;
  rows.forEach(([cnt, hScale], ri) => { const rowW = W0 * 0.74; const w = (rowW - gap * (cnt - 1)) / cnt; const y = D0 * 0.355 - ri * (kw + gap) - (ri ? (kw * (1 - 0.62)) / 2 : 0);
    for (let i = 0; i < cnt; i++) { const x = -rowW / 2 + w / 2 + i * (w + gap); let sx = w / kw; if (ri === 5 && i === 4) sx = (w * 3 + gap * 2) / kw; if (ri === 5 && (i === 5 || i === 6)) continue;
      m.compose(new THREE.Vector3(ri === 5 && i === 4 ? x + w + gap : x, y, T0 + 0.012), new THREE.Quaternion(), new THREE.Vector3(sx, hScale, 1)); keys.setMatrixAt(k++, m); } });
  keys.count = k; keys.castShadow = true; g.add(keys);
  const pad = new THREE.Mesh(new RoundedBoxGeometry(0.16 * S, 0.1 * S, 0.003, 4, 0.0015), new THREE.MeshPhysicalMaterial({color: 0x34363b, metalness: 0.6, roughness: 0.22, clearcoat: 0.6})); pad.position.set(0, -D0 * 0.28, T0 + 0.006); g.add(pad);
  for (const s of [-1, 1]) { const gr = new THREE.Mesh(new THREE.PlaneGeometry(0.018 * S, D0 * 0.42), new THREE.MeshStandardMaterial({map: grilleTex, metalness: 0.8, roughness: 0.4})); gr.position.set(s * W0 * 0.445, D0 * 0.17, T0 + 0.0065); g.add(gr); }
  for (const [x, y] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) { const f = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.006, 16), keyMat); f.rotation.x = Math.PI / 2; f.position.set(x * W0 * 0.42, y * D0 * 0.4, 0.003); g.add(f); }
  for (const [y, w] of [[-0.12, 0.05], [0.0, 0.03], [0.07, 0.03]]) { const p = new THREE.Mesh(new RoundedBoxGeometry(0.004, w, 0.012, 2, 0.002), keyMat); p.position.set(-W0 / 2 - 0.001, y, T0 / 2 + 0.006); g.add(p); }
  const hinge = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.016, W0 * 0.86, 24), new THREE.MeshStandardMaterial({color: 0x141518, metalness: 0.6, roughness: 0.4})); hinge.rotation.z = Math.PI / 2; hinge.position.set(0, D0 / 2 - 0.012, T0 + 0.01); g.add(hinge);
  const lid = new THREE.Group(); lid.position.set(0, D0 / 2 - 0.012, T0 + 0.012); lid.rotation.x = -0.24; g.add(lid);
  const LT = 0.0068 * S; const shell = new THREE.Mesh(new RoundedBoxGeometry(W0, LT, D0 - 0.01, 6, 0.016), SB); shell.position.set(0, LT / 2, (D0 - 0.01) / 2); shell.castShadow = true; lid.add(shell);
  const bez = new THREE.Mesh(new RoundedBoxGeometry(W0 - 0.012, 0.004, D0 - 0.022, 4, 0.014), glassBlack); bez.position.set(0, -0.001, (D0 - 0.01) / 2); lid.add(bez);
  const sw = W0 - 0.006 * S * 2, sh = D0 - 0.01 - 0.0075 * S * 2 - 0.004; const sc = new THREE.Mesh(new THREE.PlaneGeometry(sw, sh), new THREE.MeshBasicMaterial({map: scr, toneMapped: false})); sc.rotation.x = Math.PI / 2; sc.position.set(0, -0.0035, (D0 - 0.01) / 2 - 0.006); lid.add(sc);
  const notch = new THREE.Mesh(new RoundedBoxGeometry(0.035 * S, 0.002, 0.026, 3, 0.008), glassBlack); notch.position.set(0, -0.0042, D0 - 0.026); lid.add(notch);
  const sgl = glow(0x6b90ff, 1.8, 0.16); sgl.position.set(0, -0.25, (D0 - 0.01) / 2); lid.add(sgl);
  g.userData = {lid, screen: sc, base}; return g; }
const mac = makeMacbook(lapTex.t); hero.add(mac);
// desk + room
const walnut = ctex(2048, 1024, (g, w, h) => { const r = rnd(41); const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, '#4a2f1f'); gr.addColorStop(1, '#5c3a25'); g.fillStyle = gr; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 420; i++) { const y0 = r() * h; g.strokeStyle = `rgba(${25 + r() * 30},${12 + r() * 14},${6 + r() * 8},${0.12 + r() * 0.25})`; g.lineWidth = 0.6 + r() * 2.4; g.beginPath(); g.moveTo(0, y0); for (let x = 0; x <= w; x += 24) g.lineTo(x, y0 + Math.sin(x * 0.004 + i) * 9 + Math.sin(x * 0.02 + i * 3) * 2); g.stroke(); }
  for (let i = 0; i < 9; i++) { g.strokeStyle = 'rgba(20,10,4,0.35)'; g.lineWidth = 1.5; const cx = r() * w, cy = r() * h; for (let k = 1; k < 7; k++) { g.beginPath(); g.ellipse(cx, cy, k * 22, k * 6, 0, 0, 7); g.stroke(); } } }, [1.4, 1]);
const desk = new THREE.Mesh(new RoundedBoxGeometry(6, 3.4, 0.12, 3, 0.02), new THREE.MeshPhysicalMaterial({map: walnut, roughness: 0.38, clearcoat: 0.55, clearcoatRoughness: 0.35})); desk.position.set(0, 0.4, -0.06); desk.receiveShadow = true; hero.add(desk);
const backWall = new THREE.Mesh(new THREE.PlaneGeometry(40, 16), new THREE.MeshStandardMaterial({color: 0x15171c, roughness: 0.95})); backWall.rotation.x = Math.PI / 2; backWall.position.set(0, 4.5, 2); hero.add(backWall);
const cityB = new THREE.Group(); hero.add(cityB); { const r = rnd(77); for (let i = 0; i < 140; i++) { const c = [0xffc070, 0xffe0b0, 0x9fc0ff, 0xff9a60][Math.floor(r() * 4)]; const s = glow(c, 0.18 + r() * 0.35, 0.35 + r() * 0.5); s.position.set((r() - 0.5) * 14, 4.3, 0.8 + r() * 4.5); cityB.add(s); } }
const mug = new THREE.Group(); hero.add(mug); { const cer = new THREE.MeshPhysicalMaterial({color: 0xe9e4da, roughness: 0.18, clearcoat: 0.8}); const c = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.15, 0.36, 48, 1, true), cer); c.rotation.x = Math.PI / 2; c.position.z = 0.18; c.castShadow = true; mug.add(c);
  const bot = new THREE.Mesh(new THREE.CircleGeometry(0.15, 32), cer); bot.position.z = 0.005; mug.add(bot); const cof = new THREE.Mesh(new THREE.CircleGeometry(0.16, 32), new THREE.MeshPhysicalMaterial({color: 0x2a160b, roughness: 0.1, clearcoat: 1})); cof.position.z = 0.31; mug.add(cof);
  const hd = new THREE.Mesh(new THREE.TorusGeometry(0.08, 0.022, 16, 32, Math.PI), cer); hd.rotation.set(Math.PI / 2, Math.PI / 2, 0); hd.position.set(0.17, 0, 0.18); hd.rotation.y = -Math.PI / 2; mug.add(hd); }
mug.position.set(1.35, -0.25, 0);
const plant = new THREE.Group(); hero.add(plant); { const pot = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.16, 0.34, 40), new THREE.MeshStandardMaterial({color: 0x2b2b2e, roughness: 0.75})); pot.rotation.x = Math.PI / 2; pot.position.z = 0.17; pot.castShadow = true; plant.add(pot);
  const lm = new THREE.MeshPhysicalMaterial({color: 0x2f6b34, roughness: 0.45, clearcoat: 0.3, side: THREE.DoubleSide}); const r = rnd(5);
  for (let i = 0; i < 26; i++) { const lf = new THREE.Mesh(new THREE.SphereGeometry(0.1, 16, 8), lm); lf.scale.set(0.35, 1, 0.05); const a = r() * 6.28, e = 0.4 + r() * 0.9; lf.position.set(Math.cos(a) * 0.12, Math.sin(a) * 0.12, 0.4 + r() * 0.3); lf.rotation.set(e, 0, a); lf.castShadow = true; plant.add(lf); } }
plant.position.set(-1.7, 1.0, 0);
const book = new THREE.Mesh(new RoundedBoxGeometry(0.7, 0.95, 0.06, 2, 0.01), new THREE.MeshStandardMaterial({color: 0x1d3b5a, roughness: 0.7})); book.position.set(-1.45, -0.35, 0.03); book.rotation.z = 0.2; book.castShadow = true; hero.add(book);
// realistic python (tapered body, scale texture in Python blue / yellow)
const skin = ctex(1024, 256, (g, w, h) => { const r = rnd(19); g.fillStyle = '#c99a2e'; g.fillRect(0, 0, w, h); for (let i = 0; i < 60; i++) { const x = r() * w, y = h * 0.5 + (r() - 0.5) * h * 0.6; g.fillStyle = r() < 0.6 ? '#21407a' : '#2d5aa8'; g.beginPath(); g.ellipse(x, y, 26 + r() * 30, 22 + r() * 20, r(), 0, 7); g.fill(); g.fillStyle = '#e0b84a'; g.beginPath(); g.ellipse(x, y, 8 + r() * 6, 6 + r() * 5, 0, 0, 7); g.fill(); }
  const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, 'rgba(255,235,180,0.55)'); gr.addColorStop(0.18, 'rgba(0,0,0,0)'); gr.addColorStop(0.82, 'rgba(0,0,0,0)'); gr.addColorStop(1, 'rgba(255,235,180,0.55)'); g.fillStyle = gr; g.fillRect(0, 0, w, h);
  for (let y = 0; y < h; y += 9) for (let x = (y / 9) % 2 * 5; x < w; x += 10) { g.strokeStyle = 'rgba(20,14,6,0.28)'; g.lineWidth = 1; g.beginPath(); g.moveTo(x, y + 4.5); g.lineTo(x + 5, y); g.lineTo(x + 10, y + 4.5); g.lineTo(x + 5, y + 9); g.closePath(); g.stroke(); } }, [6, 1]);
const scaleBump = ctex(256, 128, (g, w, h) => { g.fillStyle = '#808080'; g.fillRect(0, 0, w, h); for (let y = 0; y < h; y += 9) for (let x = (y / 9) % 2 * 5; x < w; x += 10) { const gr = g.createRadialGradient(x + 5, y + 4.5, 0, x + 5, y + 4.5, 6); gr.addColorStop(0, '#d0d0d0'); gr.addColorStop(1, '#505050'); g.fillStyle = gr; g.fillRect(x, y, 10, 9); } }, [24, 4]);
scaleBump.colorSpace = THREE.NoColorSpace;
const snakeMat = new THREE.MeshPhysicalMaterial({map: skin, bumpMap: scaleBump, bumpScale: 1.4, roughness: 0.42, clearcoat: 0.55, clearcoatRoughness: 0.35, sheen: 0.4, sheenColor: new THREE.Color(0xfff0c0)});
let snake = null; const snakeHead = new THREE.Group(); hero.add(snakeHead);
{ const hm = new THREE.MeshPhysicalMaterial({map: skin, bumpMap: scaleBump, bumpScale: 1.0, roughness: 0.4, clearcoat: 0.6}); const hg = new THREE.SphereGeometry(0.1, 48, 32); const p = hg.attributes.position;
  for (let i = 0; i < p.count; i++) { let x = p.getX(i), y = p.getY(i), z = p.getZ(i); const t = (x + 0.1) / 0.2; x *= 1.85; y *= lerp(1.0, 0.62, t); z *= lerp(0.72, 0.42, t); if (z < 0) z *= 0.75; p.setXYZ(i, x, y, z); } hg.computeVertexNormals();
  const head = new THREE.Mesh(hg, hm); head.castShadow = true; snakeHead.add(head);
  for (const s of [-1, 1]) { const e = new THREE.Mesh(new THREE.SphereGeometry(0.02, 24, 16), new THREE.MeshPhysicalMaterial({color: 0x1a0d04, roughness: 0.05, clearcoat: 1})); e.position.set(0.07, s * 0.052, 0.025); snakeHead.add(e);
    const n = new THREE.Mesh(new THREE.SphereGeometry(0.006, 8, 6), keyMat); n.position.set(0.178, s * 0.022, 0.012); snakeHead.add(n); } }
function snakePts(t) { const pts = [], R = []; const N = 200;
  for (let i = 0; i <= N; i++) { const s = i / N; let p; if (s < 0.72) { const a = s / 0.72 * Math.PI * 2 * 2.1 + 0.4; const rr = lerp(0.62, 0.3, s / 0.72); p = new THREE.Vector3(1.55 + rr * Math.cos(a), 0.55 + rr * Math.sin(a) * 0.85, 0.07 + 0.11 * Math.max(0, Math.sin(a * 0.5)) * (s > 0.5 ? 1 : 0.3)); }
    else { const k = (s - 0.72) / 0.28; const sway = 0.06 * Math.sin(t * 1.3 + k * 3); p = new THREE.Vector3(1.55 + lerp(0.3, -0.25, k) + sway, 0.55 + lerp(0, -0.45, k), lerp(0.08, 0.62, ease(k)) + 0.02 * Math.sin(t * 2)); }
    pts.push(p); R.push(0.075 * Math.min(1, s * 9 + 0.15) * (s > 0.92 ? lerp(1, 0.75, (s - 0.92) / 0.08) : 1)); } return [pts, R]; }
function taperTube(pts, R, seg = 260, rad = 18) { const c = new THREE.CatmullRomCurve3(pts); const fr = c.computeFrenetFrames(seg, false); const pos = [], uv = [], idx = [];
  for (let i = 0; i <= seg; i++) { const s = i / seg, P = c.getPointAt(s); const r = R[Math.min(R.length - 1, Math.round(s * (R.length - 1)))]; for (let j = 0; j <= rad; j++) { const v = j / rad * Math.PI * 2; const N = fr.normals[i].clone().multiplyScalar(-Math.cos(v)).add(fr.binormals[i].clone().multiplyScalar(Math.sin(v)));
    const q = P.clone().add(N.multiplyScalar(r)); pos.push(q.x, q.y, Math.max(q.z, 0.004)); uv.push(s * 9, j / rad); } }
  for (let i = 0; i < seg; i++) for (let j = 0; j < rad; j++) { const a = i * (rad + 1) + j, b = a + rad + 1; idx.push(a, b, a + 1, b, b + 1, a + 1); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setIndex(idx); g.computeVertexNormals(); return [g, c]; }
function updSnake(t) { const [pts, R] = snakePts(t); const [g, c] = taperTube(pts, R); if (snake) { snake.geometry.dispose(); hero.remove(snake); } snake = new THREE.Mesh(g, snakeMat); snake.castShadow = snake.receiveShadow = true; hero.add(snake);
  const p = c.getPointAt(1), d = c.getTangentAt(1); snakeHead.position.copy(p).add(d.clone().multiplyScalar(0.11)); const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(1, 0, 0), new THREE.Vector3(d.x, d.y, d.z * 0.35).normalize()); snakeHead.quaternion.copy(q); }
const heroGlows = new THREE.Group(); hero.add(heroGlows);
const deskLamp = new THREE.SpotLight(0xffd6a0, 40, 12, 0.7, 0.6, 2); deskLamp.position.set(-1.6, -1.2, 3.2); deskLamp.target.position.set(0.3, 0.3, 0); deskLamp.castShadow = true; deskLamp.shadow.mapSize.set(2048, 2048); deskLamp.shadow.bias = -0.0002; deskLamp.shadow.radius = 6; hero.add(deskLamp); hero.add(deskLamp.target);
const screenLight = new THREE.RectAreaLight(0x8fb0ff, 6, 1.4, 0.9); hero.add(screenLight);
