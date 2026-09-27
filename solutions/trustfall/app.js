
const CANDIDATE_REF = "candidate";
const START_VIEW = "/";
const EXCEPTION_EXAMPLE = "{\"rule_id\":\"<scanner-rule-id>\",\"resource\":\"<terraform-resource-address>\",\"owner\":\"<security-owner>\",\"ticket\":\"<tracking-ticket>\",\"status\":\"accepted\",\"expires\":\"YYYY-MM-DD\",\"justification\":\"<accepted-exception-rationale>\"}";
const ACTIVE_STATUSES = new Set(["queued", "scanning", "reviewing"]);
const TERMINAL_STATUSES = new Set(["passed", "failed", "stale"]);
const state = { repo: null, runs: [], assurances: [], selectedPath: null, draftTree: null, draftHead: null, poll: null };
const pages = {
  "/": ["Project overview", "Candidate state, pipeline evidence, and release controls"],
  "/repository": ["Repository", "Browse and update the mutable release candidate"],
  "/commits": ["Changes", "Commit history for the candidate ref"],
  "/runs": ["Pipelines", "Scanner, ReviewBot, and approval execution history"],
  "/artifacts": ["Artifacts", "SARIF retained from completed scanner stages"],
  "/assurances": ["Repository assurances", "Current public security-control state"],
  "/releases": ["Releases", "Request a protected environment promotion"]
};
function esc(value) { return String(value ?? "").replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch])); }
function byId(id) { return document.getElementById(id); }
function short(value) { return value ? String(value).slice(0, 12) : "unknown"; }
function pathNow() { return pages[location.pathname] ? location.pathname : START_VIEW; }
function setBusy(button, busy, label) { if (!button) return; button.disabled = busy; button.setAttribute("aria-busy", busy ? "true" : "false"); if (label) button.textContent = label; }
function toast(message) { const box = byId("toast"); box.textContent = message; box.hidden = false; clearTimeout(toast.timer); toast.timer = setTimeout(() => { box.hidden = true; }, 4200); }
async function jsonFetch(url, options) { const response = await fetch(url, options); let body = {}; try { body = await response.json(); } catch (_) {} if (!response.ok) throw new Error(body.detail || `${response.status} ${response.statusText}`); return body; }
async function loadBase() {
  const [repo, runs, assurances] = await Promise.all([jsonFetch("/api/repository"), jsonFetch("/api/runs"), jsonFetch("/api/assurances")]);
  state.repo = repo;
  if (!state.draftTree || state.draftHead !== repo.head) {
    state.draftTree = { ...repo.tree };
    state.draftHead = repo.head;
  }
  state.runs = [...runs].sort((a, b) => Number(b.number) - Number(a.number));
  state.assurances = assurances;
  byId("head-pill").textContent = `${repo.candidate_ref} @ ${short(repo.head)}`;
  const sideRef = byId("side-ref"); if (sideRef) sideRef.textContent = repo.candidate_ref;
}
function setChrome() {
  const page = pages[pathNow()] || pages["/"];
  byId("page-title").textContent = page[0];
  byId("page-subtitle").textContent = page[1];
  byId("crumb-page").textContent = page[0];
  document.querySelectorAll("#nav a").forEach(a => a.classList.toggle("active", a.dataset.path === pathNow()));
}
function statusPill(status, forceClass = "") {
  const lower = String(status || "pending").toLowerCase();
  const cls = forceClass || (["verified", "passed", "approved", "issued", "complete", "completed"].includes(lower) ? "ok" : ["failed", "denied"].includes(lower) ? "danger" : ["stale", "cancelled", "not issued", "not_issued"].includes(lower) ? "warn" : "neutral");
  return `<span class="status ${cls}">${esc(String(status || "pending"))}</span>`;
}
function latestRun() { return state.runs[0] || null; }
function reviewRan(run) {
  const review = run?.review || {};
  return Boolean(review.review_path || review.assurance_updated || (Array.isArray(review.events) && review.events.length));
}
function stageState(run, name) {
  if (!run) return { cls: "", label: "waiting" };
  const status = String(run.status || "queued");
  const scan = run.scan || {};
  const reviewed = reviewRan(run);
  if (name === "checkout") return { cls: "done", label: "complete" };
  if (name === "scan") {
    if (scan.available) return { cls: "done", label: "complete" };
    if (status === "scanning") return { cls: "current", label: "running" };
    if (status === "failed") return { cls: "failed", label: "failed" };
    if (status === "stale") return { cls: "cancelled", label: "cancelled" };
    return { cls: "", label: "waiting" };
  }
  if (name === "review") {
    if (reviewed) return { cls: "done", label: "complete" };
    if (status === "reviewing") return { cls: "current", label: "running" };
    if (status === "failed" && scan.available) return { cls: "failed", label: "failed" };
    if (status === "stale") return { cls: "cancelled", label: "not run" };
    return { cls: "", label: "waiting" };
  }
  if (name === "approval") {
    if (run.approval) return { cls: "done", label: "issued" };
    if (status === "passed") return { cls: "", label: "not issued" };
    if (status === "failed") return { cls: "", label: "not issued" };
    if (status === "stale") return { cls: "cancelled", label: "not issued" };
    return { cls: "", label: "waiting" };
  }
  return { cls: "", label: "waiting" };
}
function stageClass(run, name) { return stageState(run, name).cls; }
function expiryText(expiresAt) {
  const seconds = Math.max(0, Number(expiresAt || 0) - Math.floor(Date.now() / 1000));
  return seconds ? `${Math.floor(seconds / 60)}m ${seconds % 60}s` : "expired";
}
function reviewTrace(review) {
  const events = Array.isArray(review?.events) ? review.events : [];
  if (!events.length) return "";
  const labels = {
    scanner_findings_loaded: "Scanner evidence",
    historical_context_loaded: "Historical context",
    security_observation_recorded: "Security observation",
    review_path_completed: "Review path",
    approval_evaluated: "Approval controller"
  };
  const value = event => event.event === "historical_context_loaded" ? `${event.records || 0} record(s) loaded` : String(event.result ?? "complete");
  return `<div class="trace" aria-label="Review trace">${events.map(event => `<div class="trace-row"><span class="trace-key">${esc(labels[event.event] || event.event)}</span><span class="trace-value mono">${esc(value(event))}</span></div>`).join("")}</div>`;
}
function pipelineStages(run, details = false) {
  const scan = run?.scan || {};
  const review = run?.review || {};
  const approval = run?.approval;
  const reviewed = reviewRan(run);
  const scanText = !run ? "No run submitted" : scan.available ? `${scan.findings || 0} finding(s), ${scan.accepted_suppressions || 0} accepted suppression(s)` : run.status === "scanning" ? "Scanner is running" : run.status === "queued" ? "Waiting for scanner" : "No scanner artifact recorded";
  const reviewText = !run ? "ReviewBot not called yet" : !reviewed ? run.status === "reviewing" ? "ReviewBot is evaluating scanner evidence" : run.status === "stale" ? "Candidate changed before review completed" : run.status === "failed" && scan.available ? "Review did not complete" : "Waiting for ReviewBot" : details ? `${review.review_path ? `${String(review.review_path).toUpperCase()} review · ` : ""}${review.historical_assurances_used || 0} historical record(s) loaded` : "Review complete";
  const items = [
    ["checkout", "Checkout", run ? `Candidate ${run.commit}` : "No run submitted"],
    ["scan", "Security Scan", scanText],
    ["review", "AI Review", reviewText],
    ["approval", "Approval", approval ? "Approved" : TERMINAL_STATUSES.has(String(run?.status)) ? "No approval issued for this run" : "Waiting for review decision"]
  ];
  if (approval) items[3][2] = details ? `Deployment candidate: ${approval.deployment_candidate || "revision-bound"} / Revision observed: ${approval.reviewed_revision} / Tier: ${approval.policy_tier} / Expires: ${expiryText(approval.expires_at)}` : "Approved";
  const rows = items.map((item, index) => {
    const current = stageState(run, item[0]);
    const extra = index === 2 && details && review.assurance_updated ? statusPill("memory updated", "warn") : statusPill(current.label, current.cls === "failed" ? "danger" : current.cls === "done" ? "ok" : current.cls === "cancelled" ? "warn" : "neutral");
    return `<div class="pipeline-row ${stageClass(run, item[0])}"><div class="pipeline-index">${index + 1}</div><div class="pipeline-name">${esc(item[1])}</div><div class="pipeline-detail">${esc(item[2])}</div>${extra}</div>`;
  }).join("");
  return `<div class="pipeline">${rows}</div>${details ? reviewTrace(review) : ""}`;
}
function assurancesTable() {
  if (!state.assurances.length) return `<div class="empty">No public assurances returned.</div>`;
  return `<div class="table assurance-table" role="table" aria-label="Repository assurances"><div class="table-row head"><span>Control</span><span>State</span><span>Scope</span><span>Evidence / source</span><span>Origin</span></div>${state.assurances.map(a => `<div class="table-row"><span class="mono">${esc(a.control)}</span><span>${statusPill(a.state || a.status)}</span><span>${esc(a.scope)}</span><span>${esc(a.evidence_class)} · ${esc(a.source)}</span><span>${esc(a.originating_run)} · ${esc(a.artifact)}</span></div>`).join("")}</div>`;
}
function ensurePolling() {
  const active = state.runs.find(run => ACTIVE_STATUSES.has(String(run.status)));
  if (!active) { if (state.poll) clearInterval(state.poll); state.poll = null; return; }
  if (state.poll) return;
  state.poll = setInterval(async () => {
    try {
      await loadBase();
      render();
      if (!state.runs.some(run => ACTIVE_STATUSES.has(String(run.status)))) { clearInterval(state.poll); state.poll = null; }
    } catch (_) {}
  }, 1800);
}
async function startPipeline(button) {
  const original = button.textContent;
  try {
    setBusy(button, true, "Starting...");
    const result = await jsonFetch("/api/runs", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ commit: state.repo.head }) });
    toast(`Pipeline ${result.status} for ${short(state.repo.head)}`);
    await loadBase(); render(); ensurePolling();
  } catch (error) { toast(error.message); }
  finally { setBusy(button, false, original); }
}
function renderOverview(root) {
  const run = latestRun();
  const verified = state.assurances.filter(item => String(item.status).toUpperCase() === "VERIFIED").length;
  root.innerHTML = `
    <section class="facts" aria-label="Project status">
      <div class="fact"><span>Candidate ref</span><strong class="mono">${esc(state.repo.candidate_ref)}</strong></div>
      <div class="fact"><span>Head commit</span><strong class="mono">${esc(short(state.repo.head))}</strong></div>
      <div class="fact"><span>Latest pipeline</span><strong>${run ? `#${esc(run.number)} · ${esc(String(run.status).toUpperCase())}` : "Not run"}</strong></div>
      <div class="fact"><span>Verified controls</span><strong>${verified} / ${state.assurances.length}</strong></div>
    </section>
    <div class="grid">
      <section class="panel span-8"><div class="panel-head"><h2>Latest Pipeline${run ? ` · #${esc(run.number)}` : ""}</h2><div class="toolbar"><button id="run-now">Run pipeline</button><a href="/runs">All pipelines</a></div></div><div class="panel-body">${pipelineStages(run, false)}</div></section>
      <section class="panel span-4"><div class="panel-head"><h2>Release candidate</h2></div><div class="panel-body"><p class="muted" style="margin-top:0">Current head</p><p style="margin:0 0 9px"><strong class="mono">${esc(short(state.repo.head))}</strong></p><p class="muted"><span class="mono">${esc(state.repo.candidate_ref)}</span> advances when new repository commits are created.</p><a href="/repository">Open repository →</a></div></section>
      <section class="panel span-7"><div class="panel-head"><h2>Security assurances</h2><a href="/assurances">View controls</a></div><div class="panel-body">${assurancesTable()}</div></section>
      <section class="panel span-5"><div class="panel-head"><h2>Production deployment</h2>${statusPill("protected", "neutral")}</div><div class="panel-body"><p class="muted" style="margin-top:0">Promotion requires an active approval accepted by the Release Agent.</p><div class="toolbar" style="margin-bottom:12px"><button id="release-prod" class="danger">Deploy to production</button><a href="/releases">Release desk</a></div><pre class="log" id="release-log">No deployment request in this session.</pre></div></section>
    </div>`;
  byId("run-now").onclick = event => startPipeline(event.currentTarget);
  byId("release-prod").onclick = event => requestRelease(event.currentTarget, "production", byId("release-log"));
}
function fileButton(path) { return `<button type="button" class="mono ${path === state.selectedPath ? "active" : ""}" data-file="${esc(path)}">${esc(path)}</button>`; }
function selectFile(path) { state.selectedPath = path; renderRepository(byId("content")); }
function renderRepository(root) {
  const tree = state.draftTree || state.repo.tree;
  const files = Object.keys(tree).sort();
  state.selectedPath = state.selectedPath && tree[state.selectedPath] !== undefined ? state.selectedPath : files[0];
  root.innerHTML = `<section class="panel"><div class="panel-head"><div><h2>Repository Workbench</h2><div class="muted mono" style="margin-top:2px;font-size:11px">${esc(state.repo.candidate_ref)} @ ${esc(short(state.repo.head))}</div></div><div class="toolbar"><button id="commit-update">Commit Update</button><button class="secondary" id="run-head">Run Pipeline</button></div></div><div class="workspace"><div class="file-list" aria-label="Files">${files.map(fileButton).join("")}</div><div class="editor"><label for="source-editor">Editing <span class="mono">${esc(state.selectedPath)}</span></label><textarea id="source-editor" spellcheck="false"></textarea><p class="muted">Edits are kept while you switch files and committed together. Commit creation uses optimistic head matching; a stale editor cannot silently advance the candidate.</p></div></div></section>`;
  const editor = byId("source-editor"); editor.value = tree[state.selectedPath] || ""; editor.oninput = () => { state.draftTree[state.selectedPath] = editor.value; };
  document.querySelectorAll("[data-file]").forEach(button => { button.onclick = () => selectFile(button.dataset.file); });
  byId("commit-update").onclick = event => commitUpdate(event.currentTarget);
  byId("run-head").onclick = event => startPipeline(event.currentTarget);
}
async function commitUpdate(button) {
  const original = button.textContent;
  try {
    setBusy(button, true, "Committing...");
    const tree = { ...state.draftTree };
    const result = await jsonFetch("/api/commits", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ expected_head: state.repo.head, tree }) });
    toast(`Committed ${short(result.commit)}`);
    await loadBase(); renderRepository(byId("content"));
  } catch (error) { toast(error.message); }
  finally { setBusy(button, false, original); }
}
function renderCommits(root) {
  root.innerHTML = `<section class="panel"><div class="panel-head"><h2>Change History</h2><button class="secondary" id="refresh-commits">Refresh</button></div><div class="panel-body" id="commit-list"><div class="empty">Loading commits...</div></div></section>`;
  byId("refresh-commits").onclick = () => renderPage();
  jsonFetch("/api/commits").then(commits => {
    byId("commit-list").innerHTML = commits.length ? `<div class="table"><div class="table-row head"><span>Commit</span><span>Parent</span><span>Created</span></div>${commits.map(c => `<div class="table-row"><span class="mono">${esc(short(c.id))}</span><span class="mono muted">${esc(short(c.parent))}</span><span>${new Date(c.created_at * 1000).toLocaleString()}</span></div>`).join("")}</div>` : `<div class="empty">No commits recorded.</div>`;
  }).catch(error => { byId("commit-list").textContent = error.message; });
}
function runCard(run) {
  return `<article class="panel"><div class="panel-head"><div class="run-header-meta"><h3>Run #${esc(run.number)}</h3>${statusPill(run.status)}<span class="mono muted">${esc(run.commit)}</span></div>${run.scan.available ? `<a href="/api/runs/${encodeURIComponent(run.id)}/artifacts/results.sarif">results.sarif</a>` : ""}</div><div class="panel-body">${pipelineStages(run, true)}</div></article>`;
}
function renderRuns(root) {
  root.innerHTML = `<section class="panel"><div class="panel-head"><div><h2>Pipeline Control</h2><div class="muted" style="font-size:11px;margin-top:2px">Only one pipeline can be active for this instance.</div></div><button id="start-run">Run Pipeline</button></div><div class="panel-body"><div class="run-list">${state.runs.map(runCard).join("") || `<div class="empty">No pipeline runs yet.</div>`}</div></div></section>`;
  byId("start-run").onclick = event => startPipeline(event.currentTarget);
}
function renderArtifacts(root) {
  const runs = state.runs.filter(run => run.scan && run.scan.available);
  root.innerHTML = `<div class="artifact-layout"><section class="panel"><div class="panel-head"><h2>Scanner Artifacts</h2><span class="muted">${runs.length} retained</span></div><div class="panel-body"><div class="artifact-list">${runs.map(run => `<button class="secondary artifact-button" data-run="${esc(run.id)}">Run #${esc(run.number)} · results.sarif</button>`).join("") || `<div class="empty">No scanner artifacts yet.</div>`}</div></div></section><section class="panel"><div class="panel-head"><h2>Artifact Preview</h2><span class="muted mono">SARIF 2.1.0</span></div><div class="panel-body"><pre class="log artifact-preview" id="artifact-preview">Select an artifact to inspect scanner output.</pre></div></section></div>`;
  document.querySelectorAll(".artifact-button").forEach(button => { button.onclick = async () => { try { const data = await jsonFetch(`/api/runs/${encodeURIComponent(button.dataset.run)}/artifacts/results.sarif`); byId("artifact-preview").textContent = JSON.stringify(data, null, 2); } catch (error) { byId("artifact-preview").textContent = error.message; } }; });
}
function renderAssurances(root) {
  root.innerHTML = `<div class="grid"><section class="panel span-8"><div class="panel-head"><div><h2>Repository Assurances</h2><div class="muted" style="font-size:11px;margin-top:2px">Public control state persisted by ReviewBot</div></div><button class="secondary" id="refresh-assurances">Refresh</button></div><div class="panel-body">${assurancesTable()}</div></section><section class="span-4 callout"><div class="callout-head">Release integrity</div><div class="callout-body"><p class="muted">Evidence relates to release artifact provenance, artifact-storage auditability, and promotion traceability.</p><p class="muted">Accepted scanner exceptions reference a scanner finding and its Terraform resource.</p><pre class="log">${esc(EXCEPTION_EXAMPLE)}</pre></div></section></div>`;
  byId("refresh-assurances").onclick = () => renderPage();
}
function renderReleases(root) {
  root.innerHTML = `<section class="panel"><div class="panel-head"><div><h2>Release Desk</h2><div class="muted" style="font-size:11px;margin-top:2px">Protected environment promotion</div></div>${statusPill("guarded", "neutral")}</div><div class="panel-body"><div class="release-flow"><div class="release-node"><span>Candidate</span><strong class="mono">${esc(short(state.repo.head))}</strong></div><div class="release-arrow">→</div><div class="release-node"><span>Approval gate</span><strong>Release Agent</strong></div><div class="release-arrow">→</div><div class="release-node"><span>Environment</span><strong id="flow-target">staging</strong></div></div><div class="release-box"><div class="release-form"><label for="release-target">Target environment<select id="release-target"><option value="staging">staging</option><option value="production">production</option></select></label><p class="muted">Candidate ref <span class="mono">${esc(CANDIDATE_REF)}</span></p><p class="muted">Current head <span class="mono">${esc(short(state.repo.head))}</span></p><div class="toolbar"><button id="request-release">Request Release</button></div></div><pre class="log" id="release-output">Release Agent has not been called from this desk.</pre></div></div></section>`;
  const target = byId("release-target");
  target.onchange = () => { byId("flow-target").textContent = target.value; };
  byId("request-release").onclick = event => requestRelease(event.currentTarget, target.value, byId("release-output"));
}
async function requestRelease(button, target, output) {
  const original = button.textContent;
  try {
    setBusy(button, true, "Requesting...");
    const result = await jsonFetch("/api/releases", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ candidate_ref: CANDIDATE_REF, action: "promote", target }) });
    output.textContent = result.lease || "release accepted";
  } catch (error) { output.textContent = `Denied: ${error.message}`; }
  finally { setBusy(button, false, original); }
}
function refreshExpiryLabels() {
  document.querySelectorAll("[data-expiry]").forEach(node => { node.textContent = expiryText(node.dataset.expiry); });
}
function render() {
  const root = byId("content");
  const path = pathNow();
  setChrome();
  if (path === "/repository") renderRepository(root);
  else if (path === "/commits") renderCommits(root);
  else if (path === "/runs") renderRuns(root);
  else if (path === "/artifacts") renderArtifacts(root);
  else if (path === "/assurances") renderAssurances(root);
  else if (path === "/releases") renderReleases(root);
  else renderOverview(root);
}
async function renderPage() {
  try { await loadBase(); render(); ensurePolling(); }
  catch (error) { setChrome(); byId("content").innerHTML = `<section class="panel"><div class="panel-body"><div class="empty">${esc(error.message)}</div></div></section>`; }
}
setInterval(refreshExpiryLabels, 1000);
renderPage();
