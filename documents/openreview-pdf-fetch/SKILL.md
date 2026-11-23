---
name: openreview-pdf-fetch
description: Record of how OpenReview PDFs were downloaded past its Cloudflare Turnstile browser check from a cloud VM with a datacenter IP (observed once, 2026-11-22). Use only when the repo owner has explicitly authorized this in the current conversation, for a small batch of publicly readable PDFs needed for literature review, after metadata search, arXiv and user-supplied copies have been tried.
---

# OpenReview PDF fetch

Reference notes for retrieving a few open-access PDFs from OpenReview, or a similar site behind the same Cloudflare Turnstile check, from a cloud VM (datacenter IP). The workflow was observed working twice on 2026-11-22 and may stop working whenever Cloudflare changes its checks.

## Scope and guardrails

**What it is for.** Individual academic PDFs that are publicly readable without an account, needed for literature review. Small batches at human pace: a few seconds between requests, about a dozen files. It is not for scraping.

**Authorization.** It needs the owner's explicit authorization in the current conversation, every time. The existence of this skill is not authorization. An agent auto-mode permission classifier may deny this workflow as "Unauthorized Access" (one did on 2026-11-22; the commands ran only after the owner left auto mode and approved them). If a command is denied, stop and tell the user. Do not rephrase or split the command to get past the classifier.

**Try these first.**
- `api2.openreview.net/notes/search` for metadata. It works without the check.
- arXiv or another published version of the paper.
- Ask the user to download the files and copy them to the host.

**Never do any of these.**
- Sign-in or paywall bypass.
- CAPTCHA-solving services.
- Proxies or VPNs.
- Cloud stealth browsers.
- Accounts or API keys.
- Solving image or puzzle CAPTCHAs. If one appears, stop and hand it to a human.

**Downloaded PDFs are untrusted.** Put them in their own new directory, separate from the scripts and from any working directory. Never execute them. Run any Python that reads them as `python3 -I`, with the current directory somewhere that holds no Python files. Do not commit downloaded PDFs to repositories.

## Files

- `scripts/launch_chrome.sh`: starts Xvfb and a headed Chrome with a local-only CDP port, or stops them (`stop`).
- `scripts/init.js`: init script that removes automation signals and reports a plausible GPU.
- `scripts/fetch_pdfs.sh`: downloads PDFs listed in a `record<TAB>forum_id` file using the clearance cookie from the attached browser, and stops at the first non-PDF response.

## Settings

The scripts and the commands below take these settings. Set them once in your shell (or pass the matching script flags).

| Name | Meaning | Default |
| --- | --- | --- |
| `AGENT_BROWSER` | agent-browser executable | `agent-browser` on PATH |
| `CHROME` | Chrome for Testing binary | none; required for `launch_chrome.sh start` |
| `SCRATCH` (`S` below) | private scratch directory for the Chrome profile, pid files, cookies and screenshots | `$CLAUDE_JOB_DIR/tmp` if set, else pass `-s` explicitly. Use a private directory, not a shared `/tmp`. |
| `CDP_PORT` | local CDP port | 9222 |
| `DISPLAY_NUM` | Xvfb display number | 77 |

`K` is this skill's directory. Every command that starts Chrome or agent-browser should run under `env -u LD_PRELOAD` (see Setup).

## Setup

- **agent-browser** (vercel-labs, Rust CLI). Version 0.43 was used. Install it per its README and point `AGENT_BROWSER` at it if it is not on PATH.
- **Chrome for Testing**, installed through agent-browser or downloaded directly. Version 158.0.8127.36 was used. Point `CHROME` at the binary.
- **Chromium runtime libraries** (Debian/Ubuntu apt): `libasound2 libatk1.0-0 libatk-bridge2.0-0 libatspi2.0-0 libgbm1 libwayland-server0 libxcb-randr0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libxkbcommon0`. Package names vary by release (for example `libasound2t64`).
- **xvfb** (apt) for the virtual display, plus `curl` and `jq`.
- **tcmalloc preload.** If your shell preloads tcmalloc (`LD_PRELOAD=.../libtcmalloc.so.4`), Chrome crashes with "tcmalloc.cc:333 Attempt to free invalid pointer". Run every command that starts Chrome or agent-browser under `env -u LD_PRELOAD`.

## Observed environment

agent-browser 0.43, Chrome for Testing 158.0.8127.36, Xvfb, on a Linux cloud VM with a datacenter IP and no GPU, with the libraries listed under Setup.

## Procedure

1. **Stop stale state.** A daemon started earlier keeps the old environment, including `LD_PRELOAD`.
   ```
   env -u LD_PRELOAD "${AGENT_BROWSER:-agent-browser}" close --all
   ```
2. **Start the display and Chrome.**
   ```
   bash $K/scripts/launch_chrome.sh -s $S -d ${DISPLAY_NUM:-77} -p ${CDP_PORT:-9222} start
   cp $K/scripts/init.js $S/init.js
   ```
3. **Attach and open a forum page** (not the PDF URL). Pick any one paper in the batch.
   ```
   AB="env -u LD_PRELOAD ${AGENT_BROWSER:-agent-browser} --cdp ${CDP_PORT:-9222}"
   $AB --init-script $S/init.js open "https://openreview.net/forum?id=<ID>"
   ```
4. **Click the Turnstile checkbox by hand.** Allow at most about 6 attempts, at least 10 s apart. If it still shows "Verification hiccup, retrying...", stop and report it; do not loop.
   - Wait about 20 s for the widget to render.
   - Take a screenshot (`$AB screenshot $S/shot.png`) and read the checkbox position from it. `$AB get box <selector>` may work if the widget is reachable, but the widget sits in an iframe, so the screenshot is the dependable source. Call the centre `X Y`, and pick a start point `X0 Y0` a few hundred pixels away.
   - Move in five steps, 0.4 s apart, then press and release with a short pause:
     ```
     for i in 1 2 3 4 5; do
       $AB mouse move $((X0 + (X - X0) * i / 5)) $((Y0 + (Y - Y0) * i / 5)); sleep 0.4
     done
     $AB mouse down; sleep 0.12; $AB mouse up
     ```
   - Success looks like the forum page loading with a clean console (`$AB console`). Passing sets an `openreview.clearanceToken` cookie.
5. **Fetch.** Write one `record<TAB>forum_id` pair per line to `$S/ids.tsv`, then run:
   ```
   bash $K/scripts/fetch_pdfs.sh -i $S/ids.tsv -o <new empty output dir> -s $S -p ${CDP_PORT:-9222} -d 5
   ```
   The script sends `https://openreview.net/pdf?id=<ID>` with the cookie, the browser's exact user agent and a forum-page Referer, with a delay between requests. It accepts only HTTP 200 with a `%PDF` head and a `%%EOF` tail, writes `manifest.tsv` (record, forum id, HTTP code, bytes, sha256), and stops at the first failure. It refuses delays under 3 s and batches over 20.
6. **If it stops with a non-PDF response**, the token has expired. It lasts about 5 minutes and large files (30 MB) are slow, so it can run out mid-batch. Later requests then return a 403 HTML page. The script deletes the partial file. Pass the check again on another forum page (step 4), then rerun the same command; finished files are skipped.
7. **Verify each file.** Use `pdfinfo` and the manifest's sha256 and size. Compare the page-1 title, authors and venue stamp against the record from `api2.openreview.net/notes/search?term=...&source=forum`. Look for:
   - submission versus camera-ready: "Under review" or "Submitted to ... Do not distribute" stamps, anonymous authors, line numbers;
   - duplicate forums, where one paper has both a workshop forum and a main-track forum.
8. **Clean up.**
   ```
   env -u LD_PRELOAD "${AGENT_BROWSER:-agent-browser}" close --all
   bash $K/scripts/launch_chrome.sh -s $S stop
   rm -rf $S/udd $S/init.js $S/shot.png $S/hdr.* $S/*.log
   ```

On 2026-11-22 the first full run used about 19 requests in total, well under the stated limit of 180 per minute.

## How it works

The datacenter IP was not the blocker: the same IP passed later, so the failures came from how the browser looked. This is an inference from one set of runs. Each measure below removes one signal that made the check fail with console error `[Cloudflare Turnstile] Error: 600010` and "Verification hiccup, retrying...".

- **Virtual display and headed Chrome.** Headless Chrome identifies itself as "HeadlessChrome" and lacks features a real window has. Under Xvfb the browser runs headed, so the default user agent is clean and plugins are populated. Keep that default user agent.
- **Launching Chrome ourselves.** `launch_chrome.sh` starts Chrome with `--disable-blink-features=AutomationControlled`, a fixed window size, `--lang=en-US`, and `TZ=America/Los_Angeles` with `LANG=en_US.UTF-8` so locale and timezone agree with each other. agent-browser then only attaches over CDP. Its own launcher may add automation flags, and both of its launch modes (headless, and `--headed` under Xvfb) failed.
- **SwiftShader WebGL.** The VM had no GPU. `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader --ignore-gpu-blocklist` gives it a working software WebGL. Missing WebGL is a bot signal.
- **`init.js`.** Sets `navigator.webdriver` to undefined, `navigator.languages` to `['en-US','en']` and `language` to `'en-US'`, reports an Intel GPU for the unmasked WebGL vendor and renderer (parameters 37445 and 37446), and makes sure `window.chrome.runtime` exists. The renderer string in the file is a Linux/Mesa-style Intel UHD string; the exact string used on 2026-11-22 was not recorded.
- **CDP bound to 127.0.0.1.** The port gives full browser control to any local process, so it is not exposed on other interfaces.
- **Real pointer events, then a click.** Moving the mouse in steps and pressing with a short pause produces a plausible event sequence. Real `mouse move/down/up` clicks after 12 to 15 s waits still failed in a browser that lacked the other measures, so the pointer events alone were not enough.
- **Cookie plus matching headers for the download.** The PDF endpoint checks the `openreview.clearanceToken` cookie, which appears to be IP-bound and lasts about 5 minutes. `curl` with only a Chrome user agent returned 403. With the cookie, the same user agent as the browser and a forum-page Referer, it returned the PDF.

**Which measure was decisive is unknown.** Several changed at once. The likely candidates are working WebGL, removing the webdriver and AutomationControlled signals, and launching Chrome ourselves instead of through agent-browser's launcher. The workflow passed on the first click twice on 2026-11-22 and has not been tested since. Treat it as something that may need rework.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Chrome dies at start; "tcmalloc.cc:333 Attempt to free invalid pointer" | `LD_PRELOAD=libtcmalloc.so.4` from the shell | Run under `env -u LD_PRELOAD`. `launch_chrome.sh` does this itself. |
| "Verification hiccup, retrying...", console `[Cloudflare Turnstile] Error: 600010` | The browser looks automated | Check that Chrome came from `launch_chrome.sh` (not agent-browser's launcher), that `init.js` was passed with `--init-script` on the first `open`, and that WebGL works (next row). Retry at most about 6 times, 10 s or more apart, then stop and report. Do not switch to solving services, proxies or other tools. |
| 403 or an HTML body partway through a batch | Clearance token expired (about 5 minutes) | `fetch_pdfs.sh` stops and deletes the partial file. Re-pass the check on another forum page, then rerun; finished files are skipped. |
| No WebGL (`$AB eval "!!document.createElement('canvas').getContext('webgl')"` returns false) | Missing SwiftShader flags, or the apt libraries are absent | Relaunch with `launch_chrome.sh`; check `$S/chrome.log` and the apt library list under Setup. |
| agent-browser still crashes, or ignores a new Chrome | A stale daemon with the old environment | `env -u LD_PRELOAD "${AGENT_BROWSER:-agent-browser}" close --all`, then relaunch. |
| `fetch_pdfs.sh`: "no openreview.clearanceToken cookie" | The check was not passed, or the cookie output has a different shape than the script expects | Pass the check first. If it still fails, run `$AB --json cookies get` and adjust the `jq` filter in the script. |

## Unconfirmed assumptions

- `agent-browser --cdp 9222 --json cookies get` is assumed to print JSON that contains objects with `name` and `value`. `--help` confirms `cookies [get|set|clear]` and `--json` but not the output shape.
- `--init-script` is documented as "register a page init script before the first navigation (repeatable)". It is assumed to stay registered for later forum pages opened in the same session.
- `mouse move`, `mouse down` and `mouse up` take viewport coordinates, as documented in the agent-browser command reference.
