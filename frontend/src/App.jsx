import "./App.css";
import { Routes, Route } from "react-router-dom";
import { ArrowUpRight, Sparkles } from "lucide-react";

import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import Analyzer from "./pages/Analyzer";
import History from "./pages/History";
import BatchProcessing from "./pages/BatchProcessing";

function App() {
  return (
    <div className="flex min-h-screen flex-col bg-[#F6F3EB] text-[#1F1E1A] lg:flex-row">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Top Navigation */}
        <header className="sticky top-0 z-30 border-b border-[#E1DBCD] bg-[#F6F3EB]/85 backdrop-blur-xl">
          <div className="mx-auto flex w-full max-w-[1400px] flex-wrap items-center justify-between gap-4 px-5 py-4 md:px-8">
            <div className="min-w-0">
              <p className="eyebrow mb-1.5 flex items-center gap-1.5">
                NexDeal <span className="text-[#C4BEAE]">/</span> Intelligence Workspace
              </p>

              <h1 className="display truncate text-[1.35rem] font-bold">
                The future of better deals<span className="text-[#C64F2B]">.</span>
              </h1>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="flex items-center gap-2 rounded-full border border-[#E1DBCD] bg-white/70 px-3.5 py-2">
                <span className="live-dot h-1.5 w-1.5 rounded-full bg-[#7FA62F]" />
                <span className="text-[11px] font-bold tracking-wide text-[#3B392F]">
                  AI Workspace
                </span>
              </div>

              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#1F1E1A] text-[#D9F36A] shadow-[0_10px_22px_-14px_rgba(31,30,26,0.9)]">
                <Sparkles size={18} />
              </div>
            </div>
          </div>
        </header>

        {/* Editorial Announcement Strip */}
        <div className="border-b border-[#1F1E1A]/10 bg-[#1F1E1A] text-[#F6F3EB]">
          <div className="mx-auto flex w-full max-w-[1400px] flex-wrap items-center justify-between gap-3 px-5 py-2.5 md:px-8">
            <div className="flex items-center gap-3">
              <span className="rounded-full bg-[#D9F36A] px-2.5 py-1 text-[9px] font-bold uppercase tracking-[0.18em] text-[#1F1E1A]">
                NexDeal AI
              </span>

              <p className="text-[11px] tracking-[0.06em] text-[#D8D4C8]">
                Negotiation intelligence, reimagined.
              </p>
            </div>

            <ArrowUpRight size={15} className="text-[#D9F36A]" />
          </div>
        </div>

        {/* Page Content */}
        <main className="mx-auto w-full max-w-[1400px] flex-1">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analyzer" element={<Analyzer />} />
            <Route path="/history" element={<History />} />
            <Route path="/batch" element={<BatchProcessing />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default App;
