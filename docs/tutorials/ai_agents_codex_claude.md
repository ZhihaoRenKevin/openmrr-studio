# Using OpenMRR Studio Offline or Online with Claude, Codex & Local LLMs

OpenMRR Studio works **100% offline out-of-the-box** and also connects cleanly to **Claude**, **OpenAI Codex**, and **Local Ollama / MLX** with **ultra-minimal token consumption (<150 tokens per physics call)** by running 100% of numerical solvers locally on your CPU / Apple Silicon AMX / NVIDIA CUDA GPU.

---

## 1. Switch Offline vs. Online AI Directly Inside the Studio UI

Above the chat box in OpenMRR Studio, select any of the 4 AI modes at any time:
1. **`⚡ Offline · Built-in Copilot` *(Default)***: 100% offline deterministic physics copilot (`0` tokens, zero internet needed).
2. **`🖥 Offline · Local Ollama / MLX`**: Connects locally to `http://127.0.0.1:11434` (`Ollama`) or `http://127.0.0.1:1234/v1` (`LM Studio`) with zero cloud data transfer.
3. **`🟣 Online · Claude`**: Automatically uses your locally signed-in `claude` (`Claude Code` CLI) login with zero extra API key needed, or accepts an optional in-memory API key via **`🔑 Key`**.
4. **`🟢 Online · Codex / OpenAI`**: Automatically uses your locally signed-in `codex` (`OpenAI Codex` CLI) login with zero extra API key needed, or accepts an optional in-memory API key via **`🔑 Key`**.

*(In every mode, 2D Maxwell FEM eigenmodes, spatial CMT integrals, fabrication dose sweeps, and `.GDS` exports run locally on your machine for exact physics!)*

---

## 2. Connect Directly to `Claude` or `Codex` via MCP (`<150 tokens/call`)

### OpenAI Codex (`Codex CLI` & `Codex Desktop`)
1. When you open `openmrr-studio` in Codex, Codex automatically reads [`AGENTS.md`](../../AGENTS.md) to invoke `openmrr agent` subcommands locally.
2. Optional MCP registration (`~/.codex/config.toml`):
   ```toml
   [mcp_servers.openmrr]
   command = "uv"
   args = ["--directory", "/path/to/openmrr-studio", "run", "openmrr", "mcp"]
   ```

### Claude Code & Claude Desktop
1. Opening `openmrr-studio` in `claude` automatically detects [`.mcp.json`](../../.mcp.json), exposing all 7 `openmrr_*` MCP tools (`openmrr_status`, `openmrr_width_cutoff`, `openmrr_design_mrr`, `openmrr_sweep_mrr`, `openmrr_fab_tolerance`, `openmrr_inspect_gds`, `openmrr_fit_spectrum`).
2. For Claude Desktop (`claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "openmrr": {
         "command": "uv",
         "args": ["--directory", "/path/to/openmrr-studio", "run", "openmrr", "mcp"]
       }
     }
   }
   ```
