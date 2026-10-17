(() => {
  "use strict";
  const $ = (selector, root=document) => root.querySelector(selector);
  const $$ = (selector, root=document) => [...root.querySelectorAll(selector)];
  const toast = (message) => {
    const el = $("#toast");
    if (!el) return;
    el.textContent = message;
    el.classList.add("show");
    window.clearTimeout(toast.timer);
    toast.timer = window.setTimeout(() => el.classList.remove("show"), 3200);
  };

  // Progressive enhancement: content is visible by default; animation never gates visibility.
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const revealEls = $$(".reveal");
  if ("IntersectionObserver" in window && !reducedMotion) {
    revealEls.forEach(el => el.classList.add("reveal-ready"));
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -35px 0px" });
    revealEls.forEach(el => observer.observe(el));
  }

  // Persist a language preference for the localization phase; default content is English.
  const languageButton = $("#language-button");
  const languages = ["EN", "ID", "中文"];
  let langIndex = Math.max(0, languages.indexOf(localStorage.getItem("glory-language") || "EN"));
  const setLanguage = () => {
    languageButton.textContent = languages[langIndex] + " ⌄";
    languageButton.setAttribute("aria-label", "Language selected: " + languages[langIndex] + ". Click to change.");
  };
  setLanguage();
  languageButton?.addEventListener("click", () => {
    langIndex = (langIndex + 1) % languages.length;
    localStorage.setItem("glory-language", languages[langIndex]);
    setLanguage();
    toast("Language preference saved. Full translations are planned for the localization phase.");
  });

  // Modal behavior.
  const openModal = (id) => {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-open");
    $("[role='dialog'] button", modal)?.focus();
  };
  const closeModal = (modal) => {
    modal?.classList.remove("open");
    modal?.setAttribute("aria-hidden", "true");
    document.body.classList.remove("modal-open");
  };
  $("#open-prayer")?.addEventListener("click", () => openModal("prayer-modal"));
  $("#reflection-button")?.addEventListener("click", () => {
    $("#prayer-text").textContent = "Lord, what do I need to lay down today? Where can I practice love? Give me the courage to take one faithful next step. Amen.";
    $("#modal-title").textContent = "Take a moment to reflect.";
    openModal("prayer-modal");
  });
  $("#open-reminders")?.addEventListener("click", () => openModal("reminder-modal"));
  $$("[data-close-modal]").forEach(button => button.addEventListener("click", () => closeModal(button.closest(".modal-backdrop"))));
  $$(".modal-backdrop").forEach(modal => modal.addEventListener("click", event => {
    if (event.target === modal) closeModal(modal);
  }));
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") $$(".modal-backdrop.open").forEach(closeModal);
  });

  // Reminder and audio are independent opt-in preferences. No sound plays automatically.
  const notifyToggle = $("#notify-toggle");
  const audioToggle = $("#audio-toggle");
  const timeInput = $("#reminder-time");
  try {
    notifyToggle.checked = localStorage.getItem("glory-notifications") === "true";
    audioToggle.checked = localStorage.getItem("glory-prayer-audio") === "true";
    timeInput.value = localStorage.getItem("glory-reminder-time") || "08:00";
  } catch (_) { /* Persistent preferences may be unavailable in private browsing. */ }
  $("#save-reminders")?.addEventListener("click", async () => {
    let notificationEnabled = notifyToggle.checked;
    if (notificationEnabled && !("Notification" in window)) {
      notificationEnabled = false;
      notifyToggle.checked = false;
      $("#reminder-feedback").textContent = "This browser doesn't support notifications. You can still use the app without them.";
    } else if (notificationEnabled && Notification.permission !== "granted") {
      const permission = await Notification.requestPermission();
      if (permission !== "granted") {
        notificationEnabled = false;
        notifyToggle.checked = false;
        $("#reminder-feedback").textContent = "Notification permission wasn't granted. Other preferences can still be saved.";
      }
    }
    try {
      localStorage.setItem("glory-notifications", String(notificationEnabled));
      localStorage.setItem("glory-prayer-audio", String(audioToggle.checked));
      localStorage.setItem("glory-reminder-time", timeInput.value || "08:00");
    } catch (_) { /* Show honest feedback even when storage is restricted. */ }
    if ($("#reminder-feedback").textContent === "") {
      $("#reminder-feedback").textContent = "Preferences saved on this device. Reliable scheduled delivery will be added with the notification service in a later phase.";
    }
    toast("Your preferences have been saved on this device.");
  });

  // Scripture guidance is a small curated reflection, not an AI or a personal prophecy.
  $("#ask-form")?.addEventListener("submit", async event => {
    event.preventDefault();
    const form = event.currentTarget;
    const question = $("#question").value.trim();
    const response = $("#ask-response");
    if (!question) {
      response.textContent = "Write a question or concern first, and we'll make space for it.";
      return;
    }
    const submit = $("button[type='submit']", form);
    if (submit) submit.disabled = true;
    response.textContent = "Finding a Scripture reflection for your question…";
    try {
      const csrfToken = $("input[name='csrfmiddlewaretoken']", form)?.value || "";
      const result = await fetch(form.action, {
        method: "POST",
        headers: {"X-CSRFToken": csrfToken, "X-Requested-With": "XMLHttpRequest"},
        body: new URLSearchParams({question})
      });
      const data = await result.json();
      if (!result.ok) throw new Error(data.error || "We couldn't prepare a reflection just now.");
      response.replaceChildren();
      const heading = document.createElement("strong");
      heading.className = "guidance-reference";
      heading.textContent = data.reference;
      const passage = document.createElement("p");
      passage.className = "guidance-passage";
      passage.textContent = "“" + data.passage + "”";
      const reflectionHeading = document.createElement("strong");
      reflectionHeading.textContent = "A moment to reflect";
      const reflection = document.createElement("p");
      reflection.textContent = data.reflection;
      const note = document.createElement("small");
      note.textContent = data.note;
      response.append(heading, passage, reflectionHeading, reflection, note);
    } catch (error) {
      response.textContent = error.message || "The reflection couldn't be loaded. Please try again.";
    } finally {
      if (submit) submit.disabled = false;
    }
  });

  // Installability and service worker; avoid interrupting the first visit.
  if ("serviceWorker" in navigator && location.protocol.startsWith("http")) {
    window.addEventListener("load", () => navigator.serviceWorker.register("/service-worker.js").catch(() => {}));
  }
  let deferredInstallPrompt = null;
  window.addEventListener("beforeinstallprompt", event => {
    event.preventDefault();
    deferredInstallPrompt = event;
    const installButton = $("#install-app");
    if (installButton) installButton.hidden = false;
  });
  $("#install-app")?.addEventListener("click", async () => {
    if (!deferredInstallPrompt) return toast("Use your browser menu and choose Install app or Add to Home Screen.");
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
  });

  // Rating prompt: ask only after repeated meaningful use, and never repeatedly nag.
  try {
    const count = Number(localStorage.getItem("glory-visit-count") || "0") + 1;
    localStorage.setItem("glory-visit-count", String(count));
    if (count >= 5 && !localStorage.getItem("glory-rating-dismissed")) {
      const rating = document.createElement("div");
      rating.className = "rating-nudge";
      rating.innerHTML = '<span>✧</span><div><strong>Has GLORY blessed your day?</strong><small>Help us make this spiritual space better.</small></div><button type="button" aria-label="Dismiss rating prompt">×</button>';
      rating.querySelector("button").addEventListener("click", () => {
        localStorage.setItem("glory-rating-dismissed", "true");
        rating.remove();
      });
      document.body.appendChild(rating);
    }
  } catch (_) {}
})();
