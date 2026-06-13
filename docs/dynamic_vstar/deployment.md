# Dynamic V* — Label Studio self-host deployment

End-to-end recipe for self-hosting Label Studio Community Edition behind a
free Cloudflare Tunnel and loading V* images for annotation. Follow
top to bottom.

## 0. Prerequisites

- Docker Desktop or Docker Engine running locally (or on a small VPS)
- Cloudflare account with a domain you control (DNS managed by Cloudflare)
- Python 3.10+ with this repo's `requirements.txt` installed for the
  upload/parser scripts
- A Label Studio "owner" email + password you'll create in step 2

## 1. Run Label Studio in Docker

Persistent SQLite + media data in `./ls-data`. Pinning the image tag
(`1.21.0`) keeps schema stable across reboots; bump deliberately.

```bash
mkdir -p ls-data
docker run -d --name labelstudio --restart unless-stopped \
  -p 127.0.0.1:8080:8080 \
  -v "$PWD/ls-data:/label-studio/data" \
  -e LABEL_STUDIO_DISABLE_SIGNUP_WITHOUT_LINK=true \
  -e LABEL_STUDIO_USERNAME=owner@example.com \
  -e LABEL_STUDIO_PASSWORD=change-me-now \
  heartexlabs/label-studio:1.21.0
```

Notes:
- We bind to `127.0.0.1` so the only public path is via Cloudflare Tunnel.
- `DISABLE_SIGNUP_WITHOUT_LINK=true` forces invite links (step 6).
- Verify locally: `curl -I http://127.0.0.1:8080/` should return HTTP 200.

Or use compose (`docker-compose.yml`):

```yaml
services:
  labelstudio:
    image: heartexlabs/label-studio:1.21.0
    restart: unless-stopped
    ports: ["127.0.0.1:8080:8080"]
    volumes: ["./ls-data:/label-studio/data"]
    environment:
      LABEL_STUDIO_DISABLE_SIGNUP_WITHOUT_LINK: "true"
      LABEL_STUDIO_USERNAME: owner@example.com
      LABEL_STUDIO_PASSWORD: change-me-now
```

`docker compose up -d` to start.

## 2. First login + API token

Open http://127.0.0.1:8080 in your browser, log in with the credentials
above, then go to **Account & Settings -> Access Token** and copy the
token. Set it as an env var for the rest of this guide:

```bash
export LS_TOKEN="<paste the token>"
export LS_URL="http://127.0.0.1:8080"   # change to public URL after step 4
```

## 3. Set up Cloudflare Tunnel

Install `cloudflared` (macOS):

```bash
brew install cloudflared
```

Linux: download the deb/rpm from
https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/.

Authenticate and create the tunnel:

```bash
cloudflared tunnel login                       # opens browser; pick the zone
cloudflared tunnel create vstar-labelstudio    # writes ~/.cloudflared/<UUID>.json
```

Route DNS to the tunnel (replace with your hostname):

```bash
cloudflared tunnel route dns vstar-labelstudio label.example.com
```

Create `~/.cloudflared/config.yml`:

```yaml
tunnel: vstar-labelstudio
credentials-file: /Users/<you>/.cloudflared/<UUID>.json

ingress:
  - hostname: label.example.com
    service: http://localhost:8080
    originRequest:
      noTLSVerify: true
  - service: http_status:404
```

Run it:

```bash
cloudflared tunnel run vstar-labelstudio
```

Or install as a service so it survives reboots:

```bash
sudo cloudflared service install
```

Then update the env var so the upload script targets the public URL:

```bash
export LS_URL="https://label.example.com"
```

Browse https://label.example.com — you should see the LS login page over
HTTPS terminated by Cloudflare.

## 4. Create the project

In the LS UI:

1. **Create Project** -> name it `Dynamic V*`.
2. **Labeling Setup** -> **Custom template** -> paste the contents of
   `docs/dynamic_vstar/labelstudio_config.xml` -> **Save**.
3. Note the project ID from the URL (e.g. `/projects/3/data` -> `3`).

```bash
export LS_PROJECT_ID=3
```

## 5. Upload V* images

5 demo images:

```bash
python scripts/upload_vstar_to_labelstudio.py \
  --ls-url "$LS_URL" \
  --ls-token "$LS_TOKEN" \
  --project-id "$LS_PROJECT_ID" \
  --limit 5
```

All 191 images:

```bash
python scripts/upload_vstar_to_labelstudio.py \
  --ls-url "$LS_URL" \
  --ls-token "$LS_TOKEN" \
  --project-id "$LS_PROJECT_ID" \
  --limit 191
```

The script tags each task with `image_id`, `question_id`, and `category`
so annotators can see the V* source on the task page.

## 6. Invite annotators

Label Studio Community Edition has two roles by default: Owner and
Annotator. To invite people:

1. **Organization** (top-right menu) -> **People** -> **Add People**.
2. Click **Reset Link** for each invite to copy a one-shot signup URL.
3. Send each annotator their personal link plus your https hostname.
4. Back in the project, **Settings -> Members** -> add them.

For task assignment, use **Data Manager -> Filter** (e.g. by
`data.category`) and **Actions -> Assign to Annotators** to slice the
work into disjoint batches per the spec's v0 workflow.

## 7. Export and parse

After annotation:

1. Project page -> **Export** -> select **JSON-MIN** -> download the
   `.json` file (e.g. `project-3-at-...json`).
2. Run the parser:

```bash
python scripts/parse_labelstudio_export.py \
  --export ~/Downloads/project-3-at-2026-05-04.json \
  --out data/annotations/dynamic_vstar_v0.jsonl
```

The output JSONL conforms to `docs/dynamic_vstar/annotation_spec.md`
("Output format" section). Validation warnings (missing required
fields, malformed position_relation entries) are printed to stderr;
the rows they refer to are skipped.

## 8. Maintenance

- Backups: snapshot `./ls-data` (SQLite + uploaded media live there).
- Upgrade: `docker pull heartexlabs/label-studio:<newtag>` then
  recreate the container; the volume migrates schema on first boot.
- Logs: `docker logs -f labelstudio`.
- Rotating the API token: regenerate in the LS UI, update `$LS_TOKEN`.

## Troubleshooting

- **Cloudflared "connection refused"**: the LS container isn't
  listening on `127.0.0.1:8080`. Check `docker ps` and the port
  binding.
- **Upload script returns 401**: token wrong or expired; regenerate.
- **Upload returns 400 about label_config**: project's labeling config
  doesn't reference `$image`. Re-paste the XML from
  `labelstudio_config.xml`.
- **Per-region fields don't appear**: ensure the labeling config was
  saved without modification — the parser keys on the exact `name`
  attributes.
- **Parser warns "image has 0 valid boxes"**: the annotator skipped
  required fields; have them complete the region or relax
  `required="true"` in the XML if you want partial entries.
