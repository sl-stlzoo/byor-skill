# BYOR facts (verified against github.com/thoughtworks/build-your-own-radar, Nov 2026)

If anything here conflicts with the live upstream README, trust the README and tell the user. Re-check upstream
before publishing if you can browse. Official guide: https://www.thoughtworks.com/radar/byor
Hosted tool: https://radar.thoughtworks.com   Source: https://github.com/thoughtworks/build-your-own-radar (AGPL-3.0)

## Input formats (any one)
- Public Google Sheet (set sharing to "Anyone with the link: Viewer"), private Google Sheet (needs Google sign-in),
  a CSV URL, or a JSON URL. URLs must be publicly reachable by the browser unless self-hosting local files.
- Required columns/fields: `name`, `ring`, `quadrant`, `isNew`, `description`.
- Optional column `status` shows movement: `New`, `Moved In`, `Moved Out`, `No Change` (case-insensitive).
- `isNew` values: `TRUE` / `FALSE`.
- CSV parsed with D3; quote descriptions that contain commas or newlines.
- Descriptions are sanitised; only a whitelist of HTML tags survives. Keep HTML minimal.
- Blip names must be unique.

## Names
- On the hosted site (radar.thoughtworks.com) ring and quadrant names must be among the defaults:
  rings `adopt`, `trial`, `assess`, `caution` (the data value `hold` is still accepted), quadrants `techniques`, `platforms`, `tools`,
  `languages & frameworks`.
- Fourth ring: newer releases call it **Caution**; the value `hold` (any case) is still accepted and displayed
  as Caution.
- A **self-hosted** BYOR has no such restriction. Set custom names with environment variables:
  ```
  export RINGS='["Adopt", "Trial", "Assess", "Caution"]'
  export QUADRANTS='["Techniques", "Platforms", "Tools", "Languages & Frameworks"]'
  ```
  The radar always has 4 quadrants; rings are up to 4.

## Docker (self-hosting, easiest path to custom quadrant names)
```
docker pull wwwthoughtworks/build-your-own-radar
docker run --rm -p 8080:80 \
  -e SERVER_NAMES="localhost 127.0.0.1" \
  -e RINGS='[...]' -e QUADRANTS='[...]' \
  -v /path/to/radar-output:/opt/build-your-own-radar/files \
  wwwthoughtworks/build-your-own-radar:latest
# then open http://localhost:8080 and enter  http://localhost:8080/files/radar.csv
```
Other env vars: `CLIENT_ID` (Google OAuth, needed for private sheets), `API_KEY` (public sheets without auth),
`GTM_ID`, `ADOBE_LAUNCH_SCRIPT_URL`, `ASSET_PATH`.

## Using a file on GitHub
A raw URL (`https://raw.githubusercontent.com/<owner>/<repo>/<branch>/radar.csv`) of a public repo works as the
CSV/JSON URL. Private repos do not work from the hosted site.

## Hosted-site compatibility mode (this repo's `--compat` export)
Because the default business quadrants are custom names, publishing to the hosted site needs either (a) self-hosting
or (b) `--compat`, which renames our four quadrants to the four BYOR defaults in order and prefixes each description
with the real quadrant name in bold. Option (b) is functional but visually mislabelled; recommend (a).
