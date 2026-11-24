import {
  LayoutGrid,
  
  Clock3,
  Layers3,
  ArrowUpRight,
  Zap,
} from "lucide-react";

import { NavLink } from "react-router-dom";

const menuItems = [
  { name: "Overview", path: "/", icon: LayoutGrid, number: "01" },
  { name: "Deal Archive", path: "/history", icon: Clock3, number: "02" },
  { name: "Batch Intelligence", path: "/batch", icon: Layers3, number: "03" },
];

function Sidebar() {
  return (
    <aside className="sticky top-0 z-40 shrink-0 border-b border-[#E1DBCD] bg-[#F2EEE4]/95 backdrop-blur-xl lg:h-screen lg:w-[278px] lg:border-b-0 lg:border-r">
      <div className="flex h-full flex-col px-4 py-3.5 lg:px-6 lg:py-8">

        {/* Brand */}
        <div className="flex items-center justify-between gap-4 lg:block">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-[11px] bg-[#1F1E1A] shadow-[0_8px_18px_-10px_rgba(31,30,26,0.95)] lg:h-10 lg:w-10 lg:rounded-xl">
                <Zap
                  size={20}
                  fill="#D9F36A"
                  className="text-[#D9F36A]"
                />
              </div>

              <span className="text-[25px] font-bold leading-none tracking-[-0.07em] text-[#1F1E1A] lg:text-[28px]">
                nexdeal<span className="text-[#C64F2B]">.</span>
              </span>
            </div>

            <p className="mt-2.5 hidden text-[9px] font-bold uppercase tracking-[0.28em] text-[#98938A] lg:block">
              Procurement Intelligence
            </p>
          </div>

          <p className="hidden text-[9px] font-bold uppercase tracking-[0.18em] text-[#ABA69C] sm:block lg:hidden">
            Workspace / 001
          </p>
        </div>

        {/* Navigation */}
        <div className="mb-4 mt-8 hidden text-[9px] font-bold uppercase tracking-[0.28em] text-[#ABA69C] lg:block">
          Workspace / 001
        </div>

        <nav className="-mx-1 mt-2.5 flex gap-1.5 overflow-x-auto px-1 pb-1.5 lg:mx-0 lg:mt-0 lg:flex-col lg:gap-1 lg:overflow-visible lg:px-0 lg:pb-0">
          {menuItems.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === "/"}
                className={({ isActive }) =>
                  `group relative flex shrink-0 items-center gap-2.5 rounded-xl px-3 py-2.5 text-[13px] transition-all duration-200 lg:px-4 lg:py-3.5 lg:text-sm ${
                    isActive
                      ? "bg-[#1F1E1A] text-[#F6F3EB] shadow-[0_12px_26px_-16px_rgba(31,30,26,0.95)] lg:translate-x-0"
                      : "text-[#75716A] hover:bg-[#E7E1D4] hover:text-[#1F1E1A]"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    {isActive && (
                      <span
                        aria-hidden
                        className="absolute left-0 top-1/2 hidden h-5 w-[3px] -translate-y-1/2 rounded-full bg-[#D9F36A] lg:block"
                      />
                    )}

                    <span
                      className={`hidden text-[9px] font-bold tabular-nums sm:inline lg:text-[10px] ${
                        isActive
                          ? "text-[#D9F36A]"
                          : "text-[#B4AFA4] group-hover:text-[#1F1E1A]/60"
                      }`}
                    >
                      {item.number}
                    </span>

                    <Icon size={17} className="shrink-0 lg:size-[18px]" />

                    <span className="flex-1 whitespace-nowrap font-semibold">
                      {item.name}
                    </span>

                    {isActive && (
                      <ArrowUpRight
                        size={15}
                        className="hidden shrink-0 text-[#D9F36A] sm:block"
                      />
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Bottom Panel */}
        <div className="mt-auto hidden pt-10 lg:block">

          {/* Clickable Green Card */}
          

          <div className="mt-6 flex items-center justify-between border-t border-[#E1DBCD] pt-4">
            <p className="text-[9px] font-bold tracking-[0.18em] text-[#ABA69C]">
              NEXDEAL © 2026
            </p>
            <span className="h-1.5 w-1.5 rounded-full bg-[#B9B3A5]" />
          </div>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
