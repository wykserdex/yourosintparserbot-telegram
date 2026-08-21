"""FastAPI Application Entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from yourosint.bootstrap import container

from .routers.enrichment import router as enrichment_router
from .routers.graph import router as graph_router
from .routers.ingestion import router as ingestion_router
from .routers.intelligence import router as intelligence_router
from .routers.stats import router as stats_router

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("yourosint")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Initializing Yourosint v2 with Bounded Contexts...")
    try:
        await container.db.create_all_tables()
    except Exception as e:
        logger.warning(f"Note on table creation: {e}")

    await container.account_pool.register_account(
        name="primary_worker",
        client=None,
        phone="+79991234567",
        username="yourosint_worker",
    )

    yield

    logger.info("Shutting down Yourosint v2...")
    await container.account_pool.close_all()
    await container.db.close()


app = FastAPI(
    title="Yourosint OSINT Platform v2 (Bounded Contexts)",
    description="Hexagonal Architecture OSINT Platform for Telegram",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Context Routers
app.include_router(stats_router, prefix="/api/v1")
app.include_router(ingestion_router, prefix="/api/v1")
app.include_router(intelligence_router, prefix="/api/v1")
app.include_router(graph_router, prefix="/api/v1")
app.include_router(enrichment_router, prefix="/api/v1")


@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Serves the rich interactive OSINT investigation dashboard."""
    return HTMLResponse(content=DASHBOARD_HTML)


def run():
    import uvicorn

    uvicorn.run(app, host=container.settings.HOST, port=container.settings.PORT)


if __name__ == "__main__":
    run()


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Yourosint v2 — Bounded Contexts OSINT Graph</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    :root {
      --bg-primary: #090d16;
      --bg-card: #111827;
      --border-subtle: #1f2937;
      --accent-cyan: #06b6d4;
      --accent-violet: #8b5cf6;
      --accent-rose: #f43f5e;
      --accent-emerald: #10b981;
    }
    body { background-color: var(--bg-primary); color: #f3f4f6; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; }
    .node-target { fill: #ef4444; filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.6)); }
    .node-contact { fill: #3b82f6; filter: drop-shadow(0 0 6px rgba(59, 130, 246, 0.4)); }
    .node-entity { fill: #10b981; filter: drop-shadow(0 0 6px rgba(16, 185, 129, 0.4)); }
    .edge-line { stroke: #475569; stroke-opacity: 0.6; stroke-width: 1.5px; }
    .edge-dashed { stroke: #8b5cf6; stroke-dasharray: 4,4; stroke-opacity: 0.8; stroke-width: 1.5px; }
    .glass-card { background: rgba(17, 24, 39, 0.8); backdrop-filter: blur(8px); border: 1px solid #1f2937; }
  </style>
</head>
<body class="min-h-screen">
  <!-- Header -->
  <header class="border-b border-gray-800 bg-gray-950/80 sticky top-0 z-50 px-6 py-3.5 backdrop-blur">
    <div class="max-w-7xl mx-auto flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="h-9 w-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-cyan-500/20">
          🛰️
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-lg font-bold tracking-tight text-white">yourosint <span class="text-cyan-400">v2</span></h1>
            <span class="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">Bounded Contexts</span>
          </div>
          <p class="text-xs text-gray-400">Ingestion • Intelligence • Graph Analytics • Enrichment • Privacy</p>
        </div>
      </div>
      <div class="flex items-center gap-3 text-xs">
        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <span class="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          Hexagonal Engine Online
        </span>
        <a href="/docs" target="_blank" class="px-3 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-300 border border-gray-700 transition">
          Swagger Docs
        </a>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="max-w-7xl mx-auto px-6 py-6 space-y-6">

    <!-- KPI Stats Bar -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="glass-card p-4 rounded-xl">
        <div class="text-xs text-gray-400 font-medium">Ingested Messages</div>
        <div id="stat-messages" class="text-2xl font-bold text-cyan-400 mt-1 font-mono">0</div>
        <div class="text-[11px] text-gray-500 mt-0.5">Ingestion Context</div>
      </div>
      <div class="glass-card p-4 rounded-xl">
        <div class="text-xs text-gray-400 font-medium">Intelligence Entities</div>
        <div id="stat-objects" class="text-2xl font-bold text-violet-400 mt-1 font-mono">0</div>
        <div class="text-[11px] text-gray-500 mt-0.5">Evidence Provenance Attached</div>
      </div>
      <div class="glass-card p-4 rounded-xl">
        <div class="text-xs text-gray-400 font-medium">Monitored Channels</div>
        <div id="stat-chats" class="text-2xl font-bold text-emerald-400 mt-1 font-mono">0</div>
        <div class="text-[11px] text-gray-500 mt-0.5">Auto-Cursor Tracking</div>
      </div>
      <div class="glass-card p-4 rounded-xl">
        <div class="text-xs text-gray-400 font-medium">AccountPool Workers</div>
        <div id="stat-accounts" class="text-2xl font-bold text-amber-400 mt-1 font-mono">1</div>
        <div class="text-[11px] text-gray-500 mt-0.5">Flood-Wait Shield</div>
      </div>
    </div>

    <!-- Search Section -->
    <div class="glass-card p-5 rounded-xl border border-gray-800">
      <h2 class="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">🔍 Multi-Modal OSINT Search</h2>
      <div class="flex gap-2">
        <input id="search-input" type="text" placeholder="Search target username (@durov), email, phone, IP, domain, or message text..."
          class="flex-1 bg-gray-950 border border-gray-800 rounded-lg px-4 py-2.5 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:border-cyan-500 transition">
        <button onclick="handleSearch()" class="px-5 py-2.5 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-white font-medium text-sm rounded-lg shadow-lg shadow-cyan-500/20 transition">
          Search
        </button>
      </div>
    </div>

    <!-- Investigation Main Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

      <!-- Left 2 Cols: Network Graph / Results View -->
      <div class="lg:col-span-2 space-y-6">

        <!-- Graph Visualization Card -->
        <div class="glass-card p-5 rounded-xl border border-gray-800">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="text-sm font-bold text-gray-200">Investigation Network Graph</h3>
              <p class="text-xs text-gray-400">Single-query SQL CTE interaction topology with direct and 2nd-level links</p>
            </div>
            <div class="flex items-center gap-2 text-xs">
              <span class="inline-flex items-center gap-1"><span class="h-2.5 w-2.5 rounded-full bg-rose-500"></span> Target</span>
              <span class="inline-flex items-center gap-1"><span class="h-2.5 w-2.5 rounded-full bg-blue-500"></span> Contact</span>
              <span class="inline-flex items-center gap-1"><span class="h-2.5 w-2.5 rounded-full bg-emerald-500"></span> IOC</span>
            </div>
          </div>

          <!-- SVG Visualizer Canvas -->
          <div class="w-full h-80 bg-gray-950 rounded-lg border border-gray-900 overflow-hidden relative flex items-center justify-center">
            <svg id="graph-svg" class="w-full h-full" viewBox="0 0 700 320">
              <!-- Rendered dynamically -->
            </svg>
          </div>
        </div>

        <!-- Search Results List -->
        <div class="glass-card p-5 rounded-xl border border-gray-800">
          <h3 class="text-sm font-bold text-gray-200 mb-3">Intelligence Results</h3>
          <div id="search-results" class="space-y-3 max-h-72 overflow-y-auto pr-1 text-xs text-gray-400">
            <div class="text-center py-8 text-gray-500">Enter a query or target username to see extracted intelligence</div>
          </div>
        </div>

      </div>

      <!-- Right 1 Col: Control Panels & Account Pool -->
      <div class="space-y-6">

        <!-- Parser Trigger Card -->
        <div class="glass-card p-5 rounded-xl border border-gray-800 space-y-3">
          <h3 class="text-sm font-bold text-gray-200">⚡ Ingestion Parser</h3>
          <div class="space-y-2">
            <input id="parse-chat-input" type="text" placeholder="Channel username (e.g. telegram)"
              class="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-xs text-gray-100 placeholder-gray-500 focus:outline-none focus:border-cyan-500">
            <div class="flex items-center gap-2">
              <input id="parse-limit" type="number" value="100" class="w-24 bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-xs text-gray-100">
              <button onclick="triggerParse()" class="flex-1 py-2 bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs rounded-lg transition">
                Start Ingestion
              </button>
            </div>
          </div>
          <div id="parse-status" class="text-[11px] text-gray-400"></div>
        </div>

        <!-- Account Pool Status -->
        <div class="glass-card p-5 rounded-xl border border-gray-800 space-y-3">
          <h3 class="text-sm font-bold text-gray-200">🛡️ AccountPool Status</h3>
          <div id="account-list" class="space-y-2 text-xs">
            <div class="p-2.5 rounded bg-gray-950 border border-gray-800 flex items-center justify-between">
              <div>
                <div class="font-medium text-gray-200">@primary_worker</div>
                <div class="text-[10px] text-gray-500">RPM: 0 • Errors: 0</div>
              </div>
              <span class="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">ACTIVE</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  </main>

  <script>
    async function loadStats() {
      try {
        const res = await fetch('/api/v1/stats');
        if (res.ok) {
          const data = await res.json();
          document.getElementById('stat-messages').innerText = data.total_messages;
          document.getElementById('stat-objects').innerText = data.total_objects;
          document.getElementById('stat-chats').innerText = data.total_chats;
        }
      } catch (e) { console.debug(e); }
    }

    async function handleSearch() {
      const q = document.getElementById('search-input').value.trim();
      if (!q) return;
      const resContainer = document.getElementById('search-results');
      resContainer.innerHTML = '<div class="text-center py-4 text-cyan-400">Searching bounded contexts...</div>';

      try {
        const res = await fetch(`/api/v1/intelligence/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();

        let html = '';
        if (data.phone_info) {
          html += `<div class="p-3 rounded bg-cyan-950/30 border border-cyan-800/40 mb-2">
            <div class="font-bold text-cyan-300">📞 Phone Intelligence: ${data.phone_info.international || q}</div>
            <div class="text-[11px] text-gray-400 mt-1">Carrier: ${data.phone_info.carrier || 'Unknown'} • Country: ${data.phone_info.country || 'Unknown'}</div>
          </div>`;
        }

        if (data.entities && data.entities.length > 0) {
          data.entities.forEach(obj => {
            html += `<div class="p-2.5 rounded bg-gray-950 border border-gray-800 flex items-center justify-between">
              <div>
                <span class="px-1.5 py-0.5 rounded text-[10px] uppercase font-mono bg-violet-500/10 text-violet-400 border border-violet-500/20 mr-2">${obj.type}</span>
                <span class="font-mono text-gray-200">${obj.masked_value || obj.value}</span>
                ${obj.description ? `<div class="text-[10px] text-gray-500 mt-0.5">${obj.description}</div>` : ''}
              </div>
              <span class="text-[10px] text-gray-500">Rep: ${obj.reputation}</span>
            </div>`;
          });
        }

        if (data.messages && data.messages.length > 0) {
          data.messages.forEach(msg => {
            html += `<div class="p-2.5 rounded bg-gray-950 border border-gray-800">
              <div class="flex items-center justify-between text-gray-400 text-[10px] mb-1">
                <span>@${msg.sender_username || 'anonymous'} in @${msg.chat_username || 'chat'}</span>
                <span>${new Date(msg.posted_at).toLocaleDateString()}</span>
              </div>
              <div class="text-gray-300 font-sans">${msg.text}</div>
            </div>`;
          });
        }

        if (!html) {
          html = '<div class="text-center py-6 text-gray-500">No entities or messages found</div>';
        }

        resContainer.innerHTML = html;
        loadGraph(q);
      } catch (e) {
        resContainer.innerHTML = `<div class="text-rose-400">Search error: ${e.message}</div>`;
      }
    }

    async function loadGraph(target = "durov") {
      try {
        const res = await fetch(`/api/v1/graph/user/${encodeURIComponent(target)}`);
        if (!res.ok) {
          loadGraphFallback(target);
          return;
        }
        const graph = await res.json();
        renderGraph(graph.nodes, graph.edges);
      } catch(e) {
        loadGraphFallback(target);
      }
    }

    function renderGraph(nodes, edges) {
      const svg = document.getElementById('graph-svg');
      if (!nodes || nodes.length === 0) return;

      const positions = {
        0: { x: 350, y: 150 },
        1: { x: 180, y: 80 },
        2: { x: 520, y: 90 },
        3: { x: 200, y: 240 },
        4: { x: 500, y: 230 },
      };

      let svgContent = '';
      edges.forEach(e => {
        const fromIdx = nodes.findIndex(n => n.id === e.source);
        const toIdx = nodes.findIndex(n => n.id === e.target);
        const fromP = positions[fromIdx] || { x: 200, y: 150 };
        const toP = positions[toIdx] || { x: 500, y: 150 };
        svgContent += `<line x1="${fromP.x}" y1="${fromP.y}" x2="${toP.x}" y2="${toP.y}" class="edge-line" />`;
      });

      nodes.forEach((n, idx) => {
        const pos = positions[idx] || { x: 350 + idx * 40, y: 150 };
        const isTarget = n.type === 'target';
        svgContent += `<g>
          <circle cx="${pos.x}" cy="${pos.y}" r="${isTarget ? 24 : 16}" class="${isTarget ? 'node-target' : 'node-contact'}" />
          <text x="${pos.x}" y="${pos.y + (isTarget ? 38 : 30)}" fill="#cbd5e1" font-size="10" text-anchor="middle" font-family="monospace">${n.label}</text>
        </g>`;
      });

      svg.innerHTML = svgContent;
    }

    function loadGraphFallback(target) {
      const svg = document.getElementById('graph-svg');
      const nodes = [
        { id: "target", label: `@${target}`, x: 350, y: 150, r: 24, class: "node-target" },
        { id: "c1", label: "@investigator_mike", x: 180, y: 80, r: 18, class: "node-contact" },
        { id: "c2", label: "@analyst_jane", x: 520, y: 90, r: 18, class: "node-contact" },
        { id: "e1", label: "ton.org", x: 200, y: 240, r: 14, class: "node-entity" },
        { id: "e2", label: "+79 *** *** 4567", x: 500, y: 230, r: 14, class: "node-entity" },
      ];
      const edges = [
        { from: "c1", to: "target", style: "edge-line" },
        { from: "c2", to: "target", style: "edge-line" },
        { from: "target", to: "e1", style: "edge-dashed" },
        { from: "target", to: "e2", style: "edge-dashed" },
      ];

      let svgContent = '';
      edges.forEach(e => {
        const f = nodes.find(n => n.id === e.from);
        const t = nodes.find(n => n.id === e.to);
        svgContent += `<line x1="${f.x}" y1="${f.y}" x2="${t.x}" y2="${t.y}" class="${e.style}" />`;
      });
      nodes.forEach(n => {
        svgContent += `<g>
          <circle cx="${n.x}" cy="${n.y}" r="${n.r}" class="${n.class}" />
          <text x="${n.x}" y="${n.y + n.r + 14}" fill="#cbd5e1" font-size="10" text-anchor="middle" font-family="monospace">${n.label}</text>
        </g>`;
      });
      svg.innerHTML = svgContent;
    }

    async function triggerParse() {
      const chat = document.getElementById('parse-chat-input').value.trim();
      const limit = parseInt(document.getElementById('parse-limit').value) || 100;
      if (!chat) return;

      const statusEl = document.getElementById('parse-status');
      statusEl.innerHTML = `<span class="text-cyan-400">Parsing @${chat}...</span>`;

      try {
        const res = await fetch('/api/v1/ingestion/parse', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ chat_username: chat, limit: limit })
        });
        const data = await res.json();
        if (res.ok) {
          statusEl.innerHTML = `<span class="text-emerald-400">✓ Ingestion complete: ${data.messages_saved} msgs saved (${data.duration_seconds}s)</span>`;
          loadStats();
        } else {
          statusEl.innerHTML = `<span class="text-rose-400">Error: ${data.detail}</span>`;
        }
      } catch (e) {
        statusEl.innerHTML = `<span class="text-rose-400">Error: ${e.message}</span>`;
      }
    }

    loadStats();
    loadGraph("durov");
  </script>
</body>
</html>
"""
