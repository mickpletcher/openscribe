const assert = require("node:assert/strict");
const {test} = require("node:test");
const {readFileSync} = require("node:fs");
const {join} = require("node:path");
const {createContext, runInContext} = require("node:vm");
const {createHash, webcrypto} = require("node:crypto");

function pane(options = {}) {
  const elements = Object.fromEntries(["status", "token", "preview", "apply", "diff"].map(id => [id, {
    textContent: "", value: "synthetic-session", disabled: true, listeners: {},
    addEventListener(event, handler) { this.listeners[event] = handler; }
  }]));
  const state = {bytes: [1, 2, 3], calls: [], closed: 0, slices: 0};
  const success = value => ({status: "success", value});
  const Office = {
    AsyncResultStatus: {Succeeded: "success"}, FileType: {Compressed: "compressed"}, HostType: {Word: "Word"},
    onReady(done) { done({host: options.host || "Word"}); },
    context: {
      requirements: {isSetSupported: () => options.supported !== false},
      document: {getFileAsync(type, settings, done) {
        assert.equal(type, "compressed");
        assert.equal(settings.sliceSize, 65536);
        done(success({size: options.size || state.bytes.length, sliceCount: 2,
          getSliceAsync(index, callback) {
            state.slices++;
            if (options.sliceError) return callback({status: "failed", error: {message: "Synthetic slice failure"}});
            callback(success({data: index === 0 ? state.bytes.slice(0, 1) : state.bytes.slice(1)}));
          },
          closeAsync(callback) { state.closed++; callback(success()); }
        }));
      }}
    }
  };
  const context = createContext({Office, document: {getElementById: id => elements[id]}, Uint8Array, crypto: webcrypto,
    fetch: async (path, request) => {
      state.calls.push({path, request});
      const payload = path === "/preview" ? {
        blocked: !!options.blocked, preview_id: "synthetic-preview",
        document_hash: createHash("sha256").update(Buffer.from(state.bytes)).digest("hex"),
        units: [{id: "scene-synthetic", status: "import"}], diff: "+ Synthetic revised text"
      } : {applied: 1, backup: "synthetic-checkpoint.zip"};
      return {ok: !options.requestError, json: async () => options.requestError ? {error: "Unauthorized"} : payload};
    }
  });
  runInContext(readFileSync(join(__dirname, "../src/openscribe/word_addin/taskpane.js"), "utf8"), context);
  return {state, elements, click: id => elements[id].listeners.click()};
}

test("preview does not apply; separate apply sends only reviewed identifiers", async () => {
  const app = pane();
  await app.click("preview");
  assert.equal(app.state.calls.length, 1);
  assert.equal(app.state.closed, 1);
  assert.equal(app.state.slices, 2);
  assert.match(app.elements.diff.textContent, /Synthetic revised text/);
  assert.equal(app.elements.apply.disabled, false);
  await app.click("apply");
  assert.equal(app.state.closed, 2);
  const request = app.state.calls[1].request;
  assert.equal(app.state.calls[1].path, "/apply");
  assert.deepEqual(Object.keys(JSON.parse(request.body)).sort(), ["document_hash", "preview_id"]);
  assert.equal(request.redirect, "error");
  assert.equal(request.credentials, "omit");
  assert.equal(request.headers.Authorization, "Bearer synthetic-session");
  assert.equal(app.elements.apply.disabled, true);
  assert.match(app.elements.status.textContent, /Applied 1/);
});

test("blocked preview never enables apply", async () => {
  const app = pane({blocked: true});
  await app.click("preview");
  assert.equal(app.elements.apply.disabled, true);
  assert.match(app.elements.status.textContent, /Import blocked/);
});

test("document changes after preview refuse the apply request", async () => {
  const app = pane();
  await app.click("preview");
  app.state.bytes = [9, 8, 7];
  await app.click("apply");
  assert.equal(app.state.calls.length, 1);
  assert.equal(app.state.closed, 2);
  assert.match(app.elements.status.textContent, /Word changed after preview/);
  assert.equal(app.elements.apply.disabled, true);
});

test("slice failures close the Office file and show an error", async () => {
  const app = pane({sliceError: true});
  await app.click("preview");
  assert.equal(app.state.closed, 1);
  assert.equal(app.state.calls.length, 0);
  assert.match(app.elements.status.textContent, /Synthetic slice failure/);
});

test("oversized files close without reading slices or sending bytes", async () => {
  const app = pane({size: 21 * 1024 * 1024});
  await app.click("preview");
  assert.equal(app.state.closed, 1);
  assert.equal(app.state.slices, 0);
  assert.equal(app.state.calls.length, 0);
  assert.match(app.elements.status.textContent, /20 MiB/);
});

test("unsupported Office hosts stay disabled", () => {
  const app = pane({host: "Excel"});
  assert.equal(app.elements.preview.disabled, true);
  assert.match(app.elements.status.textContent, /does not support/);
});

test("missing compressed-file capability stays disabled", () => {
  const app = pane({supported: false});
  assert.equal(app.elements.preview.disabled, true);
  assert.match(app.elements.status.textContent, /does not support/);
});

test("bridge errors clear approval and remain visible", async () => {
  const app = pane({requestError: true});
  await app.click("preview");
  assert.match(app.elements.status.textContent, /Unauthorized/);
  assert.equal(app.elements.apply.disabled, true);
  assert.equal(app.elements.preview.disabled, false);
});
