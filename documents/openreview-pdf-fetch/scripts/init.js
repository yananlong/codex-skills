// Init script for agent-browser (--init-script). Runs before page scripts in every document.
// It removes the obvious automation signals and reports a plausible GPU. It does not
// solve anything; Turnstile still has to be clicked by hand.
(() => {
  const define = (obj, name, getter) => {
    try {
      Object.defineProperty(obj, name, { get: getter, configurable: true });
    } catch (e) { /* leave the original value */ }
  };

  define(Navigator.prototype, 'webdriver', () => undefined);
  define(Navigator.prototype, 'languages', () => ['en-US', 'en']);
  define(Navigator.prototype, 'language', () => 'en-US');

  // Report an Intel GPU instead of the SwiftShader software renderer.
  const UNMASKED_VENDOR_WEBGL = 37445;
  const UNMASKED_RENDERER_WEBGL = 37446;
  const VENDOR = 'Google Inc. (Intel)';
  const RENDERER = 'ANGLE (Intel, Mesa Intel(R) UHD Graphics 630 (CFL GT2), OpenGL 4.6)';
  for (const name of ['WebGLRenderingContext', 'WebGL2RenderingContext']) {
    const ctx = window[name];
    if (!ctx) continue;
    // A Proxy keeps Function.prototype.toString returning "[native code]".
    ctx.prototype.getParameter = new Proxy(ctx.prototype.getParameter, {
      apply(target, self, args) {
        if (args[0] === UNMASKED_VENDOR_WEBGL) return VENDOR;
        if (args[0] === UNMASKED_RENDERER_WEBGL) return RENDERER;
        return Reflect.apply(target, self, args);
      },
    });
  }

  // Headed Chrome already has window.chrome; make sure runtime exists too.
  if (!window.chrome) window.chrome = {};
  if (!window.chrome.runtime) window.chrome.runtime = {};
})();
