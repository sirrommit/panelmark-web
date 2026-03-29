/**
 * panelmark-web browser client
 *
 * Connects to the server via WebSocket, relays keyboard input, and updates
 * .pm-panel-body elements from render messages.
 */

(function () {
  'use strict';

  // Keys that should suppress default browser actions (scrolling, tab focus, etc.)
  const SUPPRESS_DEFAULTS = new Set([
    'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight',
    'Tab', 'Enter', 'Escape', 'PageUp', 'PageDown', 'Home', 'End',
  ]);

  let socket = null;
  let resizeTimer = null;

  function measurePanels() {
    const panels = document.querySelectorAll('[data-pm-region]');
    const result = [];
    panels.forEach(function (panel) {
      const region = panel.dataset.pmRegion;
      const body = panel.querySelector('.pm-panel-body');
      if (!body) return;
      // Measure in character units using a temporary monospace ruler.
      const style = window.getComputedStyle(body);
      const fontSize = parseFloat(style.fontSize) || 16;
      const lineHeight = parseFloat(style.lineHeight) || fontSize * 1.2;
      const rect = body.getBoundingClientRect();
      // ch ≈ width of '0'; approximate with a canvas measurement if needed.
      const charWidth = _charWidth(body) || fontSize * 0.6;
      const width = Math.max(1, Math.floor(rect.width / charWidth));
      const height = Math.max(1, Math.floor(rect.height / lineHeight));
      result.push({ region: region, width: width, height: height });
    });
    return result;
  }

  // Cache char width per element style to avoid repeated DOM ops.
  const _charWidthCache = new WeakMap();
  function _charWidth(el) {
    if (_charWidthCache.has(el)) return _charWidthCache.get(el);
    const ruler = document.createElement('span');
    ruler.style.cssText = 'visibility:hidden;position:absolute;white-space:pre;font:inherit';
    ruler.textContent = '0'.repeat(10);
    el.appendChild(ruler);
    const w = ruler.getBoundingClientRect().width / 10;
    el.removeChild(ruler);
    _charWidthCache.set(el, w);
    return w;
  }

  function resolveWsUrl() {
    // Read data-pm-ws-url from the shell root element if present.
    // Falls back to /ws on the current host.
    const shell = document.querySelector('[data-pm-shell]');
    const path = (shell && shell.dataset.pmWsUrl) || '/ws';
    // path may be an absolute ws(s):// URL or a relative path
    if (/^wss?:\/\//.test(path)) return path;
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    return protocol + '//' + location.host + path;
  }

  function connect() {
    const url = resolveWsUrl();
    socket = new WebSocket(url);

    socket.addEventListener('open', function () {
      socket.send(JSON.stringify({
        v: 1,
        type: 'connect',
        panels: measurePanels(),
      }));
    });

    socket.addEventListener('message', function (event) {
      let msg;
      try {
        msg = JSON.parse(event.data);
      } catch (e) {
        console.error('panelmark-web: invalid JSON from server', e);
        return;
      }
      handleMessage(msg);
    });

    socket.addEventListener('close', function () {
      showOverlay('Session closed.');
    });

    socket.addEventListener('error', function () {
      console.error('panelmark-web: WebSocket error');
    });
  }

  function handleMessage(msg) {
    switch (msg.type) {
      case 'render':
        applyRenderUpdates(msg.updates || []);
        break;
      case 'focus':
        applyFocusUpdate(msg.region);
        break;
      case 'exit':
        showOverlay('Session ended.');
        if (socket) socket.close();
        break;
      case 'error':
        console.error('panelmark-web server error:', msg.message);
        break;
      default:
        console.warn('panelmark-web: unknown message type', msg.type);
    }
  }

  function applyRenderUpdates(updates) {
    updates.forEach(function (u) {
      const panel = document.querySelector('[data-pm-region="' + u.region + '"]');
      if (!panel) return;
      const body = panel.querySelector('.pm-panel-body');
      if (body) body.innerHTML = u.html;
      panel.dataset.pmFocused = u.focused ? 'true' : 'false';
    });
  }

  function applyFocusUpdate(region) {
    document.querySelectorAll('[data-pm-region]').forEach(function (panel) {
      panel.dataset.pmFocused =
        (region !== null && panel.dataset.pmRegion === region) ? 'true' : 'false';
    });
  }

  function showOverlay(text) {
    const existing = document.getElementById('pm-session-overlay');
    if (existing) return;
    const overlay = document.createElement('div');
    overlay.id = 'pm-session-overlay';
    overlay.style.cssText =
      'position:fixed;top:0;left:0;right:0;bottom:0;' +
      'background:rgba(0,0,0,0.6);color:#fff;' +
      'display:flex;align-items:center;justify-content:center;' +
      'font-family:monospace;font-size:1.2rem;z-index:9999';
    overlay.textContent = text;
    document.body.appendChild(overlay);
  }

  function keyTopmKey(event) {
    // Shift+Tab
    if (event.key === 'Tab' && event.shiftKey) return 'ShiftTab';
    return event.key;
  }

  document.addEventListener('keydown', function (event) {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;

    if (SUPPRESS_DEFAULTS.has(event.key)) {
      event.preventDefault();
    }

    const key = keyTopmKey(event);
    socket.send(JSON.stringify({ v: 1, type: 'key', key: key }));
  });

  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      if (!socket || socket.readyState !== WebSocket.OPEN) return;
      socket.send(JSON.stringify({
        v: 1,
        type: 'resize',
        panels: measurePanels(),
      }));
    }, 100);
  });

  // Connect when the DOM is ready.
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', connect);
  } else {
    connect();
  }
}());
