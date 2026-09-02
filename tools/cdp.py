#!/usr/bin/env python3
"""A real browser on a real clock, with no tab anywhere.

Every visual check in this project ran through `--screenshot` + `--virtual-time-budget`, and that
harness is blind to exactly the things this site is made of: requestAnimationFrame never ticks,
IntersectionObserver never fires, and a programmatic scroll dispatches no scroll event. Three
"unverifiable here" notes in a row is a tooling problem, not a fact about the site.

This drives headless Chrome over the DevTools protocol instead: real timers, real frames, real
observers, screenshots at any moment. It opens no tab in anyone's browser — a throwaway profile,
a port on loopback, killed on exit.

  from cdp import Chrome
  with Chrome(1280, 900) as c:
      c.goto("http://127.0.0.1:4860/index.html?intro=0")
      c.sleep(2.0)
      c.eval("document.querySelector('#seasonring').scrollIntoView({block:'center'})")
      c.shot("out.png")
      print(c.eval("document.getElementById('sr-len').textContent"))
"""
import atexit, json, os, signal, shutil, socket, subprocess, tempfile, time, urllib.request, base64
import websocket   # websocket-client

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Every browser this module opens, so a crash, a Ctrl-C or a plain `return` can never leave one
# resident. A leaked headless Chrome is ~11 processes and well over a gigabyte, and it does not
# exit on its own: the machine just gets hot.
_LIVE = set()

@atexit.register
def _reap_all():
    for c in list(_LIVE):
        try: c.close()
        except Exception: pass

def _on_signal(sig, frm):
    _reap_all()
    raise SystemExit(128 + sig)

for _s in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
    try: signal.signal(_s, _on_signal)
    except Exception: pass          # not the main thread — atexit still covers us

def _free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p

class Chrome:
    def __init__(self, width=1280, height=900, reduced_motion=False, mobile=False, extra=(), gpu=False):
        self.w, self.h = width, height
        self.port = _free_port()
        self.profile = tempfile.mkdtemp(prefix="cdp-")
        args = [CHROME, "--headless=new", f"--remote-debugging-port={self.port}",
                f"--user-data-dir={self.profile}", f"--window-size={width},{height}",
                "--hide-scrollbars", "--no-first-run", "--disable-gpu",
                "--disable-features=Translate,MediaRouter", "--mute-audio",
                "--remote-allow-origins=*",   # DevTools rejects the loopback origin without it
                # keep the process tree small: one browser used to mean ~11 processes and 1.5 GB
                "--renderer-process-limit=1", "--no-zygote", "--disable-breakpad",
                "--disable-dev-shm-usage", "--disable-extensions",
                "--disable-background-networking", "--disable-sync",
                "--disable-component-update", "--disable-domain-reliability"]
        if gpu:
            # WebGL never initialises under --disable-gpu, so every measurement taken with it
            # is blind to the site's own sky — the most expensive thing on the page.
            args = [a for a in args if a != "--disable-gpu"]
            args += ["--use-angle=swiftshader", "--enable-unsafe-swiftshader",
                     "--enable-features=Vulkan,UseSkiaRenderer"]
        if reduced_motion: args.append("--force-prefers-reduced-motion")
        args += list(extra)
        # its own process group, so close() can take the renderers down with the leader
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     start_new_session=True)
        _LIVE.add(self)
        ws_url, deadline = None, time.time() + 25
        while time.time() < deadline:
            try:
                j = json.loads(urllib.request.urlopen(
                    f"http://127.0.0.1:{self.port}/json/list", timeout=2).read())
                pages = [t for t in j if t["type"] == "page"]
                if pages: ws_url = pages[0]["webSocketDebuggerUrl"]; break
            except Exception: time.sleep(0.25)
        if not ws_url: self.close(); raise RuntimeError("chrome did not come up")
        self.ws = websocket.create_connection(ws_url, timeout=60)
        self._id = 0
        self.send("Page.enable"); self.send("Runtime.enable"); self.send("Log.enable")
        self.send("Runtime.evaluate", expression="1")   # warm
        # Headless clamps --window-size to a 500px minimum, so a phone-width request silently
        # renders at 500 and every "mobile" screenshot is a lie. Always drive the width through
        # the device-metrics override, which has no floor.
        if mobile or width < 500:
            self.resize(width, height, mobile=True, dpr=2)

    def send(self, method, **params):
        self._id += 1
        self.ws.send(json.dumps({"id": self._id, "method": method, "params": params}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get("id") == self._id:
                if "error" in m: raise RuntimeError(f"{method}: {m['error']}")
                return m.get("result", {})

    def goto(self, url, settle=1.2):
        self.send("Page.navigate", url=url); time.sleep(settle)

    def eval(self, js, timeout=30):
        r = self.send("Runtime.evaluate", expression=f"(function(){{ {js} }})()",
                      returnByValue=True, awaitPromise=True)
        if r.get("exceptionDetails"):
            e = r["exceptionDetails"]
            raise RuntimeError("JS: " + (e.get("exception", {}).get("description") or e.get("text", "?")))
        return r.get("result", {}).get("value")

    def sleep(self, s): time.sleep(s)

    def shot(self, path, clip=None):
        p = {"format": "png"}
        if clip:
            # viewport coordinates (what getBoundingClientRect returns), not document ones
            p["clip"] = {"x": clip[0], "y": clip[1], "width": clip[2], "height": clip[3], "scale": 1}
            p["captureBeyondViewport"] = False
        r = self.send("Page.captureScreenshot", **p)
        open(path, "wb").write(base64.b64decode(r["data"]))
        return path

    def resize(self, w, h, mobile=False, dpr=1):
        """Real viewport control; --window-size cannot go below 500px, this can."""
        self.send("Emulation.setDeviceMetricsOverride", width=w, height=h,
                  deviceScaleFactor=dpr, mobile=mobile)
        self.w, self.h = w, h

    def close(self):
        """Idempotent, and it kills the GROUP — terminating the leader alone strands renderers."""
        if getattr(self, "_closed", False): return
        self._closed = True
        _LIVE.discard(self)
        try: self.ws.close()
        except Exception: pass
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try: os.killpg(os.getpgid(self.proc.pid), sig)
            except Exception:
                try: self.proc.send_signal(sig)
                except Exception: pass
            try:
                self.proc.wait(timeout=4); break
            except Exception: pass
        shutil.rmtree(self.profile, ignore_errors=True)

    def __enter__(self): return self
    def __exit__(self, *a): self.close()
