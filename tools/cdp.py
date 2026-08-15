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
import json, os, shutil, socket, subprocess, tempfile, time, urllib.request, base64
import websocket   # websocket-client

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

def _free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p

class Chrome:
    def __init__(self, width=1280, height=900, reduced_motion=False, mobile=False, extra=()):
        self.w, self.h = width, height
        self.port = _free_port()
        self.profile = tempfile.mkdtemp(prefix="cdp-")
        args = [CHROME, "--headless=new", f"--remote-debugging-port={self.port}",
                f"--user-data-dir={self.profile}", f"--window-size={width},{height}",
                "--hide-scrollbars", "--no-first-run", "--disable-gpu",
                "--disable-features=Translate,MediaRouter", "--mute-audio",
                "--remote-allow-origins=*"]   # DevTools rejects the loopback origin without it
        if reduced_motion: args.append("--force-prefers-reduced-motion")
        args += list(extra)
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        try: self.ws.close()
        except Exception: pass
        try: self.proc.terminate(); self.proc.wait(timeout=5)
        except Exception:
            try: self.proc.kill()
            except Exception: pass
        shutil.rmtree(self.profile, ignore_errors=True)

    def __enter__(self): return self
    def __exit__(self, *a): self.close()
