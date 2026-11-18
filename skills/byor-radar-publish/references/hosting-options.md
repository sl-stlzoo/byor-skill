# Hosting options in detail

Facts verified against the upstream README (Nov 2026). The hosted site is https://radar.thoughtworks.com.
Enter the URL into the box on the home page and click "Build my radar".

## A. Local Docker, custom names (private; recommended)
Prereq: Docker installed. From the user's working directory:
```
python scripts/state_to_radar.py radar-state.json
bash scripts/serve_local.sh radar-state.json 8080
```
`serve_local.sh` runs:
```
docker run --rm -p 8080:80 \
  -e SERVER_NAMES="localhost 127.0.0.1" \
  -e RINGS='["Adopt","Trial","Assess","Caution"]' \
  -e QUADRANTS='["Business Operations & Finance","Customers & Members","Service & Workplace","Security & Infrastructure"]' \
  -v "$PWD/radar-output":/opt/build-your-own-radar/files \
  wwwthoughtworks/build-your-own-radar:latest
```
Then open http://localhost:8080 and enter `http://localhost:8080/files/radar.csv`.
To update: edit state, re-run the export, refresh the page (file is read from the mounted folder).

## B. Self-hosted for a team
Run the same image on an internal server or container platform behind your normal authentication/reverse proxy. Keep the
same `RINGS` and `QUADRANTS` variables. Mount a folder (or bake the file into a derived image) and point users at
`https://<your-host>/files/radar.csv`. For private Google Sheets, also set `CLIENT_ID` (and optionally `API_KEY`) and
add your origin to the OAuth client's "Authorized JavaScript origins".

## C. Hosted site + public Google Sheet (compat names)
1. `python scripts/state_to_radar.py radar-state.json --compat`
2. In Google Sheets: File > Import > Upload `radar.csv` (replace spreadsheet), header row must be the first row.
3. Share > General access > Anyone with the link > Viewer.
4. Copy the sheet URL and paste it into BYOR's box.
Public means anyone with the link can read the data.

## D. Hosted site + raw CSV on GitHub (compat names)
1. Put `radar.csv` in a PUBLIC repository.
2. Use the raw URL: `https://raw.githubusercontent.com/<owner>/<repo>/<branch>/radar.csv`.
3. Paste it into the BYOR box. Private repos do not work from the hosted site.

## E. Hosted site + private Google Sheet (compat names)
Same as C but keep the sheet restricted. BYOR prompts for Google sign-in; the viewer must have access.

## Compat mode, explained to the user
The hosted site only accepts the four default quadrant names. Compat mode maps your quadrants, in order, to
`techniques`, `platforms`, `tools`, `languages & frameworks` and prefixes each description with your real quadrant name.
The picture therefore shows the wrong quadrant labels. For correct labels, use A or B.

## Troubleshooting
| Symptom | Likely cause | Fix |
|---|---|---|
| Blank radar / "Oops" | URL not public, wrong sheet tab, or header row missing | open the URL in a private window; make sure the first row is the header |
| Some blips missing | ring or quadrant name not recognised | run `validate_radar.py --hosted` (hosted) or check `RINGS`/`QUADRANTS` (self-host) |
| 404 on `/files/radar.csv` | volume not mounted or wrong path | confirm `-v` path and that `radar-output/radar.csv` exists |
| Fourth ring shows "Caution" | upstream normalises "hold" to "Caution" | expected; or set `--hold-label Caution` for consistency |
| Garbled commas | description not quoted | re-export with the script (it quotes correctly) |
| Hosted site rejects quadrant names | custom names on the hosted site | use `--compat` or self-host |
| Browser blocks the CSV (CORS/mixed content) | file served from an origin without CORS, or http page loading https | host the radar and file on the same origin (Route A/B) |
| Docker not available | no Docker | use Route C/D with compat, or run the app with Node (`npm install && npm run dev` in the upstream repo) |
