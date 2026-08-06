# Frontend / product note — proband-ID validation feature (issue #318)

Context for the frontend + product sessions. The backend hardening for the per-study
proband-ID feature is done (see `SECURITY_REVIEW` summary in the PR / chat). A few items
need a **frontend or product decision** the backend cannot make alone. For each, this note
states what the backend now enforces **regardless of the frontend**, and what the frontend
still must do.

---

## 1. Rendering admin-authored strings safely (stored-XSS surface)

Three study fields are **authored by a study admin** and shipped to the browser:
`proband_external_id_pattern_error_text`, `proband_external_id_example`, and (in the
config UI) the raw `proband_external_id_pattern`.

**Backend enforces regardless of frontend:**
- Each field is length-capped (1024 chars for text/example/pattern) at save time.
- These are returned as plain JSON string values — never as HTML.

**Frontend MUST:**
- Render `error_text` and `example` as **text**, never via `v-html` / `innerHTML` /
  `dangerouslySetInnerHTML`. Vue's `{{ }}` / `:text` bindings escape by default — keep it
  that way. (A grep for `v-html` in the current frontend found no usages on these fields;
  this note is to keep it so.)
- Treat these strings as untrusted: a malicious/compromised study admin could otherwise
  inject markup that runs in the browser of that study's interviewers/viewers.

**Why the backend does not just strip HTML:** `error_text` is human prose and may
legitimately contain characters like `<`, `>`, `&`, quotes (e.g. "ID must be < 8 chars").
Escaping is a render-time concern; stripping at save time would corrupt legitimate text.
If product prefers a stricter contract (e.g. "error text is plain text, no angle
brackets"), say so and the backend can enforce it — but the safe default is: frontend
escapes on render.

---

## 2. `pattern_safe` field on the validation responses (new)

Both validation endpoints now return a `pattern_safe` boolean:
- `POST /api/study/{id}/proband-external-id/validate` → `ProbandIdValidationResult`
- `POST /api/proband-external-id/validate-pattern` → `ProbandIdPatternTestResult`

Semantics:
- `pattern_compiles=false` → the regex does not compile.
- `pattern_compiles=true, pattern_safe=false` → the regex compiles **but is rejected** as
  prone to catastrophic backtracking (nested unbounded quantifiers like `(a+)+`). `valid`
  is `false` and `error_text` explains how to rewrite it.
- `pattern_safe=true` → normal path; `valid` reflects whether the sample matched.

**Frontend SHOULD (config UI):** when `pattern_safe=false`, show the pattern author the
`error_text` ("rewrite using bounded quantifiers such as `{1,20}` …") distinctly from the
ordinary "sample did not match" case, so they understand the pattern was refused, not that
their sample was wrong.

Save (`POST/PATCH /api/study`) already returns **HTTP 422** with the same explanation if an
unsafe pattern is submitted — the UI should surface that message on save failure too.

---

## 0. Which validation endpoint for which user (READ THIS FIRST)

There are **two** validation endpoints. They are not interchangeable — using the wrong one
for the normal-user flow will hit a `403`.

| Endpoint | Job | Caller | Body |
|---|---|---|---|
| `POST /study/{id}/proband-external-id/validate` | Validate a **proband ID** against the study's **already-saved** pattern — the interviewer/proband **pre-submit check** | any study access (**viewer / interviewer / admin**) | `{ "proband_external_id": "..." }` |
| `POST /proband-external-id/validate-pattern` | Test an **unsaved regex** while **authoring** it in study config | **study admins only** | `{ "pattern", "sample", "normalization" }` |

**Rule for the normal-user (interviewer / proband entry) pre-submit check: call
`/validate`, NOT `/validate-pattern`.** The normal user validates *their entered proband
ID*; they never send a regex. The server already holds the study's pattern and applies it
for them, returning `valid` / `normalized_proband_external_id` / `error_text` /
`proband_external_id_example`. This path is open to viewers and up — the admin-only
restriction in §3 does **not** affect it.

`/validate-pattern` is only for the study-config screen where an admin is typing a pattern
and wants a live "does my sample match?" preview before saving. That screen is admin-only,
which is exactly who the endpoint now allows.

---

## 3. Contract change: `/proband-external-id/validate-pattern` is now study-admin-only

Previously this stateless "test this pattern" endpoint accepted **any authenticated user**.
It now requires the caller to be an **instance admin** or a **study admin of at least one
study** (it returns `403` otherwise). Rationale: it runs a *caller-supplied* regex, and the
config UI that uses it is only shown to study admins anyway.

**Frontend impact:** none expected if the "test pattern" field lives in the study-config
screen (already admin-gated). If any non-admin surface calls this endpoint, it will now get
`403` — move that call behind an admin check or drop it.

---

## 4. Input length caps (may affect UX copy)

To bound the input fed to the regex matcher, the backend now caps:
- `proband_external_id` on interview creation and on the `/validate` endpoint: **256 chars**.
- `sample` on `/validate-pattern`: **256 chars**; `pattern`: **1024 chars**.

Real proband IDs are far shorter, so this should never bite a legitimate user, but the
frontend may want a matching `maxlength` on the input and a friendly message rather than a
raw 422.
