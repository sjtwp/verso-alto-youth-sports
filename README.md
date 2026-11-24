# Verso Alto Youth Sports — Website

Static multi-page site. Every page lives in its own folder (e.g. `sports/soccer/index.html`) so URLs read like `versoaltoyouthsports.com/sports/soccer/`.

Built from the `_build/` folder.

- One-file mode (current, until the domain is connected): `python3 _build/build.py . --single` → everything in `index.html` with `#` links
- Separate-pages mode (for the real domain): `python3 _build/build.py .` → clean URLs like `/sports/soccer/`

Run it — edit sources there (pages, articles, cities, CSS, JS) and rebuild.
