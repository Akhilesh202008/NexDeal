import { useMemo, useState } from "react";
import { Upload, FileSpreadsheet, ArrowUpRight, Download, Search, ShieldCheck, LoaderCircle, AlertCircle, X } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const ACTIONS = ["ACCEPT", "COUNTER", "REJECT", "ESCALATE"];
const LABEL_PATTERN = /^(ACCEPT|COUNTER|REJECT|ESCALATE):([A-Z][A-Z0-9_]*):([0-9]*)$/;

const ACTION_STYLE = {
  ACCEPT: "bg-[#E2EFE9] text-[#1F7A63] border-[#BCDECF]",
  COUNTER: "bg-[#FAE7E0] text-[#B44626] border-[#EFC9B9]",
  REJECT: "bg-[#ECE9E2] text-[#6E6A61] border-[#DCD7CC]",
  ESCALATE: "bg-[#F8EEDA] text-[#8F6214] border-[#EBD9B4]",
};

function validLabel(label) {
  const match = LABEL_PATTERN.exec(label);
  return Boolean(match && (match[1] === "COUNTER" ? /^[0-9]+$/.test(match[3]) : match[3] === ""));
}

// Read the two-column submission CSV without adding any new dependencies.
// Labels and IDs are expected to be CSV-safe (no embedded commas or newlines).
function parseResultsCsv(text) {
  const lines = text.replace(/^\uFEFF/, "").trim().split(/\r?\n/);
  if (!lines.length || lines[0].replace(/\s/g, "").toLowerCase() !== "thread_id,label") {
    throw new Error("Backend CSV must have the header: thread_id,label");
  }
  const rows = lines.slice(1).filter(Boolean).map((line, index) => {
    const comma = line.indexOf(",");
    if (comma < 1) throw new Error(`Invalid CSV row ${index + 2}`);
    const thread_id = line.slice(0, comma).trim().replace(/^"|"$/g, "");
    const label = line.slice(comma + 1).trim().replace(/^"|"$/g, "");
    if (!thread_id || !validLabel(label)) throw new Error(`Invalid decision at CSV row ${index + 2}`);
    return { thread_id, label, action: label.split(":")[0] };
  });
  if (!rows.length) throw new Error("Backend returned an empty results CSV.");
  if (new Set(rows.map((r) => r.thread_id)).size !== rows.length) throw new Error("Backend returned duplicate thread IDs.");
  return rows;
}

export default function BatchProcessing() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [rows, setRows] = useState([]);
  const [csv, setCsv] = useState("");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("ALL");

  const counts = useMemo(() => Object.fromEntries(ACTIONS.map((action) => [action, rows.filter((row) => row.action === action).length])), [rows]);
  const filtered = useMemo(() => rows.filter((row) => (filter === "ALL" || row.action === filter) && `${row.thread_id} ${row.label}`.toLowerCase().includes(search.toLowerCase())), [rows, filter, search]);

  function selectFile(event) {
    const next = event.target.files?.[0];
    setError(""); setRows([]); setCsv(""); setSearch(""); setFilter("ALL");
    if (!next) { setFile(null); return; }
    if (!next.name.toLowerCase().endsWith(".csv")) {
      setFile(null); setError("Choose a .csv file."); event.target.value = ""; return;
    }
    if (next.size === 0 || next.size > 20 * 1024 * 1024) {
      setFile(null); setError("CSV must be non-empty and under 20 MB."); event.target.value = ""; return;
    }
    setFile(next);
  }

  async function processFile() {
    if (!file || loading) return;
    setLoading(true); setError(""); setRows([]); setCsv("");
    try {
      const data = new FormData();
      data.append("file", file);
      // Akhilesh must expose POST /batch and return a text/csv file with thread_id,label.
      const response = await fetch(`${API_URL}/batch`, { method: "POST", body: data });
      if (!response.ok) {
        let detail = `Backend returned HTTP ${response.status}`;
        try { const body = await response.json(); if (typeof body.detail === "string") detail = body.detail; } catch { /* Non-JSON error */ }
        throw new Error(detail);
      }
      const resultText = await response.text();
      const parsed = parseResultsCsv(resultText);
      setCsv(resultText); setRows(parsed);
    } catch (err) {
      setError(err instanceof TypeError ? `Cannot reach NexDeal backend at ${API_URL}. Check the backend URL, /batch endpoint and CORS.` : err.message);
    } finally { setLoading(false); }
  }

  function downloadCsv() {
    if (!csv) return;
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const anchor = document.createElement("a");
    anchor.href = url; anchor.download = "nexdeal_predictions.csv";
    document.body.appendChild(anchor); anchor.click(); anchor.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="px-5 py-8 md:px-8 md:py-10">
      <div className="rise">
        <div className="eyebrow flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-[#C64F2B]" />
          Workspace / Batch Intelligence
        </div>

        <h1 className="display mt-5 text-[2.6rem] font-bold md:text-[4rem]">
          Intelligence at <span className="text-[#C64F2B]">scale.</span>
        </h1>

        <p className="mt-5 max-w-2xl text-sm leading-7 text-[#7D786F]">
          Upload negotiation email threads, apply procurement rules, and export exact-match decisions for every thread.
        </p>
      </div>

      <div className="mt-9 grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="surface rise rise-1 p-6 md:p-8">
          <div className="flex items-center justify-between">
            <span className="eyebrow">01 / Dataset Import</span>
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#1F1E1A] text-[#D9F36A]">
              <FileSpreadsheet size={17} />
            </span>
          </div>

          <h2 className="display mt-8 text-[1.9rem] font-bold leading-[1.1] md:text-[2.3rem]">
            Your threads.
            <br />
            One intelligent workflow.
          </h2>

          <p className="mt-3 text-[13px] leading-6 text-[#7D786F]">
            Choose the official supplier email CSV. The backend will evaluate each thread using the procurement playbook.
          </p>

          <label
            htmlFor="batch-file"
            className="group mt-7 flex cursor-pointer flex-col items-center rounded-2xl border-2 border-dashed border-[#D8D2C4] bg-[#FBFAF6] p-9 text-center transition hover:-translate-y-0.5 hover:border-[#C64F2B]/60 hover:bg-white hover:shadow-[0_16px_30px_-24px_rgba(31,30,26,0.7)]"
          >
            <span className="flex h-14 w-14 items-center justify-center rounded-full bg-[#D9F36A]/35 text-[#5E6B24] transition group-hover:bg-[#D9F36A]/60">
              <Upload size={24} />
            </span>

            <span className="mt-4 text-[15px] font-bold">Choose a CSV file</span>
            <span className="mt-1.5 text-[11px] text-[#938E84]">CSV format · maximum 20 MB</span>
            <input id="batch-file" type="file" accept=".csv,text/csv" onChange={selectFile} className="sr-only" />
          </label>

          {file && (
            <div className="mt-4 flex items-center justify-between gap-3 rounded-xl border border-[#E1DBCD] bg-[#FBFAF6] p-3.5 text-[13px]">
              <span className="min-w-0 truncate font-semibold">{file.name} · {(file.size / 1024).toFixed(1)} KB</span>
              <button
                type="button"
                aria-label="Remove file"
                onClick={() => { setFile(null); setRows([]); setCsv(""); }}
                className="shrink-0 rounded-full p-1.5 text-[#8C877D] transition hover:bg-[#EFEAE0] hover:text-[#1F1E1A]"
              >
                <X size={15} />
              </button>
            </div>
          )}

          {error && (
            <div role="alert" className="mt-5 flex items-start gap-2.5 rounded-xl border border-[#E7B8A8] bg-[#FBEEE8] p-4 text-[13px] leading-6 text-[#8E3315]">
              <AlertCircle size={17} className="mt-0.5 shrink-0" />
              {error}
            </div>
          )}

          <button
            type="button"
            disabled={!file || loading}
            onClick={processFile}
            className="btn btn-accent mt-6 w-full px-6 py-4 text-sm disabled:opacity-50"
          >
            {loading ? <><LoaderCircle size={18} className="animate-spin" /> Processing Threads...</> : <>Process All Threads <ArrowUpRight size={17} /></>}
          </button>

          <div className="mt-6 flex items-center gap-3 rounded-2xl bg-[#F1EDE3] p-4">
            <ShieldCheck size={19} className="shrink-0 text-[#7C8A3C]" />
            <p className="text-[11.5px] leading-5 text-[#75716A]">
              Final decisions are generated by the backend, not guessed by the interface. Exact labels are validated before download.
            </p>
          </div>
        </section>

        <section className="dark-panel rise rise-2 flex flex-col p-6 md:p-8">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#D9F36A]">02 / Decision Intelligence</span>
            <ShieldCheck size={20} className="text-[#D9F36A]" />
          </div>

          <div className="mt-10">
            <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-[#D9F36A]">
              {rows.length ? "Batch complete" : "Awaiting processed results"}
            </p>

            <h2 className="display mt-3 text-[2rem] font-bold leading-[1.1]">
              {rows.length ? (
                <span className="text-[#D9F36A]">{rows.length.toLocaleString("en-IN")} decisions.</span>
              ) : (
                <>Every thread.<br />One clear verdict.</>
              )}
            </h2>

            <p className="mt-4 text-[13px] leading-6 text-[#9C988F]">
              {rows.length ? "Review the policy decisions below or export the submission CSV." : "Upload a dataset to generate ACCEPT, COUNTER, REJECT and ESCALATE decisions."}
            </p>
          </div>

          <div className="mt-8 grid grid-cols-2 gap-2.5">
            {ACTIONS.map((action) => (
              <div key={action} className="rounded-xl border border-white/10 bg-white/[0.04] p-3.5">
                <p className="text-[9px] font-bold tracking-[0.14em] text-[#9C988F]">{action}</p>
                <p className="display-num mt-2 text-[1.65rem] font-bold leading-none text-[#D9F36A]">{counts[action] || 0}</p>
              </div>
            ))}
          </div>

          <button
            type="button"
            disabled={!csv}
            onClick={downloadCsv}
            className="btn btn-lime mt-7 w-full px-5 py-3.5 text-[13px] disabled:opacity-40"
          >
            <Download size={16} /> Download Results CSV
          </button>

          <p className="mt-auto pt-7 text-[10px] tracking-wide text-[#79756C]">
            Required submission columns: thread_id,label
          </p>
        </section>
      </div>

      {rows.length > 0 && (
        <section className="surface rise rise-3 mt-5 overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#EDE8DD] p-5 md:px-7 md:py-6">
            <h2 className="text-lg font-bold">Decision Archive</h2>
            <span className="text-[11px] font-semibold text-[#938E84]">{filtered.length} matching threads</span>
          </div>

          <div className="flex flex-wrap gap-2.5 p-5 pb-0 md:px-7">
            <div className="flex min-w-[200px] flex-1 items-center gap-2.5 rounded-xl border border-[#E1DBCD] bg-[#FBFAF6] px-3.5 transition focus-within:border-[#C64F2B] focus-within:bg-white focus-within:shadow-[0_0_0_4px_rgba(198,79,43,0.1)]">
              <Search size={16} className="shrink-0 text-[#A6A198]" />
              <input
                aria-label="Search decisions"
                placeholder="Search thread ID or label"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-transparent py-2.5 text-[13px] outline-none placeholder:text-[#ABA69C]"
              />
            </div>

            <select
              aria-label="Filter action"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="field w-auto cursor-pointer py-2.5 pr-8 text-[13px] font-semibold"
            >
              <option value="ALL">All decisions</option>
              {ACTIONS.map((action) => <option key={action} value={action}>{action}</option>)}
            </select>
          </div>

          <div className="p-5 md:p-7">
            <div className="max-h-[560px] overflow-auto rounded-2xl border border-[#E1DBCD]">
              <table className="nd-table min-w-[560px]">
                <thead>
                  <tr><th>Thread ID</th><th>Decision</th><th>Exact label</th></tr>
                </thead>
                <tbody>
                  {filtered.slice(0, 100).map((row) => (
                    <tr key={row.thread_id} className="nd-row">
                      <td className="font-semibold text-[#1F1E1A]">{row.thread_id}</td>
                      <td>
                        <span className={`inline-block rounded-full border px-2.5 py-1 text-[10px] font-bold tracking-[0.08em] ${ACTION_STYLE[row.action]}`}>{row.action}</span>
                      </td>
                      <td className="font-mono text-[11px] text-[#7D786F]">{row.label}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {filtered.length > 100 && (
              <p className="mt-3 text-[11px] text-[#938E84]">
                Showing first 100 matches. Download CSV for all {rows.length} decisions.
              </p>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
