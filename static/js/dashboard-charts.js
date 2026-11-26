/**
 * WanderInsight — Chart.js Live PostgreSQL Analytics & Form Helpers (SDD F-03, F-05, F-06)
 * Reads live SQL-aggregated series from canvas data-* attributes when available,
 * with graceful fallback when a user has not logged visitation records yet.
 */
(function () {
  function parseJsonAttr(el, attr) {
    const raw = el.getAttribute(attr);
    if (!raw) return null;
    try {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) && parsed.length > 0 ? parsed : null;
    } catch (_err) {
      return null;
    }
  }

  function initCharts() {
    if (typeof Chart === "undefined") return;

    Chart.defaults.font.family = "'DM Sans', -apple-system, sans-serif";
    Chart.defaults.color = "#5C554E";

    // 1. Visitation Trend Line Chart (Curator / Viewer / Admin / Site Detail)
    const trendEl = document.getElementById("wi-visitation-chart");
    if (trendEl) {
      const liveLabels = parseJsonAttr(trendEl, "data-labels");
      const liveValues = parseJsonAttr(trendEl, "data-values");
      const hasLive = Boolean(liveLabels && liveValues);

      const datasets = [
        {
          label: hasLive ? "Recorded Visitors (PostgreSQL)" : "Sample Corridor Baseline",
          data: hasLive ? liveValues : [4120, 4690, 5310, 5890, 6420, 7180],
          borderColor: "#8C3B1A",
          backgroundColor: "rgba(140, 59, 26, 0.12)",
          borderWidth: 2.5,
          fill: true,
          tension: 0.32,
          pointRadius: 4,
          pointBackgroundColor: "#8C3B1A",
        },
      ];

      if (!hasLive) {
        datasets.push({
          label: "Prior Year Reference",
          data: [3650, 3980, 4420, 4910, 5180, 5790],
          borderColor: "#C8922E",
          borderDash: [5, 5],
          borderWidth: 2,
          fill: false,
          tension: 0.32,
          pointRadius: 3,
        });
      }

      new Chart(trendEl, {
        type: "line",
        data: {
          labels: hasLive ? liveLabels : ["May", "Jun", "Jul", "Aug", "Sep", "Oct"],
          datasets: datasets,
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "top", align: "end" },
          },
          scales: {
            y: { beginAtZero: true, grid: { color: "rgba(22, 20, 18, 0.08)" } },
            x: { grid: { display: false } },
          },
        },
      });
    }

    // 2. Demographic Origin Doughnut (BR-01: Local + Domestic + Foreign = Total)
    const demoEl = document.getElementById("wi-demographic-chart");
    if (demoEl) {
      const originValues = parseJsonAttr(demoEl, "data-origin-values");
      const originSum = originValues
        ? originValues.reduce(function (acc, n) {
            return acc + (Number(n) || 0);
          }, 0)
        : 0;

      const chartValues = originSum > 0 ? originValues : [46, 34, 20];
      const chartLabels =
        originSum > 0
          ? [
              "Local Residents (" + originValues[0] + ")",
              "Domestic Tourists (" + originValues[1] + ")",
              "Foreign Tourists (" + originValues[2] + ")",
            ]
          : ["Local Residents (46%)", "Domestic Tourists (34%)", "Foreign Tourists (20%)"];

      new Chart(demoEl, {
        type: "doughnut",
        data: {
          labels: chartLabels,
          datasets: [
            {
              data: chartValues,
              backgroundColor: ["#1E5631", "#C8922E", "#1D5C63"],
              borderWidth: 2,
              borderColor: "#FFFFFF",
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "65%",
          plugins: {
            legend: { position: "bottom" },
          },
        },
      });
    }

    // 3. Admin Role & RBAC Distribution Doughnut (Django Admin Console)
    const roleEl = document.getElementById("wi-admin-role-chart");
    if (roleEl) {
      const admins = parseInt(roleEl.dataset.admins || "1", 10);
      const curators = parseInt(roleEl.dataset.curators || "0", 10);
      const viewers = parseInt(roleEl.dataset.viewers || "0", 10);
      const total = admins + curators + viewers;
      const chartData = total > 0 ? [admins, curators, viewers] : [1, 1, 1];

      new Chart(roleEl, {
        type: "doughnut",
        data: {
          labels: [
            "Administrators (" + admins + ")",
            "Curators (" + curators + ")",
            "Viewers (" + viewers + ")",
          ],
          datasets: [
            {
              data: chartData,
              backgroundColor: ["#7F1D1D", "#1E5631", "#1D5C63"],
              borderWidth: 2,
              borderColor: "#FFFFFF",
              hoverOffset: 6,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "64%",
          plugins: {
            legend: {
              position: "bottom",
              labels: { padding: 14, usePointStyle: true, pointStyle: "circle" },
            },
          },
        },
      });
    }
  }

  function initVisitationSumHelper() {
    const calcBtn = document.getElementById("wi-calc-total-btn");
    const totalInput = document.getElementById("id_total_visitors");
    const liveBadge = document.getElementById("wi-origin-sum-preview");
    const parts = document.querySelectorAll("[data-origin-part]");
    if (!parts.length || !totalInput) return;

    function computeOriginSum() {
      let sum = 0;
      parts.forEach(function (inp) {
        const val = parseInt(inp.value || "0", 10);
        if (!Number.isNaN(val) && val > 0) sum += val;
      });
      if (liveBadge) {
        liveBadge.textContent = String(sum);
      }
      return sum;
    }

    parts.forEach(function (inp) {
      inp.addEventListener("input", computeOriginSum);
    });
    computeOriginSum();

    if (calcBtn) {
      calcBtn.addEventListener("click", function () {
        totalInput.value = String(computeOriginSum());
      });
    }
  }

  function initDoubleSubmitGuard() {
    document.querySelectorAll('main form[method="post"]').forEach(function (form) {
      form.addEventListener("submit", function () {
        if (form.dataset.wiSubmitting === "1") return;
        form.dataset.wiSubmitting = "1";
        const btn = form.querySelector('button[type="submit"]');
        if (btn) {
          btn.disabled = true;
          btn.setAttribute("aria-busy", "true");
        }
      });
    });
  }

  function boot() {
    initCharts();
    initVisitationSumHelper();
    initDoubleSubmitGuard();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
