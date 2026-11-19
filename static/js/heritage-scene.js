/**
 * WanderInsight — Full-Viewport Interactive Three.js Background + Standalone 3D Holographic Globe
 * 1) #wi-bg-canvas: Full-window interactive 3D topographic terrain mesh + heritage constellation
 *    that ripples around the mouse cursor and emits shockwaves on click.
 * 2) #wi-three-canvas: Standalone free-floating 3D Holographic Globe (not clipped inside a box)
 *    with GLSL Fresnel + scanline shader, Fibonacci lattice, geodesic telemetry arcs, pulsing
 *    Cebu landmark beacons, and interactive click-and-drag 360° orbit rotation.
 */
(function () {
  const motionMq = window.matchMedia("(prefers-reduced-motion: reduce)");
  let reduceMotion = motionMq.matches;
  motionMq.addEventListener("change", function (e) {
    reduceMotion = e.matches;
  });

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
    renderer.domElement.setAttribute("role", "img");
    renderer.domElement.setAttribute("aria-label", "Interactive 3D topographic wave and heritage constellation background");
    host.replaceChildren(renderer.domElement);

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
   * 2. STANDALONE REALISTIC 3D EARTH GLOBE (#wi-three-canvas)
   *    Free-floating realistic 3D planet with deep ocean, green continents,
   *    elevated highland relief, specular water reflections, soft drifting
   *    cloud layer, sky-blue atmosphere rim, Cebu heritage landmark pins,
   *    and click-and-drag 360° interactive rotation.
   * ========================================================================== */
  function initHeroGlobe() {
    const container = document.getElementById("wi-three-canvas");
    if (!container || typeof THREE === "undefined") return;

    const width = container.clientWidth || 460;
    const height = container.clientHeight || 420;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    camera.position.set(0, 0.12, 4.75);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.domElement.setAttribute("role", "img");
    renderer.domElement.setAttribute("aria-label", "Interactive 3D Earth globe with Cebu cultural heritage beacons. Drag to rotate.");
    container.replaceChildren(renderer.domElement);

    const root = new THREE.Group();
    scene.add(root);

    // 1. Realistic GLSL Procedural Earth Shader (Blue Oceans, Specular Sun Glint,
    //    Coastal Shallows, Lush Green Forests/Plains, Highland Mountains & Cloud Layer)
    const earthUniforms = {
      uTime: { value: 0 },
      uLightDir: { value: new THREE.Vector3(0.75, 0.55, 0.9).normalize() },
    };

    const earthVert = [
      "varying vec3 vNormal;",
      "varying vec3 vViewPos;",
      "varying vec3 vLocalPos;",
      "void main() {",
      "  vLocalPos = normalize(position);",
      "  vNormal = normalize(normalMatrix * normal);",
      "  vec4 mvPos = modelViewMatrix * vec4(position, 1.0);",
      "  vViewPos = -mvPos.xyz;",
      "  gl_Position = projectionMatrix * mvPos;",
      "}"
    ].join("\n");

    const earthFrag = [
      "uniform float uTime;",
      "uniform vec3 uLightDir;",
      "varying vec3 vNormal;",
      "varying vec3 vViewPos;",
      "varying vec3 vLocalPos;",
      "",
      "// 3D Simplex-like FBM noise for realistic continental coastlines & islands",
      "float hash(vec3 p) {",
      "  p = fract(p * 0.3183099 + 0.1);",
      "  p *= 17.0;",
      "  return fract(p.x * p.y * p.z * (p.x + p.y + p.z));",
      "}",
      "float noise(vec3 x) {",
      "  vec3 i = floor(x);",
      "  vec3 f = fract(x);",
      "  f = f * f * (3.0 - 2.0 * f);",
      "  return mix(",
      "    mix(mix(hash(i + vec3(0,0,0)), hash(i + vec3(1,0,0)), f.x),",
      "        mix(hash(i + vec3(0,1,0)), hash(i + vec3(1,1,0)), f.x), f.y),",
      "    mix(mix(hash(i + vec3(0,0,1)), hash(i + vec3(1,0,1)), f.x),",
      "        mix(hash(i + vec3(0,1,1)), hash(i + vec3(1,1,1)), f.x), f.y), f.z);",
      "}",
      "float fbm(vec3 p) {",
      "  float v = 0.0;",
      "  float a = 0.52;",
      "  for (int i = 0; i < 5; i++) {",
      "    v += a * noise(p);",
      "    p = p * 2.07 + vec3(1.7, 9.2, 3.4);",
      "    a *= 0.5;",
      "  }",
      "  return v;",
      "}",
      "",
      "void main() {",
      "  vec3 N = normalize(vNormal);",
      "  vec3 V = normalize(vViewPos);",
      "  vec3 L = normalize(uLightDir);",
      "",
      "  // Continental elevation field",
      "  vec3 p = vLocalPos * 2.45 + vec3(0.4, 1.1, 2.2);",
      "  float h = fbm(p);",
      "  float detail = fbm(vLocalPos * 9.5);",
      "  float seaLevel = 0.495;",
      "",
      "  // Realistic Ocean Palette (deep ocean -> turquoise coastal shelf)",
      "  vec3 deepOcean = vec3(0.05, 0.23, 0.46);",
      "  vec3 midOcean  = vec3(0.08, 0.36, 0.62);",
      "  vec3 shallow   = vec3(0.14, 0.58, 0.71);",
      "  float waterDepth = clamp((seaLevel - h) / 0.22, 0.0, 1.0);",
      "  vec3 oceanCol = mix(shallow, mix(midOcean, deepOcean, waterDepth), smoothstep(0.0, 0.65, waterDepth));",
      "",
      "  // Realistic Land Palette (sandy beach -> lush emerald lowland -> deep forest -> mountain -> polar/peak)",
      "  vec3 sandCol     = vec3(0.84, 0.78, 0.58);",
      "  vec3 lushGreen   = vec3(0.20, 0.54, 0.24);",
      "  vec3 deepForest  = vec3(0.11, 0.38, 0.17);",
      "  vec3 highland    = vec3(0.46, 0.42, 0.29);",
      "  vec3 mountainTop = vec3(0.88, 0.89, 0.90);",
      "",
      "  float landElev = clamp((h - seaLevel) / 0.28, 0.0, 1.0);",
      "  vec3 landCol = mix(sandCol, lushGreen, smoothstep(0.0, 0.10, landElev));",
      "  landCol = mix(landCol, deepForest, smoothstep(0.12, 0.48, landElev + detail * 0.15));",
      "  landCol = mix(landCol, highland, smoothstep(0.52, 0.80, landElev));",
      "  landCol = mix(landCol, mountainTop, smoothstep(0.80, 0.98, landElev));",
      "",
      "  // Polar latitude snow caps",
      "  float lat = abs(vLocalPos.y);",
      "  landCol = mix(landCol, vec3(0.95, 0.97, 0.99), smoothstep(0.76, 0.88, lat + detail * 0.08));",
      "",
      "  // Smooth anti-aliased coastline transition",
      "  float isLand = smoothstep(seaLevel - 0.008, seaLevel + 0.008, h);",
      "  vec3 surfaceCol = mix(oceanCol, landCol, isLand);",
      "",
      "  // Soft drifting atmospheric clouds",
      "  vec3 cloudPos = vLocalPos * 3.4 + vec3(uTime * 0.015, 0.0, -uTime * 0.01);",
      "  float clouds = smoothstep(0.55, 0.78, fbm(cloudPos));",
      "  surfaceCol = mix(surfaceCol, vec3(0.98, 0.99, 1.0), clouds * 0.55);",
      "",
      "  // Directional sunlight + ambient sky hemisphere + ocean specular sun reflection",
      "  float diff = max(dot(N, L), 0.0);",
      "  float ambient = 0.34;",
      "  vec3 H = normalize(L + V);",
      "  float spec = pow(max(dot(N, H), 0.0), 36.0) * (1.0 - isLand) * (1.0 - clouds * 0.8) * 0.55;",
      "",
      "  // Soft natural blue atmosphere rim",
      "  float fresnel = pow(1.0 - max(dot(N, V), 0.0), 2.8);",
      "  vec3 atmoCol = vec3(0.38, 0.72, 0.96);",
      "",
      "  vec3 finalCol = surfaceCol * (ambient + diff * 0.82) + vec3(1.0, 0.97, 0.90) * spec;",
      "  finalCol = mix(finalCol, atmoCol, fresnel * 0.38);",
      "  gl_FragColor = vec4(finalCol, 1.0);",
      "}"
    ].join("\n");

    const earthGeo = new THREE.SphereGeometry(1.42, 64, 48);
    const earthMat = new THREE.ShaderMaterial({
      uniforms: earthUniforms,
      vertexShader: earthVert,
      fragmentShader: earthFrag,
    });
    const earthMesh = new THREE.Mesh(earthGeo, earthMat);
    root.add(earthMesh);

    // 2. Soft Sky-Blue Outer Atmosphere Halo
    const atmoGeo = new THREE.SphereGeometry(1.51, 48, 36);
    const atmoMat = new THREE.ShaderMaterial({
      vertexShader: earthVert,
      fragmentShader: [
        "varying vec3 vNormal;",
        "varying vec3 vViewPos;",
        "void main() {",
        "  float rim = pow(1.0 - abs(dot(normalize(vNormal), normalize(vViewPos))), 3.2);",
        "  gl_FragColor = vec4(0.35, 0.70, 0.95, rim * 0.32);",
        "}"
      ].join("\n"),
      transparent: true,
      depthWrite: false,
      side: THREE.BackSide,
    });
    root.add(new THREE.Mesh(atmoGeo, atmoMat));

    // 3. Subtle Brass Heritage Equator Ring & Cebu Landmark Pins
    const ringMatGold = new THREE.MeshBasicMaterial({
      color: 0xc8922e,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.32,
    });
    const ring1 = new THREE.Mesh(new THREE.RingGeometry(1.66, 1.678, 72), ringMatGold);
    ring1.rotation.x = Math.PI / 2.25;
    ring1.rotation.y = 0.25;
    root.add(ring1);

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

    const dotGeo = new THREE.SphereGeometry(0.036, 12, 12);
    const dotMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b });
    const haloGeo = new THREE.RingGeometry(0.048, 0.068, 24);
    const haloMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.8,
    });

    const pulseHalos = [];
    beaconPositions.forEach(function (pos, idx) {
      const surfaceVec = new THREE.Vector3(pos[0], pos[1], pos[2]).normalize().multiplyScalar(1.435);
      const dot = new THREE.Mesh(dotGeo, dotMat);
      dot.position.copy(surfaceVec);
      beaconGroup.add(dot);

      const halo = new THREE.Mesh(haloGeo, haloMat.clone());
      halo.position.copy(surfaceVec.clone().multiplyScalar(1.005));
      halo.lookAt(surfaceVec.clone().multiplyScalar(2));
      halo.userData = { phase: idx * 0.8 };
      beaconGroup.add(halo);
      pulseHalos.push(halo);
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
      earthUniforms.uTime.value = t;

      // Gentle floating bob
      root.position.y = Math.sin(t * 0.8) * 0.05;

      // Rotate Earth & landmarks together
      earthMesh.rotation.y += 0.0025;
      beaconGroup.rotation.y += 0.0025;
      ring1.rotation.z += 0.0018;

      for (let i = 0; i < pulseHalos.length; i++) {
        const h = pulseHalos[i];
        const s = 1 + 0.45 * (0.5 + 0.5 * Math.sin(t * 2.2 + h.userData.phase));
        h.scale.set(s, s, 1);
        h.material.opacity = 1.05 - s * 0.5;
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
