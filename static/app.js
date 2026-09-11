'use strict';
// Set this URL to your Flask endpoint to enable real analysis. See README.md.
const ANALYSIS_ENDPOINT = '/process';
const exercises = {
  squat: { name: 'Squat', tip: 'Place your camera at hip height, side-on, with your whole body in frame.', good: 'Good depth', detail: 'Sample cue: you reached a consistent depth throughout the set.', adjust: 'Keep your chest lifted', cue: 'Sample cue: focus on keeping your torso steady as you stand.' },
  curl: { name: 'Bicep curl', tip: 'Face the camera with your arms and weights fully visible. Leave space above your head.', good: 'Controlled tempo', detail: 'Sample cue: your movement stayed smooth through each rep.', adjust: 'Keep elbows steady', cue: 'Sample cue: keep your elbows close to your sides as you lift.' },
  press: { name: 'Shoulder press', tip: 'Face the camera and make sure your hands remain visible at full overhead extension.', good: 'Full extension', detail: 'Sample cue: you reached a consistent overhead position.', adjust: 'Keep your torso steady', cue: 'Sample cue: avoid leaning back as you press overhead.' }
};
const $ = id => document.getElementById(id);
let selected = 'squat', videoFile = null, videoUrl = null, stream = null, recorder = null, chunks = [], recordingTimer = null, request = null, generation = 0;
$('year').textContent = new Date().getFullYear();
function message(text) { $('message').textContent = text; }
function clearResults() { $('reps').textContent = '—'; $('rep-caption').textContent = 'Your next set starts here.'; $('feedback-content').replaceChildren(); const p = document.createElement('p'); p.className = 'empty-feedback'; p.textContent = 'Your feedback will appear here. Explore the demo to see an example.'; $('feedback-content').append(p); }
function stopCamera(discard = false) { clearTimeout(recordingTimer); if (recorder && recorder.state !== 'inactive') { if (discard) recorder.onstop = null; recorder.stop(); } if (stream) stream.getTracks().forEach(track => track.stop()); stream = null; $('stop').hidden = true; $('video').srcObject = null; }
function reset() { $('video-stream').hidden = true; $('video-stream').removeAttribute('src'); generation++; request?.abort(); request = null; stopCamera(true); $('video').pause(); $('video').removeAttribute('src'); $('video').load(); if (videoUrl) URL.revokeObjectURL(videoUrl); videoUrl = null; videoFile = null; $('file').value = ''; $('video').hidden = true; $('upload-prompt').hidden = false; $('video-state').textContent = 'Ready when you are'; $('analyze').disabled = false; $('analyze').textContent = ANALYSIS_ENDPOINT ? 'Analyze video ↗' : 'Explore demo results ↗'; message(''); clearResults(); }
function route() { const key = location.hash.replace('#analysis/', ''); const analysis = location.hash.startsWith('#analysis/') && Object.hasOwn(exercises, key); if (!analysis || key !== selected) reset(); $('home-view').hidden = analysis; $('analysis-view').hidden = !analysis; if (analysis) { selected = key; $('exercise-title').textContent = exercises[key].name + ' analysis'; $('setup-tip').textContent = exercises[key].tip; window.scrollTo(0, 0); } else if (location.hash) { requestAnimationFrame(() => document.querySelector(['#exercises','#how-it-works','#home'].includes(location.hash) ? location.hash === '#home' ? '#home-view' : location.hash : '#home-view')?.scrollIntoView()); } }
document.querySelectorAll('[data-exercise]').forEach(button => button.addEventListener('click', () => { location.hash = 'analysis/' + button.dataset.exercise; }));
window.addEventListener('hashchange', route); route();
function loadVideo(file) { if (!file || !file.type.startsWith('video/')) { message('Please choose a video file (MP4, MOV or WebM).'); return; } if (file.size > 100 * 1024 * 1024) { message('This video is too large. Choose a video under 100 MB.'); return; } reset(); videoFile = file; videoUrl = URL.createObjectURL(file); $('video').src = videoUrl; $('video').muted = false; $('video').hidden = false; $('upload-prompt').hidden = true; $('video-state').textContent = file.name; }
$('video').addEventListener('error', () => message('This video could not be played. Try an MP4 or WebM video supported by your browser.'));
$('upload').onclick = () => $('file').click(); $('file').onchange = event => loadVideo(event.target.files[0]);
['dragenter','dragover'].forEach(name => $('drop-zone').addEventListener(name, event => { event.preventDefault(); $('drop-zone').classList.add('dragging'); }));
['dragleave','drop'].forEach(name => $('drop-zone').addEventListener(name, event => { event.preventDefault(); $('drop-zone').classList.remove('dragging'); if (name === 'drop') loadVideo(event.dataTransfer.files[0]); }));
$('camera').onclick = async () => { if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) { message('Camera recording is unavailable here. Upload a video instead, or open this site using HTTPS.'); return; } const current = generation; $('camera').disabled = true; message(''); try { const acquired = await navigator.mediaDevices.getUserMedia({ video: true, audio: false }); if (current !== generation) { acquired.getTracks().forEach(track => track.stop()); return; } stream = acquired; chunks = []; $('video').hidden = false; $('upload-prompt').hidden = true; $('video').muted = true; $('video').srcObject = stream; await $('video').play(); recorder = new MediaRecorder(stream); const activeRecorder = recorder; recorder.ondataavailable = event => { if (event.data.size) chunks.push(event.data); }; recorder.onstop = () => { const file = new File(chunks, 'recorded-set.' + (activeRecorder.mimeType.includes('mp4') ? 'mp4' : 'webm'), { type: activeRecorder.mimeType || 'video/webm' }); stopCamera(); loadVideo(file); }; recorder.start(); $('video-state').textContent = '● Recording · up to 60 seconds'; $('stop').hidden = false; $('analyze').disabled = true; recordingTimer = setTimeout(() => stopCamera(), 60000); } catch (error) { stopCamera(true); $('video').hidden = true; $('upload-prompt').hidden = false; message('Could not access your camera. Check camera permissions, then try again or upload a video.'); } finally { $('camera').disabled = false; } };
$('stop').onclick = () => stopCamera(); $('reset').onclick = reset;
function renderResults(result) { if (!Number.isInteger(result.reps) || result.reps < 0 || !Array.isArray(result.feedback) || result.feedback.some(item => !item || !['good','adjust'].includes(item.status) || typeof item.title !== 'string' || typeof item.detail !== 'string')) throw new Error('The analysis response was not in the expected format.'); $('reps').textContent = result.reps; $('rep-caption').textContent = ANALYSIS_ENDPOINT ? 'Set complete. Ready for your next one?' : 'Sample results · not your video'; $('feedback-content').replaceChildren(); result.feedback.forEach(item => { const row = document.createElement('div'); row.className = 'feedback-item'; const icon = document.createElement('span'); icon.className = item.status === 'good' ? 'status-good' : 'status-adjust'; icon.textContent = item.status === 'good' ? '✓' : '△'; const text = document.createElement('div'); const title = document.createElement('strong'); title.textContent = item.title; const detail = document.createElement('p'); detail.textContent = item.detail; text.append(title, detail); row.append(icon, text); $('feedback-content').append(row); }); }
$('video-stream').onerror = () => message('The processed stream could not load. Check the Flask terminal for the error.');
$('analyze').onclick = async () => {
  if (!videoFile) { message('Choose or record a video first.'); return; }
  message('');
  const current = generation;
  $('analyze').disabled = true;
  $('analyze').textContent = 'Uploading…';
  $('video-stream').hidden = true;
  $('video-stream').removeAttribute('src');
  request = new AbortController();
  try {
    const form = new FormData();
    form.append('video', videoFile);
    form.append('exercise', selected);
    const response = await fetch(ANALYSIS_ENDPOINT, {
      method: 'POST', body: form, signal: request.signal
    });
    const data = response.headers.get('content-type')?.includes('application/json')
      ? await response.json() : null;
    if (!response.ok) throw new Error(data?.error || `Upload failed (${response.status}). Check the Flask terminal.`);
    if (!data?.stream_url) throw new Error('The /process route must return JSON with stream_url. Restart Flask after updating your exercise server.');
    if (current !== generation) return;
    $('video').pause();
    $('video').hidden = true;
    $('upload-prompt').hidden = true;
    $('video-stream').src = data.stream_url + (data.stream_url.includes('?') ? '&' : '?') + 't=' + Date.now();
    $('video-stream').hidden = false;
    $('video-state').textContent = 'Processed video';
    $('rep-caption').textContent = 'Rep count is shown on the video.';
    $('feedback-content').textContent = 'Exercise feedback and pose landmarks appear on the processed video.';
  } catch (error) {
    if (error.name !== 'AbortError' && current === generation) message(error.message);
  } finally {
    if (current === generation) {
      $('analyze').disabled = false;
      $('analyze').textContent = 'Analyze video ↗';
    }
  }
};
if (ANALYSIS_ENDPOINT) { document.querySelector('.demo-badge').textContent = 'VIDEO ANALYSIS'; document.querySelector('.demo-note').textContent = 'When you choose Analyze video, your video is sent for analysis.'; }
window.addEventListener('pagehide', () => { request?.abort(); $('video-stream').removeAttribute('src'); stopCamera(true); if (videoUrl) URL.revokeObjectURL(videoUrl); });
if (document.modelContext?.registerTool) { try { Promise.resolve(document.modelContext.registerTool({ name: 'select_exercise', description: 'Open the session workspace for an exercise. Does not record or analyze video.', inputSchema: { type: 'object', properties: { exercise: { type: 'string', enum: ['squat','curl','press'] } }, required: ['exercise'], additionalProperties: false }, annotations: { readOnlyHint: false, untrustedContentHint: false }, execute: input => { if (!input || !Object.hasOwn(exercises, input.exercise)) throw new Error('Unknown exercise'); location.hash = 'analysis/' + input.exercise; route(); return { exercise: input.exercise, status: 'workspace_open' }; } })).catch(() => {}); } catch {} }
