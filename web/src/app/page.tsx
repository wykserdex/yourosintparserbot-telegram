"use client";

import { useState } from "react";

// ═══════════════════════════════════════════════════════════════════════════
// Yourosint v2 OSINT & Threat Intel Graph Dashboard
// ═══════════════════════════════════════════════════════════════════════════

const ENTITY_TYPES = [
  "Username", "Phone", "Email", "Domain",
  "IP Address", "Bank Card", "BTC Wallet", "ETH Wallet",
  "Telegram Channel", "Evidence Provenance",
] as const;

const ARCH_PILLARS = [
  {
    title: "AccountPool Engine",
    icon: "🛡️",
    desc: "Active lease-based session rotation, dynamic flood-wait backoff, health-check heartbeat & sliding-window RPM tracking.",
    color: "border-cyan-500/30 bg-cyan-950/20",
  },
  {
    title: "Postgres CTE Graph",
    icon: "🕸️",
    desc: "Single-query LATERAL CTEs computing target_ids → all_users → enriched_users with zero N+1 latency & GIN trigram indexing.",
    color: "border-violet-500/30 bg-violet-950/20",
  },
  {
    title: "Blind Index & HMAC",
    icon: "🔒",
    desc: "Zero-knowledge phone & card correlation via HMAC-SHA256 blind indexing with versioned rotation & NFKC canonicalization.",
    color: "border-emerald-500/30 bg-emerald-950/20",
  },
];

function TopologyGraphVisualizer() {
  const nodes = [
    { id: "target", label: "🎯 Target\n@durov", x: 350, y: 150, color: "#ef4444", type: "target" },
    { id: "c1", label: "👤 Contact\n@investigator", x: 180, y: 70, color: "#3b82f6", type: "contact" },
    { id: "c2", label: "👤 Contact\n@developer_tg", x: 520, y: 70, color: "#3b82f6", type: "contact" },
    { id: "c3", label: "👤 Contact\n@crypto_wh", x: 180, y: 240, color: "#3b82f6", type: "contact" },
    { id: "c4", label: "👤 Contact\n@sec_analyst", x: 520, y: 240, color: "#3b82f6", type: "contact" },
    { id: "e1", label: "📧 Email\ncontact@durov.im", x: 50, y: 150, color: "#10b981", type: "entity" },
    { id: "e2", label: "📞 Phone\n+7 999 123-**-**", x: 650, y: 150, color: "#10b981", type: "entity" },
    { id: "e3", label: "🌐 Domain\nton.org", x: 350, y: 20, color: "#06b6d4", type: "entity" },
    { id: "e4", label: "💳 Card\n4276 **** **** 8821", x: 350, y: 280, color: "#f59e0b", type: "entity" },
  ];

  const edges = [
    { from: "target", to: "c1", label: "450 msgs", style: "solid", color: "#6366f1" },
    { from: "target", to: "c2", label: "180 msgs", style: "solid", color: "#6366f1" },
    { from: "target", to: "c3", label: "92 msgs", style: "solid", color: "#6366f1" },
    { from: "target", to: "c4", label: "64 msgs", style: "solid", color: "#6366f1" },
    { from: "c1", to: "e1", label: "extracted", style: "dashed", color: "#10b981" },
    { from: "c2", to: "e2", label: "extracted", style: "dashed", color: "#10b981" },
    { from: "target", to: "e3", label: "mentions", style: "dashed", color: "#06b6d4" },
    { from: "target", to: "e4", label: "blind-idx", style: "dashed", color: "#f59e0b" },
    { from: "c1", to: "c2", label: "3 common chats", style: "dashed", color: "#8b5cf6" },
  ];

  const getNode = (id: string) => nodes.find((n) => n.id === id)!;

  return (
    <div className="flex justify-center w-full">
      <svg viewBox="0 0 720 330" className="w-full max-w-3xl h-auto">
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
            <polygon points="0 0, 8 3, 0 6" fill="#64748b" />
          </marker>
        </defs>

        {/* Edges */}
        {edges.map((e, idx) => {
          const from = getNode(e.from);
          const to = getNode(e.to);
          const isDashed = e.style === "dashed";
          return (
            <g key={`edge-${idx}`}>
              <line
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                stroke={e.color || "#475569"}
                strokeWidth={isDashed ? 1.2 : 2}
                strokeDasharray={isDashed ? "4,4" : "none"}
                opacity={0.75}
              />
              {e.label && (
                <text
                  x={(from.x + to.x) / 2}
                  y={(from.y + to.y) / 2 - 4}
                  fill="#94a3b8"
                  fontSize="8"
                  textAnchor="middle"
                  fontFamily="monospace"
                >
                  {e.label}
                </text>
              )}
            </g>
          );
        })}

        {/* Nodes */}
        {nodes.map((n) => (
          <g key={n.id} className="cursor-pointer">
            <rect
              x={n.x - 45}
              y={n.y - 20}
              width={90}
              height={40}
              rx={8}
              fill={n.color + "18"}
              stroke={n.color}
              strokeWidth={1.5}
            />
            {n.label.split("\n").map((line, li) => (
              <text
                key={li}
                x={n.x}
                y={n.y - 6 + li * 13}
                fill={n.color}
                fontSize={li === 0 ? "10" : "8.5"}
                fontWeight={li === 0 ? "bold" : "normal"}
                textAnchor="middle"
                fontFamily="sans-serif"
              >
                {line}
              </text>
            ))}
          </g>
        ))}
      </svg>
    </div>
  );
}

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<"overview" | "api" | "architecture">("overview");

  return (
    <div className="min-h-screen bg-[#090d16] text-gray-100">
      {/* Top Navigation */}
      <header className="border-b border-gray-800 bg-gray-950/70 sticky top-0 z-50 px-6 py-4 backdrop-blur">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-cyan-500/20">
              🛰️
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-white tracking-tight">Yourosint <span className="text-cyan-400">v2</span></h1>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">Clean Arch</span>
              </div>
              <p className="text-xs text-gray-400">High-Performance Telegram OSINT & Intelligence Graph</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-2.5 py-1 rounded-full text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              ✓ v2.0.0 Online
            </span>
          </div>
        </div>
      </header>

      {/* Main Tabs */}
      <div className="max-w-6xl mx-auto px-6 pt-5">
        <div className="flex gap-2 border-b border-gray-800 pb-0">
          {(["overview", "api", "architecture"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 text-xs font-medium rounded-t transition-colors ${
                activeTab === tab
                  ? "bg-gray-900 text-cyan-400 border-t border-l border-r border-gray-800 border-b-transparent"
                  : "text-gray-400 hover:text-gray-200"
              }`}
            >
              {tab === "overview" ? "📊 Live Graph & Search" : tab === "api" ? "🔌 REST API Reference" : "🏗️ Clean Architecture"}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Contents */}
      <div className="max-w-6xl mx-auto px-6 py-6 space-y-6">
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Graph Visualization */}
            <div className="p-5 rounded-xl bg-gray-900/60 border border-gray-800">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-sm font-bold text-gray-200">Interactive User Interaction & IOC Graph</h2>
                  <p className="text-xs text-gray-400">Computed via single-query PostgreSQL CTE with direct and 2nd-level connections</p>
                </div>
                <div className="flex items-center gap-3 text-xs">
                  <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-rose-500"></span> Target</span>
                  <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-blue-500"></span> Contacts</span>
                  <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-emerald-500"></span> IOCs</span>
                </div>
              </div>
              <TopologyGraphVisualizer />
            </div>

            {/* Pillar Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {ARCH_PILLARS.map((p) => (
                <div key={p.title} className={`p-4 rounded-xl border ${p.color}`}>
                  <div className="text-2xl mb-2">{p.icon}</div>
                  <h3 className="font-semibold text-sm mb-1">{p.title}</h3>
                  <p className="text-xs text-gray-400">{p.desc}</p>
                </div>
              ))}
            </div>

            {/* Entity Types */}
            <div className="p-4 rounded-xl bg-gray-900/60 border border-gray-800">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Supported Intelligence Entities</h3>
              <div className="flex flex-wrap gap-2">
                {ENTITY_TYPES.map((t) => (
                  <span key={t} className="px-2.5 py-1 rounded text-xs bg-gray-950 border border-gray-800 text-gray-300 font-mono">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === "api" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-5 rounded-xl bg-gray-900/60 border border-gray-800 space-y-3">
              <h3 className="text-sm font-semibold text-cyan-400">🔍 Query & Graph Endpoints</h3>
              <div className="space-y-2 text-xs font-mono">
                <div className="p-2.5 rounded bg-gray-950 border border-gray-800">GET /api/v1/search?q=target</div>
                <div className="p-2.5 rounded bg-gray-950 border border-gray-800">GET /api/v1/graph/user/:username</div>
                <div className="p-2.5 rounded bg-gray-950 border border-gray-800">GET /api/v1/objects/:id/relations</div>
                <div className="p-2.5 rounded bg-gray-950 border border-gray-800">GET /api/v1/objects/:id/evidence</div>
                <div className="p-2.5 rounded bg-gray-950 border border-gray-800">GET /api/v1/stats</div>
              </div>
            </div>

            <div className="p-5 rounded-xl bg-gray-900/60 border border-gray-800 space-y-3">
              <h3 className="text-sm font-semibold text-emerald-400">⚡ Ingestion & Control Endpoints</h3>
              <div className="space-y-2 text-xs font-mono">
                <div className="p-2.5 rounded bg-gray-950 border border-gray-800">POST /api/v1/parser/parse</div>
                <div className="p-2.5 rounded bg-gray-950 border border-gray-800">POST /api/v1/autopilot/control</div>
                <div className="p-2.5 rounded bg-gray-950 border border-gray-800">GET /api/v1/accounts/stats</div>
                <div className="p-2.5 rounded bg-gray-950 border border-gray-800">POST /api/v1/accounts/:name/rotate</div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "architecture" && (
          <div className="p-5 rounded-xl bg-gray-900/60 border border-gray-800 space-y-3 text-xs">
            <h3 className="text-sm font-bold text-gray-200">v2 Clean Architecture Specifications</h3>
            <ul className="space-y-2 text-gray-400 list-disc list-inside">
              <li><strong className="text-gray-200">Domain Layer:</strong> Pure business entities (Object, Relation, Evidence, Message, Account) with Pydantic v2 validation.</li>
              <li><strong className="text-gray-200">Application Layer:</strong> Isolated use cases (ParseChat, SearchEntities, BuildGraph, DiscoverChats, ExtractObjects).</li>
              <li><strong className="text-gray-200">Ports & Adapters:</strong> Abstract protocols decoupled from SQLAlchemy, Telethon, and external APIs.</li>
              <li><strong className="text-gray-200">Privacy & Blind Index:</strong> Zero plain-text leaks for sensitive data using keyed HMAC-SHA256.</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
