import { workspaceStore } from "../workspaceStore";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, ArrowUpRight, ArrowRight, CheckCircle2, RefreshCw, ShieldAlert, XCircle, GitCompareArrows, Layers3, Clock3 } from "lucide-react";

const KEY = "nexdeal_history";
const ACTIONS = ["ACCEPT", "COUNTER", "REJECT", "ESCALATE"];
const COLORS = { ACCEPT: "#1F7A63", COUNTER: "#C64F2B", REJECT: "#86827A", ESCALATE: "#A9741A" };
const TINTS = { ACCEPT: "#E2EFE9", COUNTER: "#FAE7E0", REJECT: "#ECE9E2", ESCALATE: "#F8EEDA" };

function loadHistory() {
  try {
    const data = JSON.parse(workspaceStore.getItem(KEY) || "[]");
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

function getAction(item) {
  const label = String(item?.label ?? item?.decision?.label ?? "");
  const action = String(item?.action ?? item?.decision?.action ?? label.split(":")[0]).toUpperCase();
  return ACTIONS.includes(action) ? action : null;
}

function getLabel(item) {
  return String(item?.label ?? item?.decision?.label ?? "");
}

function getId(item, index) {
  return String(item?.thread_id ?? item?.threadId ?? item?.supplier_id ?? item?.supplier ?? `Thread ${index + 1}`);
}

function useAnimatedNumber(target) {
  const [value, setValue] = useState(target);
  useEffect(() => {
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) {
      setValue(target);
      return;
    }
    let frame;
    let start;
    const duration = 550;
    const animate = (time) => {
      if (start === undefined) start = time;
      const progress = Math.min((time - start) / duration, 1);
      setValue(Math.round(target * (1 - Math.pow(1 - progress, 3))));
      if (progress < 1) frame = requestAnimationFrame(animate);
    };
    frame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frame);
  }, [target]);
  return value;
}

function Metric({ title, value, icon: Icon, accent, subtitle }) {
  const animated = useAnimatedNumber(value);
  return (
    <div className="surface surface-hover group relative overflow-hidden p-5">
      <span
        aria-hidden
        className="absolute inset-x-0 top-0 h-[3px] opacity-80"
        style={{ background: `linear-gradient(90deg, ${accent}, ${accent}00)` }}
      />

      <div className="flex items-start justify-between gap-3">
        <span className="pt-0.5 text-[9px] font-bold uppercase leading-4 tracking-[0.16em] text-[#8C877D]">{title}</span>
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl" style={{ backgroundColor: `${accent}14` }}>
          <Icon size={16} style={{ color: accent }} />
        </span>
      </div>

      <div className="display-num mt-6 text-[2.1rem] font-bold leading-none text-[#1F1E1A]">{animated.toLocaleString()}</div>
      <p className="mt-2 text-[11px] leading-4 text-[#938E84]">{subtitle}</p>
    </div>
  );
}

function Dashboard() {
  const [history, setHistory] = useState(loadHistory);
  const [filter, setFilter] = useState("ALL");
  const [updated, setUpdated] = useState(null);

  const refresh = () => {
    setHistory(loadHistory());
    setUpdated(new Date().toLocaleTimeString());
  };

  useEffect(() => {
    const onStorage = (event) => { if (event.key === KEY) refresh(); };
    const onFocus = () => refresh();
    window.addEventListener("storage", onStorage);
    window.addEventListener("focus", onFocus);
    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener("focus", onFocus);
    };
  }, []);

  const records = useMemo(() => history.map((item, index) => ({ ...item, _action: getAction(item), _label: getLabel(item), _id: getId(item, index) })), [history]);
  const counts = useMemo(() => Object.fromEntries(ACTIONS.map((action) => [action, records.filter((item) => item._action === action).length])), [records]);
  const visible = filter === "ALL" ? records : records.filter((item) => item._action === filter);
  const total = records.length;
  const known = ACTIONS.reduce((sum, action) => sum + counts[action], 0);

  return (
    <div className="px-5 py-8 md:px-8 md:py-10">
      <div className="rise flex flex-wrap items-end justify-between gap-5">
        <div>
          <div className="eyebrow flex items-center gap-2">
            <span className="live-dot h-1.5 w-1.5 rounded-full bg-[#C64F2B]" /> Overview / Command Center
          </div>

          <h1 className="display mt-5 text-[2.5rem] font-bold md:text-[3.5rem]">
            Every deal is an{" "}
            <span className="relative inline-block whitespace-nowrap text-[#C64F2B]">
              opportunity.
              <span aria-hidden className="absolute inset-x-1 bottom-1 -z-10 h-2.5 rounded-full bg-[#D9F36A]" />
            </span>
          </h1>

          <p className="mt-4 max-w-xl text-sm leading-7 text-[#7D786F]">
            Monitor real procurement decisions, review policy outcomes, and move from supplier emails to action.
          </p>
        </div>

        <button
          type="button"
          onClick={refresh}
          className="btn btn-ghost px-4 py-2.5 text-xs"
        >
          <RefreshCw size={14} /> Refresh data
        </button>
      </div>

      <div className="mt-9 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <Metric title="Total Threads" value={total} icon={Activity} accent="#1F1E1A" subtitle="Saved evaluations" />
        <Metric title="Accepted" value={counts.ACCEPT} icon={CheckCircle2} accent="#1F7A63" subtitle="Approved offers" />
        <Metric title="Countered" value={counts.COUNTER} icon={GitCompareArrows} accent="#C64F2B" subtitle="Counter-offers" />
        <Metric title="Rejected" value={counts.REJECT} icon={XCircle} accent="#86827A" subtitle="Declined offers" />
        <Metric title="Escalated" value={counts.ESCALATE} icon={ShieldAlert} accent="#A9741A" subtitle="Human review needed" />
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-5">
        <section className="negotiation-feature-card rise rise-1 rounded-[1.75rem] p-7 md:p-9 lg:col-span-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-[#1F1E1A]/70">Your next move</span>
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[#1F1E1A]/90 text-[#D9F36A]">
              <ArrowUpRight size={17} />
            </span>
          </div>

          <h2 className="display mt-8 text-[2.4rem] font-bold md:text-[3.4rem]">
            Negotiate with <br />
            <span className="text-[#1F1E1A]">intelligence.</span>
          </h2>

          <p className="mt-4 max-w-sm text-sm leading-7 text-[#1F1E1A]/70">
            Analyze a supplier email thread and inspect the backend's exact decision and policy trace.
          </p>

          <div className="mt-8 flex flex-wrap gap-2.5">
            

            <Link
              to="/batch"
              className="btn border border-[#1F1E1A]/40 bg-white/20 px-5 py-3 text-[13px] text-[#1F1E1A] backdrop-blur-sm hover:border-[#1F1E1A] hover:bg-white/45"
            >
              <Layers3 size={16} />
              Batch Intelligence
            </Link>
          </div>

          <div className="mt-8 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-[#1F1E1A]/15 pt-5 text-[10px] font-bold uppercase tracking-[0.16em] text-[#1F1E1A]/55">
            <span className="flex items-center gap-1.5"><span className="h-1 w-1 rounded-full bg-[#1F1E1A]/60" /> Policy-first</span>
            <span className="flex items-center gap-1.5"><span className="h-1 w-1 rounded-full bg-[#1F1E1A]/60" /> Backend verified</span>
            <span className="flex items-center gap-1.5"><span className="h-1 w-1 rounded-full bg-[#1F1E1A]/60" /> Auditable trace</span>
          </div>
        </section>

        <section className="surface rise rise-2 p-6 md:p-8 lg:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold">Decision breakdown</h2>
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#C64F2B]/10 text-[#C64F2B]">
              <Activity size={16} />
            </span>
          </div>

          <p className="mt-1.5 text-[11px] text-[#938E84]">Based on saved decision labels</p>

          <div className="mt-7 flex h-2.5 overflow-hidden rounded-full bg-[#1F1E1A]/8" role="img" aria-label="Decision distribution">
            {ACTIONS.map((action) => (
              <div
                key={action}
                className="transition-all duration-500"
                style={{ width: `${total ? (counts[action] / total) * 100 : 0}%`, backgroundColor: COLORS[action] }}
              />
            ))}
            {total > known && <div style={{ width: `${((total - known) / total) * 100}%`, backgroundColor: "#D7D2C6" }} />}
          </div>

          <div className="mt-7 space-y-1">
            {ACTIONS.map((action) => {
              const pct = total ? Math.round((counts[action] / total) * 100) : 0;
              return (
                <div key={action} className="flex items-center justify-between gap-3 rounded-lg px-1 py-2.5">
                  <span className="flex items-center gap-2.5 text-[13px] font-medium text-[#3B392F]">
                    <span className="h-2 w-2 rounded-full" style={{ backgroundColor: COLORS[action] }} />
                    {action}
                  </span>

                  <span className="flex items-center gap-3">
                    <span className="hidden h-1 w-16 overflow-hidden rounded-full bg-[#1F1E1A]/8 sm:block">
                      <span className="block h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: COLORS[action] }} />
                    </span>
                    <span className="display-num text-[13px] font-bold text-[#1F1E1A]">{counts[action]}</span>
                    <span className="w-9 text-right text-[11px] tabular-nums text-[#A6A198]">{pct}%</span>
                  </span>
                </div>
              );
            })}

            {total > known && (
              <p className="pt-2 text-[11px] leading-5 text-[#A6A198]">
                {total - known} record(s) without a recognized decision label.
              </p>
            )}
          </div>
        </section>
      </div>

      <section className="surface rise rise-3 mt-5 overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#EDE8DD] p-6">
          <div>
            <h2 className="text-xl font-bold">Recent negotiations</h2>
            <p className="mt-1 text-[11px] text-[#938E84]">
              {updated ? `Last refreshed at ${updated}` : "Saved negotiation activity"}
            </p>
          </div>

          <Link to="/history" className="group inline-flex items-center gap-2 text-[13px] font-bold text-[#1F1E1A] transition hover:text-[#C64F2B]">
            View Deal Archive
            <ArrowRight size={15} className="transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>

        <div className="flex flex-wrap gap-1.5 px-6 pt-5">
          {["ALL", ...ACTIONS].map((action) => (
            <button
              key={action}
              type="button"
              onClick={() => setFilter(action)}
              aria-pressed={filter === action}
              className={`rounded-full px-3.5 py-1.5 text-[11px] font-bold transition ${
                filter === action
                  ? "bg-[#1F1E1A] text-[#F6F3EB] shadow-[0_10px_20px_-16px_rgba(31,30,26,0.9)]"
                  : "border border-[#E1DBCD] bg-white text-[#7D786F] hover:border-[#C64F2B]/40 hover:text-[#C64F2B]"
              }`}
            >
              {action === "ALL" ? "All decisions" : action}
            </button>
          ))}
        </div>

        {visible.length === 0 ? (
          <div className="flex flex-col items-center px-6 py-14 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-[#F6F3EB] text-[#B7B1A5]">
              <Clock3 size={22} />
            </span>
            <h3 className="mt-4 text-[15px] font-bold">{total ? "No matching decisions" : "No negotiations saved yet"}</h3>
            <p className="mt-1.5 max-w-sm text-[13px] leading-6 text-[#938E84]">
              {total ? "Try another decision filter." : "Processed batch results will appear here automatically."}
            </p>
          </div>
        ) : (
          <div className="px-3 pb-3 pt-4">
            {visible.slice(0, 6).map((item, index) => (
              <div
                key={`${item._id}-${index}`}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl px-3 py-3.5 transition hover:bg-[#FBF8F0]"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#F1EDE3] text-[10px] font-bold text-[#8C877D]">
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  <div className="min-w-0">
                    <p className="truncate text-[13px] font-bold text-[#1F1E1A]">{item._id}</p>
                    <p className="mt-0.5 max-w-lg truncate font-mono text-[11px] text-[#A6A198]">{item._label || "No label provided"}</p>
                  </div>
                </div>

                <span
                  className="rounded-full px-2.5 py-1 text-[10px] font-bold tracking-[0.08em]"
                  style={{
                    backgroundColor: TINTS[item._action] || "#ECE9E2",
                    color: COLORS[item._action] || "#7D786F",
                  }}
                >
                  {item._action || "UNKNOWN"}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default Dashboard;
