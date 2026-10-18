"""Render statue layers with three.js in headless Chromium. usage: python3 render_statue.py frames.json"""
import asyncio, base64, json, sys, threading, functools, http.server, socketserver, os, time
from playwright.async_api import async_playwright
ROOT = os.path.dirname(os.path.abspath(__file__))
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
def serve(port):
    h = functools.partial(Q, directory=ROOT)
    with socketserver.TCPServer(("127.0.0.1", port), h) as s: s.serve_forever()
async def main(jobs, port):
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        pg.on("console", lambda m: print("console:", m.text) if m.type == "error" else None)
        await pg.goto(f"http://127.0.0.1:{port}/index.html")
        await pg.wait_for_function("window.ready === true", timeout=120000)
        t0 = time.time()
        for i, j in enumerate(jobs):
            if os.path.exists(j["out"]) and not j.get("force"):
                continue
            url = await pg.evaluate("p => window.renderFrame(p)", j)
            open(j["out"], "wb").write(base64.b64decode(url.split(",", 1)[1]))
            if i % 30 == 0:
                print("frame", i, len(jobs), round(time.time() - t0, 1), flush=True)
        await b.close()
if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1]))
    port = 8700 + (os.getpid() % 200)
    threading.Thread(target=serve, args=(port,), daemon=True).start()
    time.sleep(0.5)
    asyncio.run(main(jobs, port))
