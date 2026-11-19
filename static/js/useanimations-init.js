/**
 * WanderInsight — Official useAnimations (https://useanimations.com) Micro-Interaction Engine
 * Implements all 6 official useAnimations interaction contracts via lottie-web (SVG renderer):
 *   - loop         : Continuous playback (pauses when offscreen or reduced-motion)
 *   - click-toggle : Switches forward/backward between two states on click
 *   - click-replay : Replays from frame 0 on click (or parent button click)
 *   - hover        : Plays forward on mouseenter/focusin, backward on mouseleave/focusout
 *   - hover-replay : Plays once from frame 0 on mouseenter/focusin without restarting mid-play
 *   - hover-loop   : Loops while hovered, finishes current cycle on mouseleave
 *
 * Also binds interactive password visibility toggle (`visibility-v2` icon from useAnimations)
 * on password fields across Login, Registration, and Change Password forms.
 */
(function () {
  const CDN_BASE = "https://useanimations.com/icons/";
  const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");

  function initUseAnimationNode(el) {
    if (typeof lottie === "undefined" || el.dataset.uaReady === "1") return;
    const id = el.dataset.ua;
    if (!id) return;

    el.dataset.uaReady = "1";
    const interaction = el.dataset.uaInteraction || "hover-replay";
    const size = el.dataset.uaSize || "22";
    el.style.width = size + "px";
    el.style.height = size + "px";
    if (!el.getAttribute("aria-label")) {
      el.setAttribute("aria-hidden", "true");
    }

    const trigger = el.closest("a, button, .list-group-item, .kpi-card, .card-interactive, .ua-trigger") || el;
    const isLoop = interaction === "loop" || interaction === "hover-loop";

    const anim = lottie.loadAnimation({
      container: el,
      renderer: "svg",
      loop: isLoop,
      autoplay: false,
      path: CDN_BASE + id + ".json",
    });

    let toggled = el.dataset.uaActive === "true";

    anim.addEventListener("DOMLoaded", function () {
      const half = Math.floor(anim.totalFrames / 2);
      if (interaction === "loop") {
        anim.goToAndStop(0, true);
        if (!motionQuery.matches) anim.play();
      } else if (interaction === "click-toggle") {
        anim.goToAndStop(toggled ? half : 0, true);
      } else {
        anim.goToAndStop(0, true);
      }
    });

    if (interaction === "loop") {
      motionQuery.addEventListener("change", function (ev) {
        if (ev.matches) anim.goToAndStop(0, true);
        else anim.play();
      });
    } else if (interaction === "hover") {
      const playForward = function () {
        if (motionQuery.matches) return;
        anim.setDirection(1);
        anim.play();
      };
      const playBackward = function () {
        if (motionQuery.matches) return;
        anim.setDirection(-1);
        anim.play();
      };
      trigger.addEventListener("mouseenter", playForward);
      trigger.addEventListener("mouseleave", playBackward);
      trigger.addEventListener("focusin", playForward);
      trigger.addEventListener("focusout", playBackward);
    } else if (interaction === "hover-replay") {
      const replayOnce = function () {
        if (motionQuery.matches) return;
        if (anim.isPaused && anim.totalFrames > 0) {
          anim.playSegments([0, anim.totalFrames], true);
        }
      };
      trigger.addEventListener("mouseenter", replayOnce);
      trigger.addEventListener("focusin", replayOnce);
    } else if (interaction === "hover-loop") {
      const startLoop = function () {
        if (motionQuery.matches) return;
        anim.loop = true;
        if (anim.isPaused) anim.play();
      };
      const finishCycle = function () {
        anim.loop = false;
      };
      trigger.addEventListener("mouseenter", startLoop);
      trigger.addEventListener("mouseleave", finishCycle);
      trigger.addEventListener("focusin", startLoop);
      trigger.addEventListener("focusout", finishCycle);
    } else if (interaction === "click-replay") {
      const triggerReplay = function () {
        if (motionQuery.matches || anim.totalFrames <= 0) return;
        anim.playSegments([0, anim.totalFrames], true);
      };
      trigger.addEventListener("click", triggerReplay);
      trigger.addEventListener("mouseenter", triggerReplay);
    } else if (interaction === "click-toggle") {
      trigger.addEventListener("click", function () {
        if (anim.totalFrames <= 0) return;
        const half = Math.floor(anim.totalFrames / 2);
        const end = anim.totalFrames;
        toggled = !toggled;
        if (motionQuery.matches) {
          anim.goToAndStop(toggled ? half : 0, true);
        } else {
          anim.playSegments(toggled ? [0, half] : [half, end], true);
        }
      });
    }
  }

  // Enhance all password inputs with a live useAnimations visibility-v2 toggle button
  function initPasswordVisibilityToggles() {
    if (typeof lottie === "undefined") return;
    const pwdInputs = document.querySelectorAll('input[type="password"]');
    pwdInputs.forEach(function (input) {
      if (input.dataset.uaPwdReady === "1") return;
      input.dataset.uaPwdReady = "1";

      const wrapper = document.createElement("div");
      wrapper.className = "ua-pwd-wrap position-relative";
      input.parentNode.insertBefore(wrapper, input);
      wrapper.appendChild(input);
      input.style.paddingRight = "2.75rem";

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ua-pwd-btn";
      btn.setAttribute("aria-label", "Toggle password visibility");
      btn.setAttribute("aria-pressed", "false");

      const iconSpan = document.createElement("span");
      iconSpan.className = "ua-icon";
      iconSpan.dataset.ua = "visibility-v2";
      iconSpan.dataset.uaInteraction = "click-toggle";
      iconSpan.dataset.uaSize = "22";
      btn.appendChild(iconSpan);
      wrapper.appendChild(btn);

      initUseAnimationNode(iconSpan);

      btn.addEventListener("click", function () {
        const show = input.type === "password";
        input.type = show ? "text" : "password";
        btn.setAttribute("aria-pressed", show ? "true" : "false");
      });
    });
  }

  // Auto-dismiss flash message alerts after 4 seconds with snappy fade-out (<300ms)
  function initAutoDismissAlerts() {
    const alerts = document.querySelectorAll(".alert.alert-dismissible, ul.messagelist > li");
    alerts.forEach(function (alertEl) {
      setTimeout(function () {
        if (!document.body.contains(alertEl)) return;
        alertEl.style.transition = "opacity 220ms ease, transform 220ms ease";
        alertEl.style.opacity = "0";
        alertEl.style.transform = "translateY(-8px)";
        setTimeout(function () {
          if (typeof bootstrap !== "undefined" && bootstrap.Alert && alertEl.classList.contains("alert")) {
            bootstrap.Alert.getOrCreateInstance(alertEl).close();
          } else if (alertEl.parentNode) {
            alertEl.parentNode.removeChild(alertEl);
          }
        }, 220);
      }, 4000);
    });
  }

  // Immediate loading state feedback on form submission (Doherty Threshold + Web Design Guidelines)
  function initFormSubmitLoading() {
    document.querySelectorAll("form").forEach(function (form) {
      if (form.dataset.wiSubmitReady === "1") return;
      form.dataset.wiSubmitReady = "1";
      form.addEventListener("submit", function () {
        const btn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (!btn || btn.disabled) return;
        btn.setAttribute("aria-busy", "true");
        btn.disabled = true;
        if (btn.tagName === "BUTTON") {
          const textSpan = btn.querySelector("span:not(.ua-icon)");
          if (textSpan) {
            textSpan.textContent = "Working\u2026";
          } else {
            btn.textContent = "Working\u2026";
          }
        }
      });
    });
  }

  function bootUseAnimations() {
    document.querySelectorAll(".ua-icon[data-ua]").forEach(initUseAnimationNode);
    initPasswordVisibilityToggles();
    initAutoDismissAlerts();
    initFormSubmitLoading();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootUseAnimations);
  } else {
    bootUseAnimations();
  }
})();
