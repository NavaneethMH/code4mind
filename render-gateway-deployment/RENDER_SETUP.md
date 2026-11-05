# Free Render gateway setup

This is a separate deployment package for the model gateway. Do not submit it as the competition source ZIP.

1. Create a **private** GitHub repository and upload these four files to its root: `gateway_example.py`, `Dockerfile`, `render.yaml`, and this guide.
2. In Render, choose **New → Blueprint**, connect that private repository, and create the blueprint. Keep the `Free` plan and Singapore region from `render.yaml`.
3. When prompted, enter the Ollama Cloud key as `TEAM_PROVIDER_KEY` in Render's secure field. Never add it to the repository.
4. Wait for the service to deploy. Render generates `TEAM_GATEWAY_TOKEN`; copy its value from the service's Environment page for the portal's restricted bearer token field.
5. Use `https://<your-render-service>.onrender.com/gateway` as the portal gateway URL, then save a new revision and run its connection check.

The controller submission ZIP and gateway deployment ZIP are different files. The portal wants `solution.py` at the ZIP root and explicitly excludes datasets and gateway credentials.

Free Render services sleep after 15 minutes without traffic and may need about a minute to wake. Free capacity can also be suspended if included usage is exceeded. The free plan is suitable for a low-volume attempt but does not promise production availability.
