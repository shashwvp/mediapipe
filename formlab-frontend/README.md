# Formlab frontend

A responsive, dependency-free HTML/CSS/JavaScript frontend. Serve `dist/` using any static server, or move the HTML into your Flask templates and serve the CSS and JavaScript from Flask static assets (update the two asset references accordingly).

## Flow

Home → choose Squat, Bicep curl or Shoulder press → upload or record a video → explore demo results → reset or choose another exercise. Camera capture requires HTTPS or localhost, uses no microphone, and stops automatically after 60 seconds. Videos remain local in demo mode. No pose detection or real rep counting is included.

## Connect Flask

Set `ANALYSIS_ENDPOINT` at the top of `dist/app.js` to your API URL, for example `/api/analyze`. This enables the existing async fetch adapter, changes the analysis button and demo notice, and requires a video before analysis. Update the home-page sample description when going live. Cross-origin APIs must allow your frontend origin using CORS; same-origin hosting is simplest. Keep credentials on your server.

Request: `POST` multipart form data with `video` (file) and `exercise` (`squat`, `curl` or `press`). Return JSON:

```json
{
  "reps": 8,
  "feedback": [
    { "status": "good", "title": "Good depth", "detail": "Your feedback here." },
    { "status": "adjust", "title": "Keep your chest lifted", "detail": "Your feedback here." }
  ]
}
```

Responses are rendered as text, not HTML. Non-2xx responses display an error; reset and navigation cancel pending analysis. Add your MediaPipe skeleton rendering and processed-video handling as needed; the current video player previews the original local video. Enforce video limits and validation independently in the backend. Typography loads from Google Fonts with local sans-serif fallbacks.

## Files

- `dist/index.html`: home and session views
- `dist/styles.css`: visual system and responsive layouts
- `dist/app.js`: video capture, routing, demo data and API adapter

The optional `select_exercise` WebMCP tool is feature-detected and uses the same session navigation. A supported WebMCP browser was unavailable for runtime validation.
