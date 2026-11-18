/**
 * WanderInsight — Full-Viewport Interactive Three.js Background + Standalone 3D Holographic Globe
 * 1) #wi-bg-canvas: Full-window interactive 3D topographic terrain mesh + heritage constellation
 *    that ripples around the mouse cursor and emits shockwaves on click.
 * 2) #wi-three-canvas: Standalone free-floating 3D Holographic Globe (not clipped inside a box)
 *    with GLSL Fresnel + scanline shader, Fibonacci lattice, geodesic telemetry arcs, pulsing
 *    Cebu landmark beacons, and interactive click-and-drag 360° orbit rotation.
 */
(function () {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ==========================================================================
   * 1. FULL-VIEWPORT INTERACTIVE 3D BACKGROUND (#wi-bg-canvas)
   * ========================================================================== */
  function initInteractiveBackground() {
    const host = document.getElementById("wi-bg-canvas");
    if (!host || typeof THREE === "undefined") return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(52, window.innerWidth / window.innerHeight, 0.1, 120);
    camera.position.set(0, 5.2, 13.5);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    host.innerHTML = "";
    host.appendChild(renderer.domElement);

    const world = new THREE.Group();
    scene.add(world);

    const cols = 46;
    const rows = 28;
    const planeGeo = new THREE.PlaneGeometry(34, 20, cols, rows);
    planeGeo.rotateX(-Math.PI / 2.25);

    const posAttr = planeGeo.attributes.position;
    for (let i = 0; i < posAttr.count; i++) {
      const x = posAttr.getX(i);
      const z = posAttr.getZ(i);
      posAttr.setY(i, Math.sin(x * 0.35) * Math.cos(z * 0.35) * 0.45);
    }

    const terrainMat = new THREE.MeshBasicMaterial({
      color: 0xc8922e,
      wireframe: true,
      transparent: true,
      opacity: 0.16,
    });
    const terrain = new THREE.Mesh(planeGeo, terrainMat);
    terrain.position.y = -3.2;
    world.add(terrain);

    const nodeCount = 42;
    const nodes = [];
    const nodeGeo = new THREE.SphereGeometry(0.075, 10, 10);
    const nodeMatGold = new THREE.MeshBasicMaterial({ color: 0xc8922e, transparent: true, opacity: 0.65 });
    const nodeMatTerra = new THREE.MeshBasicMaterial({ color: 0x8c3b1a, transparent: true, opacity: 0.55 });

    for (let i = 0; i < nodeCount; i++) {
      const mesh = new THREE.Mesh(nodeGeo, i % 3 === 0 ? nodeMatTerra : nodeMatGold);
      mesh.position.set(
        (Math.random() - 0.5) * 24,
        (Math.random() - 0.2) * 10,
        (Math.random() - 0.5) * 10
      );
      mesh.userData = {
        vx: (Math.random() - 0.5) * 0.012,
        vy: (Math.random() - 0.5) * 0.01,
        vz: (Math.random() - 0.5) * 0.008,
      };
      world.add(mesh);
      nodes.push(mesh);
    }

    const maxSegments = nodeCount * 6;
    const linePositions = new Float32Array(maxSegments * 6);
    const lineGeo = new THREE.BufferGeometry();
    lineGeo.setAttribute("position", new THREE.BufferAttribute(linePositions, 3));
    const lineMat = new THREE.LineBasicMaterial({
      color: 0xc8922e,
      transparent: true,
      opacity: 0.14,
    });
    const constellationLines = new THREE.LineSegments(lineGeo, lineMat);
    world.add(constellationLines);

    const mouse = { x: 0, y: 0, worldX: 0, worldZ: 0 };
    const ripples = [];

    window.addEventListener("pointermove", function (e) {
      mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
      mouse.worldX = mouse.x * 13;
      mouse.worldZ = -mouse.y * 7;

      document.documentElement.style.setProperty("--cursor-x", e.clientX + "px");
      document.documentElement.style.setProperty("--cursor-y", e.clientY + "px");

      const pill = document.getElementById("wi-coords-live");
      if (pill) {
        const lat = (10.28 + ((1 - e.clientY / window.innerHeight) - 0.5) * 0.45).toFixed(4);
        const lng = (123.90 + ((e.clientX / window.innerWidth) - 0.5) * 0.45).toFixed(4);
        pill.textContent = lat + "°N, " + lng + "°E";
      }
    });

    window.addEventListener("pointerdown", function (e) {
      const rx = ((e.clientX / window.innerWidth) * 2 - 1) * 13;
      const rz = -(-(e.clientY / window.innerHeight) * 2 + 1) * 7;
      ripples.push({ x: rx, z: rz, age: 0 });
      if (ripples.length > 4) ripples.shift();
    });

    let paused = false;
    const toggleBtn = document.getElementById("wi-bg-toggle");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", function () {
        paused = !paused;
        const lbl = document.getElementById("wi-bg-toggle-label");
        if (lbl) lbl.textContent = paused ? "Resume 3D" : "Pause 3D";
      });
    }

    renderer.render(scene, camera);
    if (reduceMotion) return;

    let clock = 0;
    function animateBg() {
      requestAnimationFrame(animateBg);
      if (paused) return;
      clock += 0.018;

      for (let i = 0; i < posAttr.count; i++) {
        const vx = posAttr.getX(i);
        const vz = posAttr.getZ(i);
        let wave =
          Math.sin(vx * 0.35 + clock) * 0.35 +
          Math.cos(vz * 0.4 + clock * 0.8) * 0.3;

        const dx = vx - mouse.worldX;
        const dz = vz - mouse.worldZ;
        const dist = Math.sqrt(dx * dx + dz * dz);
        if (dist < 5.5) {
          wave += Math.cos((dist / 5.5) * (Math.PI / 2)) * 1.05;
        }

        for (let r = 0; r < ripples.length; r++) {
          const rp = ripples[r];
          const rdx = vx - rp.x;
          const rdz = vz - rp.z;
          const rDist = Math.sqrt(rdx * rdx + rdz * rdz);
          const ringRadius = rp.age * 9.0;
          const band = Math.abs(rDist - ringRadius);
          if (band < 1.6) {
            wave += Math.sin((1 - band / 1.6) * Math.PI) * (1 - rp.age) * 1.45;
          }
        }
        posAttr.setY(i, wave);
      }
      posAttr.needsUpdate = true;

      for (let r = ripples.length - 1; r >= 0; r--) {
        ripples[r].age += 0.016;
        if (ripples[r].age >= 1) ripples.splice(r, 1);
      }

      let segIdx = 0;
      for (let i = 0; i < nodeCount; i++) {
        const n = nodes[i];
        n.position.x += n.userData.vx;
        n.position.y += n.userData.vy;
        n.position.z += n.userData.vz;

        if (Math.abs(n.position.x) > 13) n.userData.vx *= -1;
        if (n.position.y > 6 || n.position.y < -2.5) n.userData.vy *= -1;
        if (Math.abs(n.position.z) > 6) n.userData.vz *= -1;

        for (let j = i + 1; j < nodeCount; j++) {
          if (segIdx >= maxSegments) break;
          const m = nodes[j];
          const d = n.position.distanceTo(m.position);
          if (d < 4.2) {
            const base = segIdx * 6;
            linePositions[base] = n.position.x;
            linePositions[base + 1] = n.position.y;
            linePositions[base + 2] = n.position.z;
            linePositions[base + 3] = m.position.x;
            linePositions[base + 4] = m.position.y;
            linePositions[base + 5] = m.position.z;
            segIdx++;
          }
        }
      }
      lineGeo.setDrawRange(0, segIdx * 2);
      lineGeo.attributes.position.needsUpdate = true;

      world.rotation.y += (mouse.x * 0.14 - world.rotation.y) * 0.04;
      world.rotation.x += (-mouse.y * 0.06 - world.rotation.x) * 0.04;

      renderer.render(scene, camera);
    }
    animateBg();

    window.addEventListener("resize", function () {
      camera.aspect = window.innerWidth / window.innerHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    });
  }

  /* ==========================================================================
   * 2. STANDALONE 3D HOLOGRAPHIC GLOBE (#wi-three-canvas)
   *    Free-floating in open 3D space (not trapped inside a dark rectangle).
   *    Includes GLSL Fresnel + scanline shader, Fibonacci lattice points,
   *    curved geodesic data arcs, pulsing Cebu beacon radar rings, and
   *    click-and-drag 360° interactive rotation.
   * ========================================================================== */
  function initHeroGlobe() {
    const container = document.getElementById("wi-three-canvas");
    if (!container || typeof THREE === "undefined") return;

    const width = container.clientWidth || 460;
    const height = container.clientHeight || 420;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100);
    // Pulled back so all orbital rings and spikes float freely without clipping the canvas edges
    camera.position.set(0, 0.15, 5.15);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    const root = new THREE.Group();
    scene.add(root);

    // 1. Custom GLSL Hologram Shader Sphere (Translucent Deep Teal + Brass Rim + Laser Scanline)
    const holoUniforms = {
      uTime: { value: 0 },
      uColorCore: { value: new THREE.Color(0x0d3b42) }, // Deep Holographic Teal
      uColorRim: { value: new THREE.Color(0xc8922e) },  // Antique Brass Gold
      uColorBeam: { value: new THREE.Color(0x38bdf8) }, // Cyan Laser Sweep
    };

    const holoVert = [
      "varying vec3 vNormal;",
      "varying vec3 vViewPos;",
      "varying vec3 vLocalPos;",
      "void main() {",
      "  vLocalPos = position;",
      "  vNormal = normalize(normalMatrix * normal);",
      "  vec4 mvPos = modelViewMatrix * vec4(position, 1.0);",
      "  vViewPos = -mvPos.xyz;",
      "  gl_Position = projectionMatrix * mvPos;",
      "}"
    ].join("\n");

    const holoFrag = [
      "uniform float uTime;",
      "uniform vec3 uColorCore;",
      "uniform vec3 uColorRim;",
      "uniform vec3 uColorBeam;",
      "varying vec3 vNormal;",
      "varying vec3 vViewPos;",
      "varying vec3 vLocalPos;",
      "void main() {",
      "  vec3 N = normalize(vNormal);",
      "  vec3 V = normalize(vViewPos);",
      "  float fresnel = pow(1.0 - abs(dot(N, V)), 1.85);",
      "  float scanFine = 0.5 + 0.5 * sin(vLocalPos.y * 46.0 - uTime * 4.0);",
      "  float laserSweep = smoothstep(0.90, 1.0, sin(vLocalPos.y * 2.1 - uTime * 1.5));",
      "  vec3 col = mix(uColorCore, uColorRim, fresnel * 0.85);",
      "  col = mix(col, uColorBeam, laserSweep * 0.65);",
      "  float alpha = 0.22 + fresnel * 0.58 + scanFine * 0.08 + laserSweep * 0.28;",
      "  gl_FragColor = vec4(col, clamp(alpha, 0.15, 0.92));",
      "}"
    ].join("\n");

    const holoSphereGeo = new THREE.SphereGeometry(1.32, 48, 36);
    const holoSphereMat = new THREE.ShaderMaterial({
      uniforms: holoUniforms,
      vertexShader: holoVert,
      fragmentShader: holoFrag,
      transparent: true,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    root.add(new THREE.Mesh(holoSphereGeo, holoSphereMat));

    // 2. Holographic Geodesic Wireframe Shell
    const wireGeo = new THREE.IcosahedronGeometry(1.34, 3);
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x8c3b1a,
      wireframe: true,
      transparent: true,
      opacity: 0.24,
    });
    const globe = new THREE.Mesh(wireGeo, wireMat);
    root.add(globe);

    // 3. Fibonacci 3D Surface Point-Cloud Lattice (600 holographic nodes)
    const dotCount = 600;
    const dotPos = new Float32Array(dotCount * 3);
    const dotColors = new Float32Array(dotCount * 3);
    const goldenRatio = (1 + Math.sqrt(5)) / 2;
    const cTeal = new THREE.Color(0x0ea5e9);
    const cTerra = new THREE.Color(0x8c3b1a);
    const cGold = new THREE.Color(0xd97706);

    for (let i = 0; i < dotCount; i++) {
      const theta = (2 * Math.PI * i) / goldenRatio;
      const phi = Math.acos(1 - (2 * (i + 0.5)) / dotCount);
      const r = 1.355;
      dotPos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      dotPos[i * 3 + 1] = r * Math.cos(phi);
      dotPos[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta);

      const mixCol = i % 3 === 0 ? cGold : (i % 2 === 0 ? cTeal : cTerra);
      dotColors[i * 3] = mixCol.r;
      dotColors[i * 3 + 1] = mixCol.g;
      dotColors[i * 3 + 2] = mixCol.b;
    }
    const cloudGeo = new THREE.BufferGeometry();
    cloudGeo.setAttribute("position", new THREE.BufferAttribute(dotPos, 3));
    cloudGeo.setAttribute("color", new THREE.BufferAttribute(dotColors, 3));
    const cloudMat = new THREE.PointsMaterial({
      size: 0.035,
      vertexColors: true,
      transparent: true,
      opacity: 0.88,
    });
    const pointCloud = new THREE.Points(cloudGeo, cloudMat);
    root.add(pointCloud);

    // 4. Sweeping Internal Horizontal Laser Scan Disc
    const scanRingGeo = new THREE.RingGeometry(0.1, 1.31, 48);
    scanRingGeo.rotateX(Math.PI / 2);
    const scanRingMat = new THREE.MeshBasicMaterial({
      color: 0x0ea5e9,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.22,
      depthWrite: false,
    });
    const scanDisc = new THREE.Mesh(scanRingGeo, scanRingMat);
    root.add(scanDisc);

    // 5. Triple Counter-Rotating Orbital Astrolabe Rings (Floating freely outside the sphere)
    const ringMatGold = new THREE.MeshBasicMaterial({
      color: 0xc8922e,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.65,
    });
    const ringMatTeal = new THREE.MeshBasicMaterial({
      color: 0x1d5c63,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.55,
    });
    const ringMatTerra = new THREE.MeshBasicMaterial({
      color: 0x8c3b1a,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.5,
    });

    const ring1 = new THREE.Mesh(new THREE.RingGeometry(1.56, 1.59, 72), ringMatGold);
    ring1.rotation.x = Math.PI / 2.35;
    ring1.rotation.y = 0.32;
    root.add(ring1);

    const ring2 = new THREE.Mesh(new THREE.RingGeometry(1.74, 1.765, 72), ringMatTeal);
    ring2.rotation.x = -Math.PI / 3.0;
    ring2.rotation.z = 0.45;
    root.add(ring2);

    const ring3 = new THREE.Mesh(
      new THREE.RingGeometry(1.88, 1.915, 48, 1, 0, Math.PI * 1.4),
      ringMatTerra
    );
    ring3.rotation.x = Math.PI / 2.1;
    root.add(ring3);

    // 6. Cebu Landmark Beacons + Pulsing Surface Radar Rings + 3D Telemetry Spikes & Arcs
    const beaconPositions = [
      [0.85, 0.62, 0.88],   // Basilica Minore del Sto. Nino
      [0.72, 0.48, 1.05],   // Magellan's Cross
      [0.95, 0.35, 0.90],   // Fort San Pedro
      [-0.65, 0.78, 0.91],  // Yap-Sandiego Ancestral House
      [0.42, -0.55, 1.18],  // Museo Sugbo
      [-0.82, -0.42, 0.98], // Casa Gorordo Museum
      [0.15, 0.98, 0.92],   // Taoist Temple
      [-0.38, 0.52, 1.19],  // Heritage of Cebu Monument
    ];

    const beaconGroup = new THREE.Group();
    root.add(beaconGroup);

    const dotGeo = new THREE.SphereGeometry(0.042, 12, 12);
    const dotMat = new THREE.MeshBasicMaterial({ color: 0xd97706 });
    const haloGeo = new THREE.RingGeometry(0.055, 0.082, 24);
    const haloMat = new THREE.MeshBasicMaterial({
      color: 0x0ea5e9,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.85,
    });

    const beaconVecs = [];
    const pulseHalos = [];

    beaconPositions.forEach(function (pos, idx) {
      const surfaceVec = new THREE.Vector3(pos[0], pos[1], pos[2]).normalize().multiplyScalar(1.35);
      beaconVecs.push(surfaceVec);

      const dot = new THREE.Mesh(dotGeo, dotMat);
      dot.position.copy(surfaceVec);
      beaconGroup.add(dot);

      const halo = new THREE.Mesh(haloGeo, haloMat.clone());
      halo.position.copy(surfaceVec.clone().multiplyScalar(1.01));
      halo.lookAt(surfaceVec.clone().multiplyScalar(2));
      halo.userData = { phase: idx * 0.8 };
      beaconGroup.add(halo);
      pulseHalos.push(halo);

      const spikeEnd = surfaceVec.clone().multiplyScalar(1.16 + (idx % 3) * 0.04);
      const spikeGeo = new THREE.BufferGeometry().setFromPoints([surfaceVec, spikeEnd]);
      const spikeMat = new THREE.LineBasicMaterial({
        color: idx % 2 === 0 ? 0x0ea5e9 : 0x8c3b1a,
        transparent: true,
        opacity: 0.75,
      });
      beaconGroup.add(new THREE.Line(spikeGeo, spikeMat));
    });

    const arcPairs = [
      [0, 1], [1, 2], [0, 7], [7, 3], [2, 4], [4, 5], [3, 6], [6, 0],
    ];
    arcPairs.forEach(function (pair, idx) {
      const vStart = beaconVecs[pair[0]];
      const vEnd = beaconVecs[pair[1]];
      const vMid = vStart.clone().add(vEnd).multiplyScalar(0.5).normalize().multiplyScalar(1.68);
      const curve = new THREE.QuadraticBezierCurve3(vStart, vMid, vEnd);
      const arcGeo = new THREE.BufferGeometry().setFromPoints(curve.getPoints(28));
      const arcMat = new THREE.LineBasicMaterial({
        color: idx % 2 === 0 ? 0x0ea5e9 : 0xc8922e,
        transparent: true,
        opacity: 0.65,
      });
      beaconGroup.add(new THREE.Line(arcGeo, arcMat));
    });

    // Interactive Click-and-Drag 360° Spin + Pointer Parallax
    let isDragging = false;
    let prevX = 0;
    let prevY = 0;
    let dragRotY = 0;
    let dragRotX = 0;
    let targetRotX = 0.14;
    let targetRotY = 0;

    container.addEventListener("pointerdown", function (e) {
      isDragging = true;
      prevX = e.clientX;
      prevY = e.clientY;
    });
    window.addEventListener("pointerup", function () {
      isDragging = false;
    });
    window.addEventListener("pointermove", function (e) {
      if (isDragging) {
        dragRotY += (e.clientX - prevX) * 0.008;
        dragRotX += (e.clientY - prevY) * 0.006;
        prevX = e.clientX;
        prevY = e.clientY;
      }
      targetRotY = (e.clientX / window.innerWidth - 0.5) * 0.55 + dragRotY;
      targetRotX = 0.14 + (e.clientY / window.innerHeight - 0.5) * 0.35 + dragRotX;
    });

    renderer.render(scene, camera);
    if (reduceMotion) return;

    let t = 0;
    function animate() {
      requestAnimationFrame(animate);
      t += 0.02;
      holoUniforms.uTime.value = t;

      // Smooth floating levitation bob in open 3D space
      root.position.y = Math.sin(t * 0.9) * 0.07;

      // Rotate hologram layers
      globe.rotation.y += 0.0032;
      pointCloud.rotation.y += 0.0032;
      beaconGroup.rotation.y += 0.0032;

      // Counter-rotate orbital rings
      ring1.rotation.z += 0.0035;
      ring2.rotation.z -= 0.0026;
      ring3.rotation.z += 0.0045;

      // Sweep internal hologram scan disc vertically
      const sweepY = Math.sin(t * 0.85) * 1.15;
      scanDisc.position.y = sweepY;
      const rScale = Math.max(0.15, Math.sqrt(Math.max(0, 1.32 * 1.32 - sweepY * sweepY)) / 1.31);
      scanDisc.scale.set(rScale, 1, rScale);

      // Pulse beacon radar halos
      for (let i = 0; i < pulseHalos.length; i++) {
        const h = pulseHalos[i];
        const s = 1 + 0.55 * (0.5 + 0.5 * Math.sin(t * 2.4 + h.userData.phase));
        h.scale.set(s, s, 1);
        h.material.opacity = 1.15 - s * 0.55;
      }

      root.rotation.y += (targetRotY - root.rotation.y) * 0.06;
      root.rotation.x += (targetRotX - root.rotation.x) * 0.06;
      renderer.render(scene, camera);
    }
    animate();

    window.addEventListener("resize", function () {
      const w = container.clientWidth || 460;
      const h = container.clientHeight || 420;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    });
  }

  /* ==========================================================================
   * 3. 3D PERSPECTIVE CARD GLARE & TILT ON INTERACTIVE CARDS
   * ========================================================================== */
  function initInteractiveCards() {
    if (reduceMotion) return;
    const cards = document.querySelectorAll(".kpi-card, .card-interactive");
    cards.forEach(function (card) {
      card.addEventListener("pointermove", function (e) {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const rx = -((y / rect.height) - 0.5) * 6;
        const ry = ((x / rect.width) - 0.5) * 6;
        card.style.transform =
          "perspective(700px) rotateX(" + rx.toFixed(2) + "deg) rotateY(" + ry.toFixed(2) + "deg) translateY(-3px)";
        card.style.setProperty("--card-spot-x", x + "px");
        card.style.setProperty("--card-spot-y", y + "px");
      });
      card.addEventListener("pointerleave", function () {
        card.style.transform = "";
      });
    });
  }

  function boot() {
    initInteractiveBackground();
    initHeroGlobe();
    initInteractiveCards();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
