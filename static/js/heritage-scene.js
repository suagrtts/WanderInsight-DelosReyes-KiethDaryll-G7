/**
 * WanderInsight — Interactive Three.js Cebu Heritage Geospatial Globe & Astrolabe
 * Renders a wireframe heritage globe with Cebu landmark coordinate pins (9.0°N–11.5°N, 123.0°E–124.5°E)
 * and orbital rings. Automatically pauses when offscreen or when prefers-reduced-motion is enabled.
 */
(function () {
  function initHeritageScene() {
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

    // Wireframe heritage globe
    const sphereGeo = new THREE.SphereGeometry(1.35, 24, 18);
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0xc8922e,
      wireframe: true,
      transparent: true,
      opacity: 0.22,
    });
    const globe = new THREE.Mesh(sphereGeo, wireMat);
    root.add(globe);

    // Inner core glow sphere
    const coreGeo = new THREE.SphereGeometry(1.31, 24, 18);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0x1a1410,
      transparent: true,
      opacity: 0.65,
    });
    root.add(new THREE.Mesh(coreGeo, coreMat));

    // Astrolabe / GPS boundary rings (BR-06 Regional Bounds 9.0–11.5N, 123.0–124.5E)
    const ringGeo1 = new THREE.RingGeometry(1.62, 1.64, 64);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0xd99b38,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.4,
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

    // Cebu Landmark beacon points around the globe
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
    const dotGeo = new THREE.SphereGeometry(0.045, 12, 12);
    const dotMat = new THREE.MeshBasicMaterial({ color: 0xffb347 });

    beaconPositions.forEach(function (pos) {
      const v = new THREE.Vector3(pos[0], pos[1], pos[2]).normalize().multiplyScalar(1.37);
      const dot = new THREE.Mesh(dotGeo, dotMat);
      dot.position.copy(v);
      root.add(dot);
    });

    // Subtle pointer parallax
    let targetRotX = 0.15;
    let targetRotY = 0;
    window.addEventListener("pointermove", function (e) {
      const nx = (e.clientX / window.innerWidth - 0.5) * 0.5;
      const ny = (e.clientY / window.innerHeight - 0.5) * 0.35;
      targetRotY = nx;
      targetRotX = 0.15 + ny;
    });

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    renderer.render(scene, camera);
    if (reduceMotion) return;

    function animate() {
      requestAnimationFrame(animate);
      globe.rotation.y += 0.0028;
      ring1.rotation.z += 0.0018;
      ring2.rotation.z -= 0.0014;
      root.rotation.y += (targetRotY - root.rotation.y) * 0.04;
      root.rotation.x += (targetRotX - root.rotation.x) * 0.04;
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

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initHeritageScene);
  } else {
    initHeritageScene();
  }
})();
