/**
 * Execute the actual pinned TypeScript Pi read tool and the Native AOT read-subset
 * on identical temporary files. No mocked Pi implementation and no paid API.
 */
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { spawnSync } from "node:child_process";
import { writeFileSync as writeJSON } from "node:fs";

const [dotnetBinary, resultPath] = process.argv.slice(2);
if (!dotnetBinary || !resultPath) throw new Error("usage: node compare_pi_read_live.mjs <binary> <results.json>");
const pinned = path.resolve("vendor/pi_ts/packages/coding-agent/dist/core/tools/read.js");
const { createReadToolDefinition } = await import(pathToFileURL(pinned).href);
const dir = mkdtempSync(path.join(tmpdir(), "pi-read-aot-comparison-"));
const cases = [
  ["empty", "", undefined, undefined],
  ["one", "alpha", undefined, undefined],
  ["lines", "alpha\nbeta\ngamma", 2, 1],
  ["limited", "alpha\nbeta\ngamma", 1, 2],
  ["zero-offset", "alpha\nbeta", 0, 1],
  ["negative-offset", "alpha\nbeta", -2, 1],
  ["trailing-newline", "first\nsecond\n", 3, 1],
  ["crlf", "first\r\nsecond\r\n", 2, 1],
  ["unicode", "olá 🧪\nβήτα\n", 1, 2],
  ["limit-zero", "alpha\nbeta", 1, 0],
  ["offset-bounds", "alpha\nbeta", 5, undefined]
];
const results = [];
try {
  const tool = createReadToolDefinition(dir);
  for (const [name, contents, offset, limit] of cases) {
    const filename = path.join(dir, name + ".txt");
    writeFileSync(filename, contents);
    const input = { path: filename };
    if (offset !== undefined) input.offset = offset;
    if (limit !== undefined) input.limit = limit;
    let upstream;
    try {
      const raw = await tool.execute("aot-direct-compare", input);
      upstream = { status: "ok", output: raw.structuredContent ?? raw.content.find(x => x.type === "text")?.text };
    } catch (err) {
      upstream = { status: "error", message: String(err?.message ?? err) };
    }
    const args = ["read-subset", filename];
    if (offset !== undefined) args.push(String(offset));
    if (limit !== undefined) args.push(String(limit));
    const dotnet = spawnSync(dotnetBinary, args, { encoding: null, timeout: 10000 });
    if (dotnet.error) throw dotnet.error;
    const csharp = { status: dotnet.status === 0 ? "ok" : "error",
      output: dotnet.stdout.toString("utf8"), message: dotnet.stderr.toString("utf8").trim() };
    // Successful results must match byte-for-byte. The subset's out-of-bounds
    // errors are compared by their exact text, not wrapper-specific stack traces.
    const pass = upstream.status === csharp.status &&
      (upstream.status === "ok" ? upstream.output === csharp.output :
        upstream.message === csharp.message);
    results.push({ name, status: pass ? "PASS" : "FAIL", upstream, csharp });
  }
} finally {
  rmSync(dir, { recursive: true, force: true });
}
const report = {
  kind: "real_pinned_pi_read_tool_vs_dotnet_aot_bounded_text_subset",
  pinned_pi_sha: "8efd314fa3d3232ce197d8d7a6a5660530b9d83e",
  pass: results.filter(x => x.status === "PASS").length,
  fail: results.filter(x => x.status === "FAIL").length,
  cases: results
};
writeJSON(resultPath, JSON.stringify(report, null, 2) + "\n");
console.log(JSON.stringify({ pass: report.pass, fail: report.fail, failures: results.filter(x => x.status === "FAIL") }, null, 2));
if (report.fail) process.exitCode = 1;
