// Enamel style guide menu: marks the section in view while scrolling, and
// runs the accent, motion and lighter fallback switches. The current page is already marked in
// the HTML, so the menu works without this; without it the guide shows the
// default accent and follows the device's motion setting.
// It also runs the demos on the Motion page. Plain JavaScript, no libraries.
(function () {
  var menu = document.currentScript.previousElementSibling;
  var root = document.documentElement;
  var links = Array.prototype.slice.call(menu.querySelectorAll(".site-menu__sub a"));
  function mark() {
    var current = null;
    links.forEach(function (a) {
      var s = document.getElementById(a.hash.slice(1));
      if (s && s.getBoundingClientRect().top < innerHeight / 3) current = a;
    });
    if (innerHeight + scrollY >= document.documentElement.scrollHeight - 2) current = links[links.length - 1];
    links.forEach(function (a) {
      if (a === current) a.setAttribute("aria-current", "true");
      else a.removeAttribute("aria-current");
    });
  }

  // A switch is a row of tabs; choosing one marks it selected and sets an
  // attribute on <html>.
  function switcher(selector, data, attribute, initial) {
    var box = menu.querySelector(selector);
    if (!box) return;
    box.hidden = false;
    function choose(value) {
      box.querySelectorAll("[" + data + "]").forEach(function (b) {
        b.setAttribute("aria-selected", String(b.getAttribute(data) === value));
      });
    }
    if (initial) choose(initial);
    box.addEventListener("click", function (ev) {
      var choice = ev.target.closest("[" + data + "]");
      if (!choice) return;
      root.setAttribute(attribute, choice.getAttribute(data));
      choose(choice.getAttribute(data));
    });
  }
  var deviceReduced = matchMedia("(prefers-reduced-motion: reduce)");
  switcher(".site-accent", "data-accent", "data-en-accent", root.getAttribute("data-en-accent"));
  switcher(".site-motion", "data-motion", "data-en-motion",
           root.getAttribute("data-en-motion") || (deviceReduced.matches ? "reduced" : "full"));
  switcher(".site-look", "data-look", "data-en-lighter", root.getAttribute("data-en-lighter") || "false");

  // ---- Motion page demos ------------------------------------------------

  // Whether motion is reduced where el is: the nearest data-en-motion wins,
  // otherwise the device decides.
  function reduced(el) {
    var scope = el.closest("[data-en-motion]");
    var value = scope ? scope.getAttribute("data-en-motion") : null;
    if (value === "reduced") return true;
    if (value === "full" && scope === root) return false;
    return deviceReduced.matches;
  }
  function token(name) {
    return getComputedStyle(root).getPropertyValue(name).trim();
  }
  function ms(name) {
    var v = token(name);
    return /ms$/.test(v) ? parseFloat(v) : parseFloat(v) * 1000;
  }

  // Each token demo, as a Web Animation. In reduced motion it jumps to its end.
  var demos = {
    duration: function (el, name, ease) {
      var dot = el.firstElementChild;
      var travel = el.clientWidth - dot.offsetWidth;
      return dot.animate([{ transform: "translateX(0)" }, { transform: "translateX(" + travel + "px)" }],
        { duration: ms(name), easing: ease || token("--en-ease-standard"), fill: "forwards" });
    },
    curve: function (el, name) {
      return demos.duration(el, "--en-motion-slow", token(name));
    },
    scale: function (el) {
      return el.animate([{ transform: "scale(1)" }, { transform: "scale(" + token("--en-focus-scale") + ")" }],
        { duration: ms("--en-motion-slow"), easing: token("--en-ease-standard"), fill: "forwards" });
    },
    ringin: function (el) {
      return el.animate([{ outlineWidth: token("--en-focus-ring-start") }, { outlineWidth: token("--en-focus-ring-width") }],
        { duration: ms("--en-motion-ring"), easing: token("--en-ease-standard") });
    },
    pulse: function (el) {
      var ease = token("--en-ease-pulse");
      return el.animate([{ opacity: 1, easing: ease }, { opacity: token("--en-pulse-min"), easing: ease }, { opacity: 1 }],
        { duration: ms("--en-pulse-duration"), iterations: parseFloat(token("--en-pulse-count")) });
    }
  };
  function play(el) {
    el.getAnimations({ subtree: true }).forEach(function (a) { a.cancel(); });
    var anim = demos[el.getAttribute("data-motion-demo")](el, el.getAttribute("data-token"));
    if (reduced(el)) anim.finish();
  }

  // Focus moves to the next item in a group, and restarts its motion there.
  function moveFocus(group) {
    var sel = group.querySelector(".en-actionbar") ? ".en-actionbar .en-button" : ".en-tile, .en-row, .en-menu__item";
    var items = Array.prototype.slice.call(group.querySelectorAll(sel));
    var at = items.findIndex(function (i) { return i.getAttribute("data-focused") === "true"; });
    if (at >= 0) items[at].removeAttribute("data-focused");
    items[(at + 1) % items.length].setAttribute("data-focused", "true");
  }

  // The picker and toast demos call components/enamel-components.js, the
  // same file apps use; nothing here re-does what it does.
  var toastCount = 0;
  function info() {
    var tpl = document.getElementById("site-info-icon");
    return tpl ? tpl.content.firstElementChild.cloneNode(true) : null;
  }
  document.addEventListener("en-select", function (ev) {
    var label = ev.detail.row.firstElementChild.textContent;
    window.EnamelUI.toast.show("Chose \u201c" + label + "\u201d", { icon: info() });
  }, true);

  document.addEventListener("click", function (ev) {
    var t = ev.target;
    var opener = t.closest("[data-open-picker]");
    if (opener && window.EnamelUI) return window.EnamelUI.picker.open(document.getElementById(opener.getAttribute("data-open-picker")), opener);
    var tb = t.closest("[data-toast]");
    if (tb && window.EnamelUI) {
      var action = tb.getAttribute("data-toast"), el = tb.getAttribute("data-toast-element");
      if (action === "show") {
        toastCount = 1;
        window.EnamelUI.toast.show("Library updated: 3 new films",
          el ? { element: document.getElementById(el) } : { icon: info() });
      } else if (action === "update") {
        toastCount += 1;
        window.EnamelUI.toast.update("Library updated: " + (toastCount + 2) + " new films");
      } else {
        window.EnamelUI.toast.hide();
      }
      return;
    }
    var replay = t.closest("[data-replay]");
    if (replay) return play(document.getElementById(replay.getAttribute("data-replay")));
    var move = t.closest("[data-move-focus]");
    if (move) return moveFocus(document.getElementById(move.getAttribute("data-move-focus")));
    var current = t.closest("[data-make-current]");
    if (current) {
      var m = document.getElementById(current.getAttribute("data-make-current"));
      m.querySelectorAll("[aria-current]").forEach(function (i) { i.removeAttribute("aria-current"); });
      var f = m.querySelector('[data-focused="true"]');
      if (f) f.setAttribute("aria-current", "page");
      return;
    }
    var step = t.closest("[data-progress-step]");
    if (step) {
      var bar = document.getElementById(step.getAttribute("data-progress-step"));
      var value = (parseFloat(bar.getAttribute("aria-valuenow")) + 20) % 120;
      bar.setAttribute("aria-valuenow", String(value));
      bar.style.setProperty("--value", value + "%");
      document.getElementById(bar.id + "-text").textContent = value + "%";
      return;
    }
    var dot = t.closest("[data-new-dot]");
    if (dot) {
      var tab = document.getElementById(dot.getAttribute("data-new-dot"));
      var old = tab.querySelector(".en-dot");
      if (old) old.remove();
      var d = document.createElement("span");
      d.className = "en-dot";
      d.setAttribute("role", "img");
      d.setAttribute("aria-label", "New");
      tab.appendChild(d);
      return;
    }
    var controls = t.closest("[data-demo-controls]");
    if (!controls) return;
    var toggle = t.closest(".en-toggle");
    if (toggle) toggle.setAttribute("aria-pressed", String(toggle.getAttribute("aria-pressed") !== "true"));
    var tabChoice = t.closest('.en-tab[role="tab"]');
    if (tabChoice) {
      tabChoice.closest('[role="tablist"]').querySelectorAll('[role="tab"]').forEach(function (b) {
        b.setAttribute("aria-selected", String(b === tabChoice));
      });
    }
  });

  addEventListener("scroll", mark, { passive: true });
  addEventListener("DOMContentLoaded", function () {
    mark();
    document.querySelectorAll("[data-motion-demo]").forEach(play);
  });
})();
