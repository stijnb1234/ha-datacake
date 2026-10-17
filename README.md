# Datacake for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Custom integration that polls the [Datacake GraphQL API](https://docs.datacake.de/api/graphql-api)
and exposes every active field of every device in a workspace as a Home Assistant sensor.

## Features

- UI setup (config flow): API token, then workspace picker
- One HA device per Datacake device, one sensor per active field
- New fields appear automatically, no reload needed
- Configurable poll interval (default 300 s, minimum 30 s)
- Re-authentication flow when the token is rejected

## Installation

### HACS (custom repository)

1. HACS → ⋮ (top right) → **Custom repositories**
2. Repository: `https://github.com/stijnb1234/ha-datacake`, category: **Integration** → **Add**
3. Search for **Datacake** in HACS, **Download**
4. Restart Home Assistant

### Manual

Copy `custom_components/datacake` into your HA `config/custom_components/` directory and restart.

## Setup

1. In Datacake: **Account Settings → API Token**, create a token.
2. In HA: **Settings → Devices & services → Add integration → Datacake**.
3. Enter the token, pick a workspace.

Change the poll interval later via the integration's **Configure** button.

## Dashboards

Sensors show up automatically. For charts use the built-in `history-graph` or
`statistics-graph` cards. HA records history from the moment of install; Datacake's
own history is not backfilled.

## Limitations

- Cloud polling only; no push.
- Sensors have no units or device classes yet (Datacake field metadata not mapped).
- Read-only.

## License

[MIT](LICENSE)
