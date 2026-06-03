> **Fork** — This is a community-maintained fork of [bugy/script-server](https://github.com/bugy/script-server) (original author: [@bugy](https://github.com/bugy)). The upstream project is no longer actively maintained.

[![CI](https://github.com/knep/script-server/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/knep/script-server/actions/workflows/ci.yml)

## What's new in this fork

### 2026-05-28 — Frontend migrated to Vue 3 + Vite + Vitest

The web frontend was upgraded from Vue 2 (Vue CLI + Webpack + Karma) to a modern toolchain:

- **Vue 2 → Vue 3**: v-model refactor (`value`/`input` → `modelValue`/`update:modelValue`),
  `emits` declarations, lifecycle hook renames (`beforeDestroy`/`destroyed` →
  `beforeUnmount`/`unmounted`), removal of `Vue.set`/`Vue.delete`/`$set`/`$delete` (Vue 3
  Proxy reactivity), `:deep()` CSS selectors, and Vue Router 4 / Vuex 4.
- **Vue CLI + Webpack → Vite**: faster builds; assets are emitted into a single hashed
  `web/assets/` folder (the server's web-build check was updated accordingly).
- **Karma + Mocha → Vitest** (jsdom): the unit suite runs headless without a browser
  (`npm run test:unit-ci`). A few materialize-CSS browser-only behaviours (dropdown/modal
  animations, layout measurements) are skipped under jsdom.
- Removed the obsolete `vue.config.js`, `babel.config.js`, and Karma entry point.

Dev commands are unchanged: `npm run serve` (dev server) and `npm run build` (production build).

### 2026-05-28 — docker-compose.yml for easy deployment

A `docker-compose.yml` is now included at the root of the repository for quick local deployments:

```bash
# Start
docker compose up -d

# Stop
docker compose down
```

Mount your script configs in `./conf/runners/` and logs will be written to `./logs/`.  
See the full [docker-compose instructions](#with-docker-compose) below.

### 2026-05-28 — Frontend unit tests for `date` and `time` components

Unit tests added for the `DateField` and `TimeField` Vue components (42 tests total), covering label/input rendering, two-way value binding, and required-field validation.

### 2026-05-28 — Docker image on GitHub Container Registry

A Docker image for this fork is now published automatically on every commit to `master`:

```bash
docker run -d \
  -p 5000:5000 \
  -v /path/to/your/conf/runners:/app/conf/runners \
  -v /path/to/your/logs:/app/logs \
  ghcr.io/knep/script-server:latest
```

Available tags: `latest` (master), `stable`, and semver tags (e.g. `1.19.0`) on git releases.  
See the full [installation instructions](#as-a-docker-container) below.

### 2026-05-28 — New `time` parameter type

A new `time` parameter type shows a native time picker in the UI and passes the selected time to the script in a configurable format.

**Configuration example:**
```json
{
  "name": "start_time",
  "type": "time",
  "time_format": "%H:%M"
}
```

- `time_format` is a Python [strftime](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes) format string. Default: `%H:%M` (24-hour HH:MM).
- The UI always shows a native time picker. The script receives the time in the configured format.
- An invalid `time_format` (e.g. `"HH:MM"` instead of `"%H:%M"`) is now detected at startup with a clear error message.

### 2026-05-28 — HTTP security headers

All responses (including WebSocket upgrade responses) now include the following security headers:

| Header | Value | Condition |
|--------|-------|-----------|
| `X-Content-Type-Options` | `nosniff` | Always |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Always |
| `Content-Security-Policy` | `default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self' ws: wss:; frame-ancestors 'none'; object-src 'none'` | Always |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Always |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | HTTPS only (`cookie_secure: true`) |

`X-Frame-Options: DENY` was already present; `frame-ancestors 'none'` in the CSP provides equivalent coverage for modern browsers.

### 2025-05-27 — New `date` parameter type

A new `date` parameter type shows a native date picker in the UI and passes the selected date to the script in a configurable format.

**Configuration example:**
```json
{
  "name": "start_date",
  "type": "date",
  "date_format": "%d/%m/%Y"
}
```

- `date_format` is a Python [strftime](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes) format string. Default: `%Y-%m-%d` (ISO 8601).
- The UI always shows a calendar date picker. The script receives the date in the configured format.
- An invalid `date_format` (e.g. `"DD/MM/YYYY"` instead of `"%d/%m/%Y"`) is now detected at startup with a clear error message.

### 2025-05-27 — GitHub Actions CI + secure cookies

- GitHub Actions CI added ([view workflows](https://github.com/knep/script-server/actions)): Python 3.10/3.11/3.12/3.13 matrix + Node 22 frontend tests on every push and pull request.
- Cookies (`username`, `token`, XSRF) are now set with `HttpOnly`, `SameSite=Lax`, and `Secure` flags. The `Secure` flag can be disabled in `conf.json` via `"cookie_secure": false` for HTTP-only deployments.

### 2025-05-27 — Python 3.12/3.13 compatibility

**Python version support:** updated minimum from Python 3.7 (end-of-life since June 2023) to **Python 3.9+** (Python 3.13 recommended).

**Python 3.13 note:** the `crypt` standard-library module was removed in Python 3.13. If your `htpasswd` file contains DES-crypt passwords (entries that do not start with `$2y$`, `$apr1$`, or `{SHA}`), the server will refuse to start with a clear error message. Regenerate those passwords using bcrypt (`htpasswd -B`) or SHA-1 (`htpasswd -s`).

**Fixes:**
- Replaced invalid string escape sequences (`\d`, `\w`, `\/`, `\ `, `\|`, `\p`, `\[`, `\.`) with raw strings (`r'...'`) in test files — these would become `SyntaxError` in Python 3.14
- Replaced deprecated `thread.setDaemon(True)` with `thread.daemon = True` in `user_file_storage.py` and `auth_abstract_oauth.py`

**Dependencies (`requirements.txt`):**
- Raised Tornado floor from `>=4` to `>=6.1` (Tornado 4/5 are incompatible with Python 3.12)
- Added `requests>=2.28` as an explicit dependency (used by HTTP notification destinations)
- Documented optional dependencies (`ldap3`, `bcrypt`) with install instructions

---

# script-server

Script-server is a Web UI for scripts.

As an administrator, you add your existing scripts into Script server and other users would be able to execute them via a web interface.
The UI is very straightforward and can be used by non-tech people.

No script modifications are needed - you configure each script in Script server and it creates the corresponding UI with parameters and takes care of validation, execution, etc.

[Admin interface screenshots](https://github.com/bugy/script-server/wiki/Admin-interface)

## Features
- Different types of script parameters (text, integer, date, time, flag, dropdown, file upload, etc.)
- Real-time script output
- Users can send input during script execution
- Auth (optional): LDAP, Google OAuth, htpasswd file
- Access control
- Alerts
- Logging and auditing
- Formatted output support (colors, styles, cursor positioning, clearing)
- Download of script output files
- Execution history
- Admin page for script configuration

For more details check [how to configure a script](https://github.com/bugy/script-server/wiki/Script-config)
or [how to configure the server](https://github.com/bugy/script-server/wiki/Server-configuration)

## Requirements

### Server-side

Python 3.9 or higher (Python 3.12 recommended) with the following modules:

* tornado >= 6.1
* requests >= 2.28

Optional modules (required only for specific features):

| Module | Feature |
|--------|---------|
| `ldap3 >= 2.9` | LDAP authentication |
| `bcrypt >= 4.0` | bcrypt password support in htpasswd auth |

Install all dependencies at once:
```bash
pip install -r requirements.txt
```

Install with optional dependencies:
```bash
pip install -r requirements.txt ldap3>=2.9 bcrypt>=4.0
```

OS support:

- Linux (main). Tested and working on Debian 10, 11
- Windows (additional). Light testing
- macOS (additional). Light testing

### Client-side

Any more or less up to date browser with enabled JS

Internet connection is **not** needed. All the files are loaded from the server.

## Installation
### For production
1. Download script-server.zip from [Latest release](https://github.com/bugy/script-server/releases/latest) (last upstream release: v1.18.0)
2. Create a script-server folder anywhere on your machine and extract the zip content into it
3. Install dependencies: `pip install -r requirements.txt`

For detailed steps on Linux with virtualenv, see the [Installation guide](https://github.com/bugy/script-server/wiki/Installing-on-virtualenv-(linux)).

##### As a Docker container

Images for this fork are published on [GitHub Container Registry](https://github.com/knep/script-server/pkgs/container/script-server):

```bash
# Pull the latest image (built from master)
docker pull ghcr.io/knep/script-server:latest

# Run with your script configs and logs persisted
docker run -d \
  -p 5000:5000 \
  -v /path/to/your/conf/runners:/app/conf/runners \
  -v /path/to/your/logs:/app/logs \
  ghcr.io/knep/script-server:latest
```

Available tags:
| Tag | Source |
|-----|--------|
| `latest` | `master` branch — most recent changes |
| `stable` | `stable` branch |
| `1.2.3` / `1.2` | Git tag `v1.2.3` |

##### With docker-compose

A ready-to-use `docker-compose.yml` is included at the root of the repository:

```bash
# Clone or download docker-compose.yml, then:
docker compose up -d
```

Place your script runner configs in `./conf/runners/` (created automatically on first run).  
Execution logs are written to `./logs/`.

To customise the server (auth, SSL, port…), uncomment the optional volume lines in `docker-compose.yml`:

```yaml
volumes:
  - ./conf/runners:/app/conf/runners
  - ./logs:/app/logs
  # - ./conf/conf.json:/app/conf/conf.json:ro   # server config
  # - ./conf/.htpasswd:/app/conf/.htpasswd:ro   # htpasswd auth
  # - ./conf/theme:/app/conf/theme:ro           # custom CSS/images
```

### For development
1. Clone this repository
2. Run `tools/init.py --no-npm`

`init.py` should be run after pulling any new changes.

**Frontend** (`web-src/`, Vue 3 + Vite). If you are making changes to web files:
- `npm install` once to install dependencies
- `npm run serve` — Vite dev server (proxies API calls to the backend on port 5000)
- `npm run build` — production build into `web/`
- `npm run test:unit-ci` — run the Vitest unit suite (headless, jsdom)

### A note on OpenBSD and some other UNIX systems
See [OpenBSD process termination issues](https://github.com/bugy/script-server/wiki/OpenBSD-process-termination-issues).


## Setup and run
1. Create configurations for your scripts in the *conf/runners/* folder (see [script config page](https://github.com/bugy/script-server/wiki/Script-config) for details)
2. Launch launcher.py from the script-server folder
  * Windows: `launcher.py`
  * Linux/macOS: `./launcher.py`
3. Add/edit scripts on the admin page

By default, the server will run on http://localhost:5000

### Server config
All the features listed above and some other minor features can be configured in *conf/conf.json*.
It is allowed not to create this file — default values will be used in that case.
See [server config page](https://github.com/bugy/script-server/wiki/Server-configuration) for details.

#### Running over plain HTTP (e.g. local dev)

Cookies (including the XSRF token) are sent with the `Secure` flag by default, so
they are **not stored by the browser over plain HTTP**. Combined with the default
`token` XSRF protection — which requires the browser to read the `_xsrf` cookie and
echo it back — this makes every `POST` (e.g. *starting an execution*) fail with
`403` and an *"XSRF token missing or invalid"* message.

When serving over HTTP (not HTTPS), set `cookie_secure` to `false` in `conf/conf.json`:

```json
{
  "security": {
    "cookie_secure": false
  }
}
```

Alternatively, switch XSRF protection to header mode (`"xsrf_protection": "header"`),
which validates the `X-Requested-With` header instead of a cookie token and so does
not depend on cookies at all. Keep the secure defaults for any HTTPS deployment.

> Tip: if you previously ran with the secure defaults, clear the stale `_xsrf` cookie
> for the site (or use a fresh browser profile) after changing these settings.

### Admin panel
Admin panel is accessible at admin.html (e.g. http://localhost:5000/admin.html)

## Logging

All web/operating logs are written to *logs/server.log*.
Each script's logs are written to a separate file in *logs/processes*. File name format:
`{script_name}_{client_address}_{date}_{time}.log`

## Testing/demo

Script-server has bundled configs/scripts for testing/demo purposes, located in the samples folder. You can
link/copy these config files (`samples/configs/*.json`) to the server config folder (`conf/runners`).

## Security

Script-server is designed to be secure and invulnerable to attacks, injections or user data leaks. However, to be
on the safe side, it's better to run Script server only on a trusted network.

### Shell commands injection

Script server guarantees that all user parameters are passed to an executable script as arguments and won't be executed
under any conditions. There is no way to inject a fraudulent command from the client side. However, user parameters are not
escaped, so scripts should take care of not executing them directly (the general recommendation for bash is to wrap all
arguments in double-quotes). Using typed parameters is recommended when appropriate, as they are validated for
proper values and are harder to exploit.

_Important!_ Command injection protection is fully supported for Linux, but _only_ for .bat and .exe files on Windows.

### XSS and CSRF

_(v1.0 - v1.16)_
Script server _is_ vulnerable to these attacks.

_(v1.17+)_
Script server is protected against XSRF attacks via a special token.
XSS protection: the code is written according to
[OWASP Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html)
and the only **known** vulnerabilities are:

* `output_format`=`html_iframe`, see the reasoning in the
  linked [Wiki page](https://github.com/bugy/script-server/wiki/Script-config#output_format)

## Contribution

If you find a bug or want to propose a feature, please [open an issue](https://github.com/knep/script-server/issues) on this fork.

Contributions are welcome:
- Bug reports and feature proposals
- Pull requests (fixes, features, documentation)
- Any other improvements you can think of
