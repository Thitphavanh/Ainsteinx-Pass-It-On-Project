import asyncio, time
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader"])
        pg = await b.new_page()
        r = await pg.evaluate("""() => { const c=document.createElement('canvas'); const g=c.getContext('webgl2'); return g? g.getParameter(g.VERSION)+' | '+g.getParameter(g.RENDERER):'none'; }""")
        print(r); await b.close()
asyncio.run(main())
