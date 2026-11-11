# Railway deployment

The Compass Geometry Laboratory runs as one stateless Streamlit web service.
The original four-relationship explorer and Rectangle with Current are both
served by `app.py`. No database, volume, object storage, or application secrets
are required. Railway hosting uses the account's normal usage-based billing.

## Build and start

These are the intended settings for the first deployment. Live infrastructure
has not yet been provisioned for this app.

- Source: `Kighway/ssi-advanced-diver`, branch `main`, repository root.
- Build: root `Dockerfile`, using the maintained Python 3.12 slim image and
  the exact Python dependency versions in `requirements-lock.txt`.
- The Docker build runs all 213 automated tests before producing a release.
- Start: Docker's `CMD` runs `sh scripts/start.sh`.
- The process binds `0.0.0.0` on Railway's `PORT` (8501 for local Docker runs).
- Health check: `/_stcore/health`, with a 120-second startup allowance.
- Restart policy: on failure, up to 3 retries.
- One replica preserves each browser's in-memory Streamlit session.

The local `streamlit run app.py` command still binds to localhost. The cloud
startup script overrides that address; it leaves Streamlit's CORS and XSRF
protections enabled. The container runs as an unprivileged user. Screenshots,
verification artifacts, development caches, and credentials are excluded from
the image.

## Updates and verification

Push commits to `main` to trigger a Railway build and deployment. A failing
test or health check prevents promotion of that release. Open the app, enable
**Dive Navigation Mode**, then select **Rectangle with Current** to verify the
060° / 10° scenario: 120 seconds, 120 metres of swimming, and 21.16 metres of
net displacement toward 150°. Disabling current closes the rectangle exactly.

The health endpoint checks the Streamlit server. The build's AppTest suite
checks Python execution and UI calculations. The GitHub Actions workflow is
configured to build the same image and check a platform-assigned port. After
deployment, verify the live session and controls in a browser over WebSocket.

Deployments and process restarts reset browser session settings. This app does
not persist dive logs or personal data.

## Local container

```bash
docker build -t ssi-advanced-diver .
docker run --rm -p 8501:8501 ssi-advanced-diver
```

Open http://127.0.0.1:8501. To test a platform-assigned port, run:

```bash
docker run --rm -e PORT=8080 -p 8080:8080 ssi-advanced-diver
```

The base image follows the Python 3.12 patch line; Python dependencies are
pinned. Railway service settings are configured directly through its API;
the Dockerfile and startup script are versioned with the source.

## First provision

Create a project named `ssi-advanced-diver` in the intended Railway workspace,
with a `production` environment and one service named `compass-lab`. Connect
`Kighway/ssi-advanced-diver` on `main`, leave the root directory at `/`, and let
Railway detect the Dockerfile. Apply the health check and restart policy above,
then generate a Railway public domain. No manual `PORT` variable or start-command
override is needed. Wait for a successful deployment and a healthy public
endpoint before treating the app as live.
