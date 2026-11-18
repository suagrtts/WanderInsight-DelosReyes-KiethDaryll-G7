/**
 * WanderInsight — Full-Viewport Interactive Three.js Background + Hero Globe
 * 1) #wi-bg-canvas: Full-window interactive 3D topographic terrain mesh + heritage constellation
 *    that ripples around the mouse cursor and emits shockwaves on click.
 * 2) #wi-three-canvas: Local hero / auth-pane 3D Cebu heritage astrolabe globe.
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

    // A) Interactive Topographic Wireframe Terrain (Cebu coastal contour waves)
    const cols = 46;
    const rows = 28;
    const planeGeo = new THREE.PlaneGeometry(34, 20, cols, rows);
    planeGeo.rotateX(-Math.PI / 2.25);

    const posAttr = planeGeo.attributes.position;
    const baseY = new Float32Array(posAttr.count);
    for (let i = 0; i < posAttr.count; i++) {
      const x = posAttr.getX(i);
      const z = posAttr.getZ(i);
      baseY[i] = Math.sin(x * 0.35) * Math.cos(z * 0.35) * 0.45;
      posAttr.setY(i, baseY[i]);
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

    // B) Floating Heritage Constellation Nodes + Dynamic Connecting Lines
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
        baseX: mesh.position.x,
        baseY: mesh.position.y,
      };
      world.add(mesh);
      nodes.push(mesh);
    }

    // Line geometry connecting nearby constellation nodes
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

    // Mouse / Pointer state & Click Ripple Shockwave
    const mouse = { x: 0, y: 0, worldX: 0, worldZ: 0 };
    const ripples = []; // { x, z, time }

    window.addEventListener("pointermove", function (e) {
      mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
      mouse.worldX = mouse.x * 13;
      mouse.worldZ = -mouse.y * 7;

      // Update CSS spotlight variables on body
      document.documentElement.style.setProperty("--cursor-x", e.clientX + "px");
      document.documentElement.style.setProperty("--cursor-y", e.clientY + "px");
    });

    window.addEventListener("pointerdown", function (e) {
      const rx = ((e.clientX / window.innerWidth) * 2 - 1) * 13;
      const rz = -(-(e.clientY / window.innerHeight) * 2 + 1) * 7;
      ripples.push({ x: rx, z: rz, age: 0 });
      if (ripples.length > 4) ripples.shift();

      const pill = document.getElementById("wi-coords-live");
      if (pill) {
        const lat = (10.28 + ((1 - e.clientY / window.innerHeight) - 0.5) * 0.45).toFixed(4);
        const lng = (123.90 + ((e.clientX / window.innerWidth) - 0.5) * 0.45).toFixed(4);
        pill.textContent = lat + "°N, " + lng + "°E · PING";
      }
    });

    // Live GPS telemetry update on pointermove
    window.addEventListener("pointermove", function (e) {
      const pill = document.getElementById("wi-coords-live");
      if (!pill) return;
      const lat = (10.28 + ((1 - e.clientY / window.innerHeight) - 0.5) * 0.45).toFixed(4);
      const lng = (123.90 + ((e.clientX / window.innerWidth) - 0.5) * 0.45).toFixed(4);
      pill.textContent = lat + "°N, " + lng + "°E";
    });

    let paused = false;
    const toggleBtn = document.getElementById("wi-bg-toggle");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", function () {
        paused = !paused;
        const lbl = document.getElementById("wi-bg-toggle-label");
        if (lbl) {
          lbl.textContent = paused ? "Resume 3D" : "Pause 3D";
        }
      });
    }

    renderer.render(scene, camera);
    if (reduceMotion) return;

    let clock = 0;
    function animateBg() {
      requestAnimationFrame(animateBg);
      if (paused) return;
      clock += 0.018;

      // 1. Animate terrain vertices + cursor magnetic ripple + click shockwaves
      for (let i = 0; i < posAttr.count; i++) {
        const vx = posAttr.getX(i);
        const vz = posAttr.getZ(i);
        let wave =
          Math.sin(vx * 0.35 + clock) * 0.35 +
          Math.cos(vz * 0.4 + clock * 0.8) * 0.3;

        // Cursor proximity swell
        const dx = vx - mouse.worldX;
        const dz = vz - mouse.worldZ;
        const dist = Math.sqrt(dx * dx + dz * dz);
        if (dist < 5.5) {
          wave += Math.cos((dist / 5.5) * (Math.PI / 2)) * 1.05;
        }

        // Click shockwaves
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

      // 2. Move constellation nodes and rebuild connecting lines
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

      // 3. Subtle camera parallax with cursor
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
   * 2. HERO / CARD ASTROLABE GLOBE (#wi-three-canvas)
   * ========================================================================== */
  function initHeroGlobe() {
    const container = document.getElementById("wi-three-canvas");
    if (!container || typeof THREE === "undefined") return;

    const width = container.clientWidth || 420;
    const height = container.clientHeight || 420;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100);
    camera.position.set(0, 0.4, 4.4);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    const root = new THREE.Group();
    scene.add(root);

    const sphereGeo = new THREE.SphereGeometry(1.35, 24, 18);
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0xc8922e,
      wireframe: true,
      transparent: true,
      opacity: 0.26,
    });
    const globe = new THREE.Mesh(sphereGeo, wireMat);
    root.add(globe);

    const coreGeo = new THREE.SphereGeometry(1.31, 24, 18);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0x1a1410,
      transparent: true,
      opacity: 0.65,
    });
    root.add(new THREE.Mesh(coreGeo, coreMat));

    const ringGeo1 = new THREE.RingGeometry(1.62, 1.64, 64);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0xd99b38,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.45,
    });
    const ring1 = new THREE.Mesh(ringGeo1, ringMat);
    ring1.rotation.x = Math.PI / 2.6;
    ring1.rotation.y = 0.3;
    root.add(ring1);

    const ringGeo2 = new THREE.RingGeometry(1.82, 1.835, 64);
    const ring2 = new THREE.Mesh(ringGeo2, ringMat);
    ring2.rotation.x = -Math.PI / 3.2;
    ring2.rotation.z = 0.4;
    root.add(ring2);

    const beaconPositions = [
      [0.85, 0.62, 0.88],
      [0.72, 0.48, 1.05],
      [0.95, 0.35, 0.90],
      [-0.65, 0.78, 0.91],
      [0.42, -0.55, 1.18],
      [-0.82, -0.42, 0.98],
      [0.15, 0.98, 0.92],
      [-0.38, 0.52, 1.19],
    ];
    const dotGeo = new THREE.SphereGeometry(0.05, 12, 12);
    const dotMat = new THREE.MeshBasicMaterial({ color: 0xffb347 });

    beaconPositions.forEach(function (pos) {
      const v = new THREE.Vector3(pos[0], pos[1], pos[2]).normalize().multiplyScalar(1.37);
      const dot = new THREE.Mesh(dotGeo, dotMat);
      dot.position.copy(v);
      root.add(dot);
    });

    let targetRotX = 0.15;
    let targetRotY = 0;
    window.addEventListener("pointermove", function (e) {
      targetRotY = (e.clientX / window.innerWidth - 0.5) * 0.65;
      targetRotX = 0.15 + (e.clientY / window.innerHeight - 0.5) * 0.45;
    });

    renderer.render(scene, camera);
    if (reduceMotion) return;

    function animate() {
      requestAnimationFrame(animate);
      globe.rotation.y += 0.0032;
      ring1.rotation.z += 0.002;
      ring2.rotation.z -= 0.0016;
      root.rotation.y += (targetRotY - root.rotation.y) * 0.05;
      root.rotation.x += (targetRotX - root.rotation.x) * 0.05;
      renderer.render(scene, camera);
    }
    animate();

    window.addEventListener("resize", function () {
      const w = container.clientWidth || 420;
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
