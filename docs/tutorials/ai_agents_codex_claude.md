# Using OpenMRR Studio with Codex, Claude Code, Claude Desktop & Local LLMs

OpenMRR Studio is engineered from the ground up for **AI-agent collaboration with ultra-minimal token consumption (<150 tokens per physics call)** by keeping 100% of heavy numerical computing on your **local CPU / Apple Silicon AMX / NVIDIA CUDA GPU**.

---

## Why Standard Photonics Scripts Burn LLM Tokens (and How OpenMRR Fixes It)

| Bottleneck in Naive Agent Workflows | OpenMRR Local-Compute Solution | Token Cost |
| :--- | :--- | :--- |
| Agent reads 4,000+ lines of solver code to figure out APIs | Repo root `AGENTS.md` + `CLAUDE.md` + `.mcp.json` give a 45-line zero-guesswork contract | **~350 tokens once** (vs ~35,000) |
| Agent prints 2,000-pt spectra or GDS polygon vertices to stdout | `openmrr agent` & `openmrr mcp` save `.csv`/`.gds`/`.lyp` locally and return **scalar KPI JSON only** | **~85–140 tokens/call** (vs ~18,000) |
| Agent re-solves 2D FEM modes from scratch on every CLI turn | Persistent SHA-256 local SSD mode cache (`outputs/.mode_cache/`) reuses solved eigenmodes in `<10 ms` | **25x faster local sweeps, 0 tokens** |
| Cloud API quota limits during interactive exploration | Built-in Copilot works **0-token offline** or connects to local **`Ollama` (`qwen3:14b`)** / **`LM Studio` (`MLX`)** | **0 cloud tokens** |

---

## 1. OpenAI Codex (`Codex CLI` & `Codex Desktop`)

1. **Zero-Config CLI + Skill Discovery**:
   When you open `openmrr-studio` in Codex, Codex automatically loads [`AGENTS.md`](../../AGENTS.md) and [`.agents/skills/openmrr-photonics/SKILL.md`](../../.agents/skills/openmrr-photonics/SKILL.md).
2. **Optional MCP Registration (`~/.codex/config.toml`)**:
   ```toml
   [mcp_servers.openmrr]
   command = "uv"
   args = ["--directory", "/path/to/openmrr-studio", "run", "openmrr", "mcp"]
   ```

---

## 2. Claude Code & Claude Desktop

1. **Claude Code (Automatic)**:
   Running `claude` inside `openmrr-studio` automatically loads [`CLAUDE.md`](../../CLAUDE.md), [`.mcp.json`](../../.mcp.json), and [`.claude/skills/openmrr-photonics/SKILL.md`](../../.claude/skills/openmrr-photonics/SKILL.md). All 6 `openmrr_*` MCP tools are immediately available!
2. **Claude Desktop (`claude_desktop_config.json`)**:
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

---

## 3. Local Zero-Cloud-Token LLMs (`Ollama` & `LM Studio` MLX)

In the OpenMRR Studio UI, check the **`Ollama`** box in the top-left Copilot header:
- OpenMRR automatically checks `http://127.0.0.1:11434` (`Ollama`, e.g. `qwen3:14b`) and falls back to `http://127.0.0.1:1234/v1` (`LM Studio` Apple Silicon MLX / GGUF).
- It sends **only a ~60-token scalar summary** with `"think": false`, returning a 1-sentence fabrication tip in `<1 s` locally while keeping 100% of your design private on-device.
