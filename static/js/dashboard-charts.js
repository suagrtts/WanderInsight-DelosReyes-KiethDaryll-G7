/**
 * WanderInsight — Chart.js Analytics Preview (SDD F-05 & F-06)
 * Renders sample heritage visitation trends (SQL LAG() MoM series), demographic breakdown (BR-01),
 * and weather correlation charts on role dashboards.
 */
(function () {
  function initCharts() {
    if (typeof Chart === "undefined") return;

    Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
    Chart.defaults.color = "#5C554E";

    // 1. Monthly Visitation Trend Line Chart (Curator / Viewer / Admin)
    const trendEl = document.getElementById("wi-visitation-chart");
    if (trendEl) {
      new Chart(trendEl, {
        type: "line",
        data: {
          labels: ["May", "Jun", "Jul", "Aug", "Sep", "Oct"],
          datasets: [
            {
              label: "Total Visitors",
              data: [4120, 4690, 5310, 5890, 6420, 7180],
              borderColor: "#8C3B1A",
              backgroundColor: "rgba(140, 59, 26, 0.12)",
              borderWidth: 2.5,
              fill: true,
              tension: 0.35,
              pointRadius: 4,
              pointBackgroundColor: "#8C3B1A",
            },
            {
              label: "Prior Year Baseline",
              data: [3650, 3980, 4420, 4910, 5180, 5790],
              borderColor: "#C8922E",
              borderDash: [5, 5],
              borderWidth: 2,
              fill: false,
              tension: 0.35,
              pointRadius: 3,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "top", align: "end" },
          },
          scales: {
            y: { beginAtZero: false, grid: { color: "rgba(222,214,198,0.5)" } },
            x: { grid: { display: false } },
          },
        },
      });
    }

    // 2. Demographic Origin Doughnut (BR-01: Local + Domestic + Foreign = Total)
    const demoEl = document.getElementById("wi-demographic-chart");
    if (demoEl) {
      new Chart(demoEl, {
        type: "doughnut",
        data: {
          labels: ["Local Residents (46%)", "Domestic Tourists (34%)", "Foreign Tourists (20%)"],
          datasets: [
            {
              data: [46, 34, 20],
              backgroundColor: ["#1E5631", "#C8922E", "#1D5C63"],
              borderWidth: 2,
              borderColor: "#FFFFFF",
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: "66%",
          plugins: {
            legend: { position: "bottom" },
          },
        },
      });
    }

    // 3. Admin Role & RBAC Distribution Doughnut (BR-10: Administrators, Curators, Viewers)
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

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCharts);
  } else {
    initCharts();
  }
})();
