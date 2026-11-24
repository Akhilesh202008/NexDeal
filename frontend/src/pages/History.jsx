import { useEffect, useMemo, useState } from "react";
import { History as HistoryIcon, Search, Copy, Check, FileText, X, RefreshCw } from "lucide-react";

const STORAGE_KEY = "nexdeal_history";
const ACTIONS = ["ALL", "ACCEPT", "COUNTER", "REJECT", "ESCALATE"];
const LABEL_PATTERN = /^(ACCEPT|COUNTER|REJECT|ESCALATE):([A-Z][A-Z0-9_]*):([0-9]*)$/;

function readHistory() {
  try {
    const raw = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(raw) ? raw : [];
  } catch {
    return [];
  }
}

function validLabel(value) {
  const match = LABEL_PATTERN.exec(String(value || ""));
  return Boolean(match && (match[1] === "COUNTER" ? /^[0-9]+$/.test(match[3]) : match[3] === ""));
}

function History() {
  const [records, setRecords] = useState(readHistory);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("ALL");
  const [selected, setSelected] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const sync = () => setRecords(readHistory());
    window.addEventListener("storage", sync);
    window.addEventListener("focus", sync);
    return () => {
      window.removeEventListener("storage", sync);
      window.removeEventListener("focus", sync);
    };
  }, []);

  const entries = useMemo(() => records.filter((record) => validLabel(record?.label)), [records]);
  const filtered = useMemo(() => entries.filter((record) => {
    const action = record.label.split(":")[0];
    const matchesAction = filter === "ALL" || action === filter;
    const text = [record.thread_id, record.supplier_id, record.category, record.label, record.email_thread]
      .filter(Boolean).join(" ").toLowerCase();
    return matchesAction && text.includes(query.trim().toLowerCase());
  }), [entries, query, filter]);

  const copyLabel = async (label) => {
    try {
      await navigator.clipboard.writeText(label);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  };

  const actionStyle = {
    ACCEPT: "bg-[#E2EFE9] text-[#1F7A63] border-[#BCDECF]",
    COUNTER: "bg-[#FAE7E0] text-[#B44626] border-[#EFC9B9]",
    REJECT: "bg-[#ECE9E2] text-[#6E6A61] border-[#DCD7CC]",
    ESCALATE: "bg-[#F8EEDA] text-[#8F6214] border-[#EBD9B4]",
  };

  return (
    <div className="px-5 py-8 md:px-8 md:py-10">
      <div className="rise">
        <div className="eyebrow flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-[#C64F2B]" />
          Workspace / Deal Archive
        </div>

        <h1 className="display mt-5 text-[2.6rem] font-bold md:text-[4rem]">
          Every decision.
          <br />
          <span className="text-[#C64F2B]">Accounted for.</span>
        </h1>

        <p className="mt-5 max-w-2xl text-sm leading-7 text-[#7D786F]">
          Explore saved negotiation decisions, review policy reasons and inspect the audit trail for each supplier thread.
        </p>
      </div>

      <div className="surface rise rise-1 mt-9 overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#EDE8DD] p-5 md:px-7 md:py-6">
          <div className="flex flex-wrap items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#1F1E1A] text-[#D9F36A]">
              <HistoryIcon size={17} />
            </span>

            <h2 className="text-lg font-bold">Decision Archive</h2>

            <span className="rounded-full bg-[#1F1E1A] px-2.5 py-1 text-[11px] font-bold text-[#D9F36A]">
              {entries.length}
            </span>
          </div>

          <button
            type="button"
            onClick={() => setRecords(readHistory())}
            className="btn btn-ghost px-3.5 py-2 text-[11px]"
          >
            <RefreshCw size={13} /> Refresh
          </button>
        </div>

        <div className="p-5 md:px-7 md:py-6">
          <div className="flex flex-wrap gap-2.5">
            <div className="flex min-w-[220px] flex-1 items-center gap-2.5 rounded-xl border border-[#E1DBCD] bg-[#FBFAF6] px-3.5 transition focus-within:border-[#C64F2B] focus-within:bg-white focus-within:shadow-[0_0_0_4px_rgba(198,79,43,0.1)]">
              <Search size={16} className="shrink-0 text-[#A6A198]" />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search thread, supplier, category or reason"
                aria-label="Search archived decisions"
                className="w-full bg-transparent py-2.5 text-[13px] outline-none placeholder:text-[#ABA69C]"
              />
            </div>

            <select
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
              aria-label="Filter by decision"
              className="field w-auto cursor-pointer py-2.5 pr-8 text-[13px] font-semibold"
            >
              {ACTIONS.map((action) => <option key={action} value={action}>{action === "ALL" ? "All decisions" : action}</option>)}
            </select>
          </div>

          {filtered.length === 0 ? (
            <div className="mt-6 flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#DDD7C9] bg-[#FBFAF6] px-6 py-16 text-center">
              <span className="flex h-14 w-14 items-center justify-center rounded-full bg-white text-[#B7B1A5] shadow-sm">
                <FileText size={24} />
              </span>

              <h3 className="mt-4 text-lg font-bold">{entries.length ? "No matching decisions" : "No saved negotiations yet"}</h3>

              <p className="mt-2 max-w-md text-[13px] leading-6 text-[#938E84]">
                {entries.length ? "Try another search or decision filter." : "Processed results will appear here after batch processing."}
              </p>
            </div>
          ) : (
            <div className="mt-6 max-h-[620px] overflow-auto rounded-2xl border border-[#E1DBCD]">
              <table className="nd-table min-w-[720px]">
                <thead>
                  <tr>{["Thread", "Supplier", "Category", "Decision", "Reason", "Details"].map((heading) => <th key={heading}>{heading}</th>)}</tr>
                </thead>
                <tbody>
                  {filtered.map((record, index) => {
                    const [action, reason] = record.label.split(":");
                    return (
                      <tr key={`${record.thread_id || record.supplier_id || "thread"}-${index}`} className="nd-row">
                        <td className="font-semibold text-[#1F1E1A]">{record.thread_id || "—"}</td>
                        <td className="text-[#52504A]">{record.supplier_id || "—"}</td>
                        <td className="text-[#52504A]">{record.category || "—"}</td>
                        <td>
                          <span className={`inline-block rounded-full border px-2.5 py-1 text-[10px] font-bold tracking-[0.08em] ${actionStyle[action]}`}>{action}</span>
                        </td>
                        <td className="font-mono text-[11px] text-[#7D786F]">{reason}</td>
                        <td>
                          <button
                            type="button"
                            onClick={() => { setSelected(record); setCopied(false); }}
                            className="font-bold text-[#C64F2B] underline-offset-4 transition hover:underline"
                          >
                            View audit
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#1F1E1A]/55 p-4 backdrop-blur-sm"
          role="presentation"
          onMouseDown={(event) => { if (event.target === event.currentTarget) setSelected(null); }}
        >
          <section
            role="dialog"
            aria-modal="true"
            aria-label="Decision audit details"
            className="dark-panel max-h-[90vh] w-full max-w-2xl overflow-y-auto p-6 md:p-8"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[9px] font-bold uppercase tracking-[0.2em] text-[#D9F36A]">NexDeal / Audit Record</p>
                <h3 className="display mt-3 text-[1.9rem] font-bold">Decision details</h3>
              </div>

              <button
                type="button"
                onClick={() => setSelected(null)}
                aria-label="Close audit"
                className="rounded-full border border-white/20 p-2 text-[#E9E5DA] transition hover:border-[#D9F36A] hover:text-[#D9F36A]"
              >
                <X size={18} />
              </button>
            </div>

            <div className="mt-6 rounded-xl border border-white/10 bg-white/[0.05] p-4">
              <p className="text-[9px] font-bold uppercase tracking-[0.18em] text-[#9C988F]">Exact decision label</p>
              <p className="mt-2 break-all font-mono text-[13px] font-bold text-[#D9F36A]">{selected.label}</p>

              <button
                type="button"
                onClick={() => copyLabel(selected.label)}
                className="btn btn-lime mt-4 px-4 py-2 text-[11px]"
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
                {copied ? "Copied" : "Copy label"}
              </button>
            </div>

            <div className="mt-6 grid gap-x-6 gap-y-1 sm:grid-cols-2">
              {[["Thread ID", selected.thread_id], ["Supplier ID", selected.supplier_id], ["Category", selected.category], ["Thread date", selected.thread_date]].map(([name, value]) => (
                <div key={name} className="border-b border-white/10 py-3">
                  <p className="text-[10px] uppercase tracking-[0.12em] text-[#9C988F]">{name}</p>
                  <p className="mt-1 text-[13px] font-semibold text-[#F1EDE2]">{value || "Not recorded"}</p>
                </div>
              ))}
            </div>

            {selected.email_thread && (
              <div className="mt-6">
                <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.18em] text-[#D9F36A]">Email thread</p>
                <pre className="whitespace-pre-wrap break-words rounded-xl border border-white/10 bg-white/[0.04] p-4 font-sans text-[12.5px] leading-6 text-[#D8D4C8]">{selected.email_thread}</pre>
              </div>
            )}

            {Array.isArray(selected.trace) && selected.trace.length > 0 && (
              <div className="mt-6">
                <p className="mb-3 text-[10px] font-bold uppercase tracking-[0.18em] text-[#D9F36A]">Rule execution trace</p>
                <ol className="space-y-2">
                  {selected.trace.map((step, index) => (
                    <li key={index} className="flex items-start gap-3 rounded-lg border border-white/10 bg-white/[0.03] p-3 text-[12.5px] leading-6 text-[#D8D4C8]">
                      <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#D9F36A]/15 text-[10px] font-bold text-[#D9F36A]">{index + 1}</span>
                      <span>{typeof step === "string" ? step : JSON.stringify(step)}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {selected.draft_email && (
              <div className="mt-6">
                <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.18em] text-[#D9F36A]">Draft response</p>
                <p className="whitespace-pre-wrap rounded-xl border border-white/10 bg-white/[0.04] p-4 text-[12.5px] leading-6 text-[#D8D4C8]">{selected.draft_email}</p>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}

export default History;
