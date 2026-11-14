/*
 * Enamel components behaviour, version 0.13.0.
 * Copyright (c) 2026 Mario Carabotta
 * SPDX-License-Identifier: MIT
 * Plain JavaScript, no dependencies, no build step. Load it after the two
 * stylesheets. It does only this: opens and closes a picker dialog, keeps
 * focus inside it, moves focus (stopping at the ends), selects and cancels,
 * and returns focus to where it came from; shows and updates a toast, hides
 * it three seconds after its last update, one at a time; and keeps the
 * picker's layer and the toast clear of the hint bar, however tall it is.
 * It knows nothing about controllers. It answers Up, Down, Enter and Escape
 * and taps, and the same actions are plain functions on window.EnamelUI for
 * apps that handle their own input. It only sets state attributes
 * (data-focused, open, hidden, data-closing) and one measurement, the hint
 * bar's height (--en-c-hintbar-height); it never sets colours, sizes or
 * timings. Leaving animations last as long as the motion tokens say.
 * The styles work without this file.
 */
(function () {
  "use strict";

  var root = document.documentElement;
  var KEYS = { ArrowUp: "up", ArrowDown: "down", Enter: "select", Escape: "cancel", Tab: "stay" };
  var TOAST_TIME = 3000; // how long a toast stays after its last update, in ms

  // A motion token's duration in ms, read from the stylesheet.
  function tokenMs(name) {
    var v = getComputedStyle(root).getPropertyValue(name).trim();
    return /ms$/.test(v) ? parseFloat(v) : (parseFloat(v) || 0) * 1000;
  }

  // Mark el as leaving, wait for its leaving animation if it has one (none in
  // reduced motion), then call done. If el is shown again before then
  // (arrive), the leave is dropped.
  function leave(el, animated, token, done) {
    var turn = el.__enTurn = (el.__enTurn || 0) + 1;
    el.setAttribute("data-closing", "true");
    var name = animated ? getComputedStyle(animated).animationName : "none";
    var finished = false;
    function end(ev) {
      if (finished || (ev && ev.target !== animated)) return;
      finished = true;
      clearTimeout(timer);
      if (animated) animated.removeEventListener("animationend", end);
      if (el.__enTurn !== turn) return;
      el.removeAttribute("data-closing");
      done();
    }
    if (!name || name === "none") return end();
    var timer = setTimeout(end, tokenMs(token) + 50);
    animated.addEventListener("animationend", end);
  }
  function arrive(el) {
    el.__enTurn = (el.__enTurn || 0) + 1;
    el.removeAttribute("data-closing");
  }

  // ---- Picker dialog --------------------------------------------------------

  var picker = null; // { dialog, opener, rows }

  function rowsOf(dialog) {
    return Array.prototype.slice.call(dialog.querySelectorAll(".en-picker__row:not(:disabled)"));
  }
  function focusedRow() {
    if (!picker) return null;
    return picker.rows.filter(function (r) { return r.getAttribute("data-focused") === "true"; })[0] || null;
  }
  function focusRow(row) {
    picker.rows.forEach(function (r) { if (r !== row) r.removeAttribute("data-focused"); });
    row.setAttribute("data-focused", "true");
    if (document.activeElement !== row) row.focus();
  }

  // Open a picker (a .en-dialog holding a .en-picker). Focus goes to the row
  // with autofocus, else the current choice (aria-current="true"), else the
  // first row. opener is where focus returns; it defaults to what had focus.
  function open(dialog, opener) {
    if (picker) close();
    var rows = rowsOf(dialog);
    if (!rows.length) return;
    picker = { dialog: dialog, opener: opener || document.activeElement, rows: rows };
    arrive(dialog);
    if (!dialog.open) {
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
    }
    var first = rows.filter(function (r) { return r.hasAttribute("autofocus"); })[0] ||
                rows.filter(function (r) { return r.getAttribute("aria-current") === "true"; })[0] || rows[0];
    focusRow(first);
  }

  // Close the open picker without choosing anything, and return focus.
  function close() {
    if (!picker) return;
    var p = picker;
    picker = null;
    p.rows.forEach(function (r) { r.removeAttribute("data-focused"); });
    // Stop being modal at once, so the page behind can take focus back while
    // the panel fades out.
    if (p.dialog.open && p.dialog.matches(":modal")) {
      p.dialog.close();
      p.dialog.show();
    }
    if (p.opener && typeof p.opener.focus === "function") p.opener.focus();
    leave(p.dialog, p.dialog.querySelector(".en-picker"), "--en-motion-dialog", function () {
      if (typeof p.dialog.close === "function" && p.dialog.open) p.dialog.close();
      p.dialog.removeAttribute("open");
    });
    return p.dialog;
  }

  function move(step) {
    if (!picker) return false;
    var at = picker.rows.indexOf(focusedRow());
    var next = Math.max(0, Math.min(picker.rows.length - 1, at + step));
    focusRow(picker.rows[next]);
    return true;
  }

  // Choose the focused row. The Cancel row (.en-picker__cancel) cancels.
  // Fires "en-select" on the dialog, with detail.row and detail.value (the
  // row's value attribute).
  function select() {
    var row = focusedRow();
    if (!row) return false;
    if (row.classList.contains("en-picker__cancel")) return cancel();
    var dialog = close();
    dialog.dispatchEvent(new CustomEvent("en-select", { detail: { row: row, value: row.value || row.getAttribute("value") } }));
    return true;
  }

  // Close without choosing. Fires "en-cancel" on the dialog.
  function cancel() {
    var dialog = close();
    if (!dialog) return false;
    dialog.dispatchEvent(new CustomEvent("en-cancel"));
    return true;
  }

  // While a picker is open it takes Up, Down, Enter, Escape and Tab first
  // (capture phase on window) and stops them reaching the app.
  window.addEventListener("keydown", function (ev) {
    if (!picker) return;
    var action = KEYS[ev.key];
    if (!action) return;
    ev.preventDefault();
    ev.stopImmediatePropagation();
    if (action === "up") move(-1);
    else if (action === "down") move(1);
    else if (action === "select") select();
    else if (action === "cancel") cancel();
  }, true);

  // A tap selects the row tapped.
  document.addEventListener("click", function (ev) {
    if (!picker) return;
    var row = ev.target.closest && ev.target.closest(".en-picker__row");
    if (!row || picker.rows.indexOf(row) < 0) return;
    ev.preventDefault();
    focusRow(row);
    select();
  }, true);

  // Focus never leaves an open picker.
  document.addEventListener("focusin", function (ev) {
    if (picker && !picker.dialog.contains(ev.target)) focusRow(focusedRow() || picker.rows[0]);
  }, true);

  // The browser's own Escape handling for dialogs becomes a cancel.
  document.addEventListener("cancel", function (ev) {
    if (picker && ev.target === picker.dialog) {
      ev.preventDefault();
      cancel();
    }
  }, true);

  // ---- Toast ----------------------------------------------------------------

  var toast = { el: null, timer: 0, time: TOAST_TIME };

  function makeToast() {
    var el = document.createElement("div");
    el.className = "en-toast";
    el.setAttribute("role", "status");
    el.setAttribute("aria-live", "polite");
    el.setAttribute("aria-atomic", "true");
    el.hidden = true;
    var icon = document.createElement("span");
    icon.className = "en-toast__icon";
    icon.setAttribute("aria-hidden", "true");
    icon.hidden = true;
    var text = document.createElement("span");
    text.className = "en-toast__text";
    el.appendChild(icon);
    el.appendChild(text);
    document.body.appendChild(el);
    return el;
  }
  function restartTimer() {
    clearTimeout(toast.timer);
    toast.timer = setTimeout(hideToast, toast.time);
  }

  // Show a toast. Replaces any toast already showing. options: icon (an
  // element, usually an svg.en-icon, for the leading icon), time (ms the toast
  // stays after its last update, default 3000), element (an existing .en-toast
  // to use instead of the one this script makes).
  function showToast(text, options) {
    options = options || {};
    var el = options.element || toast.el || (toast.el = makeToast());
    if (toast.current && toast.current !== el) {
      arrive(toast.current);
      toast.current.hidden = true;
    }
    toast.current = el;
    toast.time = options.time || TOAST_TIME;
    var icon = el.querySelector(".en-toast__icon");
    if (icon && "icon" in options) {
      icon.textContent = "";
      if (options.icon) icon.appendChild(options.icon);
      icon.hidden = !options.icon;
    }
    el.querySelector(".en-toast__text").textContent = text;
    arrive(el);
    el.hidden = false;
    restartTimer();
    return el;
  }

  // Change the text of the toast that is showing and restart its timer.
  // With no toast showing, shows one.
  function updateToast(text) {
    var el = toast.current;
    if (!el || el.hidden || el.getAttribute("data-closing") === "true") return showToast(text);
    el.querySelector(".en-toast__text").textContent = text;
    restartTimer();
    return el;
  }

  function hideToast() {
    clearTimeout(toast.timer);
    var el = toast.current;
    if (!el || el.hidden) return;
    leave(el, el, "--en-motion-slow", function () { el.hidden = true; });
  }

  // ---- Hint bar height ------------------------------------------------------

  // The picker's layer and the toast stop --en-c-hintbar-height above the
  // bottom. The hint bar is at least --en-size-bar tall and gets taller when
  // its hints wrap, which CSS alone cannot pass on to them, so this keeps
  // --en-c-hintbar-height on each hint bar's parent element at the bar's real
  // height. A picker or toast inside that parent (the toast this script makes
  // goes in <body>) stops just above it. One hint bar per parent. A hint bar
  // that is hidden (not drawn at all) or removed takes the variable off its
  // parent, so the picker's layer and the toast keep the one-bar gap they
  // had before (--en-size-bar, the variable's default): only a hint bar that
  // is showing moves them, to its real height.
  var BAR_HEIGHT = "--en-c-hintbar-height";
  var barSizes = typeof ResizeObserver === "function" ? new ResizeObserver(function (entries) {
    entries.forEach(function (entry) { measureBar(entry.target); });
  }) : null;
  function measureBar(bar) {
    var scope = bar.isConnected ? bar.parentElement : null;
    if (bar.__enBarScope && bar.__enBarScope !== scope) bar.__enBarScope.style.removeProperty(BAR_HEIGHT);
    bar.__enBarScope = scope;
    if (!scope) return;
    // The bar is measured after zoom (--en-root-size), but the variable is
    // read inside the zoomed page, so it is written in the page's own units.
    var height = bar.getBoundingClientRect().height / (scope.currentCSSZoom || 1);
    if (height > 0) scope.style.setProperty(BAR_HEIGHT, height + "px");
    else scope.style.removeProperty(BAR_HEIGHT);
  }
  function watchBars(node) {
    if (!barSizes || node.nodeType !== 1) return;
    var bars = Array.prototype.slice.call(node.querySelectorAll(".en-hintbar"));
    if (node.matches(".en-hintbar")) bars.push(node);
    bars.forEach(function (bar) { barSizes.observe(bar); measureBar(bar); });
  }
  watchBars(root);
  // Hint bars added (or moved) later.
  if (barSizes && typeof MutationObserver === "function") {
    new MutationObserver(function (records) {
      records.forEach(function (rec) { Array.prototype.forEach.call(rec.addedNodes, watchBars); });
    }).observe(root, { childList: true, subtree: true });
  }

  window.EnamelUI = {
    picker: {
      open: open,
      close: close,
      up: function () { return move(-1); },
      down: function () { return move(1); },
      select: select,
      cancel: cancel,
      isOpen: function () { return !!picker; }
    },
    toast: { show: showToast, update: updateToast, hide: hideToast }
  };
})();
