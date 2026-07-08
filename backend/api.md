# API Documentation

Base URL: `http://localhost:<port>/api`

Most endpoints require authentication via a bearer token, validated by `verify_token` or `verify_admin_token` (admin-only routes).

---

## Health

### `GET /api/health`
Simple health check.

- **Auth:** None
- **Response:** `{ "message": "Running fine..." }`

---

## Authentication & User Management

### `POST /api/login`
Logs a user in and returns an auth token.

- **Auth:** None
- **Form params:** `username` (str), `password` (str)
- **Behavior:** Validates the user exists and the password is correct, then issues a token via `create_user_token`.
- **Errors:** `400` if missing fields, `404` if user not found, `401` if password incorrect.

### `POST /api/register`
Registers a new standard user.

- **Auth:** None
- **Form params:** `username` (str), `password` (str)
- **Behavior:** Creates a user with role `"usr"`.
- **Errors:** `400` if missing fields.

### `POST /api/register/admin`
Requests creation of an admin account (first step of a two-step approval flow).

- **Auth:** None
- **Form params:** `username` (str), `password` (str)
- **Behavior:** Hashes the password and writes a pending-approval JSON file to `cache/admin/admin-create-{username}.json` with `can_create: false`. A server operator must presumably flip this flag before the account can be finalized.
- **Errors:** `400` if missing fields, `409` if username already exists.

### `POST /api/register/admin/checked`
Finalizes admin account creation once approved.

- **Auth:** None
- **Form params:** `username` (str), `password` (str)
- **Behavior:** Reads the pending admin file, checks `can_create` is `true`, verifies the password against the stored hash, then creates the admin user and deletes the pending file.
- **Errors:** `400` missing fields, `404` no pending admin file, `401` not yet approved (`can_create` false), `400` incorrect password/username on final check.

### `DELETE /api/user/{username}`
Deletes a user.

- **Auth:** Admin token (`verify_admin_token`)
- **Path params:** `username`
- **Permission:** Caller must be an admin, or be deleting their own account.
- **Errors:** `403` if no permission.

### `GET /api/user/{username}`
Fetches a single user's details.

- **Auth:** Admin token
- **Path params:** `username`
- **Errors:** `404` if user not found.

### `GET /api/user`
Lists all users.

- **Auth:** Admin token
- **Response:** `{ "users": [...] }`

### `GET /api/protected`
Example/test endpoint that returns the decoded token payload.

- **Auth:** Standard token
- **Response:** `{ "message": <decoded user info> }`

---

## Processes (Download Jobs)

A "process" appears to represent a download job for a video or playlist.

### `GET /api/process`
Lists the IDs of all processes.

- **Auth:** Standard token
- **Response:** `{ "process": [<process_id>, ...] }`

### `POST /api/process`
Creates a new process (download job).

- **Auth:** Standard token
- **Form params:** `type` (str), `playlist` (str), `title` (str), `process` (str), `private` (bool)
- **Behavior:** Registers a new process owned by the calling user.
- **Response:** `{ "message": "Process created successfully", "process_id": <id> }`

### `GET /api/process/{process_id}`
Fetches details of a specific process.

- **Auth:** Standard token
- **Path params:** `process_id` (UUID string)
- **Behavior:**
  - If the process is private and the caller isn't the owner, returns a redacted object (empty title/playlist, `can_see: false`) without exposing video data.
  - Otherwise returns full process details (`videos`, `title`, `playlist`, `private`, `finished`, `owner`, `type`, `can_see: true`).
- **Errors:** `404` if process not found.

---

## Videos & Playlists

### `GET /api/{token}/videos/{video_id}/thumbnail`
Returns a video's thumbnail image, fetching and caching it from YouTube if not already cached.

- **Auth:** `token` is a path parameter here (not a header) but is **not actually verified** in this handler (see note in Observations below).
- **Path params:** `token`, `video_id`
- **Behavior:**
  1. Checks local cache (`cache/videos/{video_id}/thumbnail.jpg`); serves it if present.
  2. Otherwise, uses `yt-dlp` to fetch video info from YouTube, downloads the thumbnail, saves it to cache, and streams it back.
- **Response:** JPEG image (`FileResponse` or `StreamingResponse`).

### `GET /api/videos`
Lists the IDs of all known videos.

- **Auth:** Standard token
- **Response:** `{ "videos": [<video_id>, ...] }`

### `GET /api/videos/{video_id}/detail`
Returns metadata for a specific video.

- **Auth:** Standard token
- **Path params:** `video_id`
- **Behavior:** Reads cached `detail.json` if present; otherwise fetches video info via `yt-dlp` and caches it.
- **Response:** `{ "id", "title", "thumbnail", "channel" }`

### `GET /api/playlist/{playlist_id}/detail`
Lists video IDs contained in a playlist.

- **Auth:** Standard token
- **Path params:** `playlist_id`
- **Behavior:** Reads cached `detail.json` if present; otherwise fetches playlist info via `yt-dlp` and caches it.
- **Response:** A list of video IDs (`[...]`).

### `GET /api/{token}/videos/{video_id}`
Streams/downloads the actual video file.

- **Auth:** `token` is passed as a path parameter and explicitly verified with `verify_token(token)`.
- **Path params:** `token`, `video_id`
- **Behavior:** Looks up the video record, resolves its file path, and returns it as an MP4 file download.
- **Errors:** `404` if video not found.

---

## Real-time Progress

### `WS /api/ws/progress`
WebSocket endpoint for streaming download progress updates.

- **Auth:** None enforced at connection time.
- **Protocol:**
  - Client connects and sends the text message `"start"` to begin receiving progress updates.
  - Server then concurrently:
    - Streams progress data every 0.25s (`current_process`, `current_video_progress`, `current_process_progress`, `current_process_video_count`, `process_eta`, `current_video_id`), read from shared multiprocessing state.
    - Listens for a `"stop"` command from the client to end the stream.
  - Disconnects are handled via `WebSocketDisconnect`.

### `GET /api/status`
Returns the current shared download-process state.

- **Auth:** Standard token
- **Response:** Shared state dictionary (process/video progress info).

---

## Observations / Potential Issues

These are worth flagging to whoever maintains this API, since they affect security and correctness:

1. **Thumbnail endpoint auth bypass:** `GET /api/{token}/videos/{video_id}/thumbnail` accepts `token` as a path parameter but never calls `verify_token` on it, unlike the sibling video-download endpoint. This means thumbnails can currently be fetched without a valid token.
2. **`app.state["shared"]` syntax:** `app.state` is accessed with dict-style bracket indexing (`app.state["shared"]`) in `start_download_task` and `status_api`, but `app.state` is a `Starlette State` object, which normally requires attribute access (`app.state.shared`). This looks like it would raise a `TypeError` at runtime as written.
3. **`status_api` return value:** `return {app.state["shared"]}` builds a Python `set` containing one item, which is not JSON-serializable in the way likely intended — probably meant to be `{"status": app.state.shared}` or similar.
4. **Password storage in plaintext-adjacent JSON:** The pending admin-approval file stores a bcrypt hash (good), but the whole approval mechanism relies on filesystem flags (`can_create`) that seemingly must be edited manually/externally — there's no endpoint shown that flips this flag.
5. **CORS:** Restricted to `http://localhost:5173`, fine for local dev but will need adjustment for production deployments.