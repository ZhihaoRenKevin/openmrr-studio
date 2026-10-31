# OpenMRR Studio（开源集成光子微环仿真、对话式设计与双向 GDSII 平台）

**无需 Ansys Lumerical、Synopsys RSoft 或 COMSOL 商业许可证 —— 通过对话式 AI 光子设计助手（Copilot）、全矢量本征模与耦合模引擎、以及双向 GDSII 版图桥，一站式完成微环谐振器（MRR）选型、单模截止校验、临界耦合综合、扫参评估、版图生成与实验光谱拟合。**

[English](./README.md) | [简体中文](./README_zh-CN.md) | [求解器交叉验证与基准](./docs/VERIFICATION_AND_BENCHMARKS.md) | [对话与 GDS 进阶教程](./docs/tutorials/chatbot_and_gds_guide.md) | [Codex 与 Claude 极省 Token 接入指南](./docs/tutorials/ai_agents_codex_claude.md) | [llms.txt](./llms.txt) | [更新日志](./CHANGELOG.md)

[![Wavebands: 400nm–14µm](https://img.shields.io/badge/wavebands-400nm%20Vis%20to%2014%CE%BCm%20Mid--IR-ec4899.svg)](./docs/VERIFICATION_AND_BENCHMARKS.md)
[![MCP Server: <150 tokens/call](https://img.shields.io/badge/MCP_Server-%3C150_tokens%2Fcall-f59e0b.svg)](./server.json)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Python 3.11 | 3.12 | 3.13](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](./pyproject.toml)
[![Solver: Pure-BSD Conformal FEM](https://img.shields.io/badge/eigenmode-scikit--fem%20(BSD)-0284c7.svg)](./src/openmrr/eigenmode_solver.py)
[![Layout: Bidirectional GDSII](https://img.shields.io/badge/layout-gdstk%20%2B%20KLayout-6f42c1.svg)](./src/openmrr/gds_bridge.py)
[![Compute: Apple Silicon AMX/MLX | CUDA | CPU](https://img.shields.io/badge/compute-Apple%20Silicon%20%7C%20CUDA%20%7C%20CPU-10b981.svg)](./src/openmrr/hardware_accel.py)

![OpenMRR Studio Overview](./docs/images/hero_openmrr_overview.png)
*上图完全由仓库内 `scripts/generate_hero_figure.py` 无商业软件直接求解生成：**（a）** 2D 全矢量弯曲波导保形有限元模场（`4H-SiC`，`R = 40 um`，`82°` 侧壁倾角），**（b）** 同心滑轮耦合器（Pulley）包角扫描与自动临界耦合点（`theta_CC`）综合，**（c）** `X切薄膜铌酸锂（TFLN）` 跑道微环电光调谐光谱（`0 V` vs `+25 V`），**（d）** 实测级顺/逆时针背向散射劈裂双峰（Split-Doublet）CMT 参数提取。*

---

## 核心亮点

1. **对话式光子设计助手（Conversational Photonics Copilot，支持中英文）**：
   像与资深光子芯片工程师对话一样，逐步确认**波导材料 $\rightarrow$ 晶圆叠层（膜厚 `H_film`、平板层 `H_slab`、侧壁角、空气/氧化物上包层）$\rightarrow$ 偏振态（`TE0`/`TM0`）与单模宽度截止 $\rightarrow$ 目标 `FSR`/`Q` 与耦合器拓扑 $\rightarrow$ 容差扫参与 `.gds` 版图导出**。
2. **双向 GDSII / OASIS 版图桥（`Upload GDS -> Simulate` + `Create GDS`）**：
   - **上传 `.gds` 自动测量并仿真**：拖入任意由 KLayout 或 `gdsfactory` 绘制的 `.gds`/`.oas` 微环文件，内置几何引擎（`gdstk` + `shapely`）自动识别**圆环点耦合、跑道型、同心滑轮（Pulley）或双环游标（Vernier）**，直接从多边形精确量取 `R`、`W_ring`、`W_bus`、`gap_thru`、`gap_drop`、`L_s` 与 `pulley_angle`，在交互式 2D 画布上用红色卡尺标出耦合间距，确认膜厚后即可一键算出光谱！
   - **一键生成单器件或 MPW 扫参阵列 `.gds` + KLayout `.lyp`**：自动包含波导芯层（`1/0`）、半刻蚀平板层（`2/0`）、TiN 微加热器（`10/0`）、GSG 电光焊盘（`11/0`）、端口引脚（`65/0`）及 KLayout 配色文件（`.lyp`）。
3. **全波段覆盖（可见光 `400 nm` $\rightarrow$ O波段 `1310 nm` $\rightarrow$ C波段 `1550 nm` $\rightarrow$ 短波红外 `2 µm` $\rightarrow$ 中远红外 `3–14 µm`）× 7 大拓扑 × 24 种洁净室材料**：
   涵盖可见光/量子光学材料（`TiO2`、`Ta2O5`、`GaN`、`金刚石 Diamond`、`Al2O3`）、通信与非线性材料（`Si (SOI)`、`a-Si:H`、`LPCVD Si3N4`、`富硅氮化硅 SiNx`、`4H-SiC`、`3C-SiC`、`AlN`、`ScAlN (10%/20%/30%)`、`Z切/X切薄膜铌酸锂 TFLN`、`GSST 相变材料`）以及中红外低损耗材料与氟化物衬底（`Ge`、`CaF2`、`MgF2`、`Ge-on-Si`），内置跨波段自适应网格/仿真域缩放与带隙/多声子吸收自动预警（如 `Si < 1.12 µm` 禁带吸收与 `SiO2 > 3.6 µm` 中红外多声子吸收告警）。
4. **跨平台自适应算力（macOS Apple Silicon / Windows CUDA GPU / 纯 CPU）且 100% MIT/BSD 开源合规**：
   自动探测 Windows/Linux 上的 **NVIDIA CUDA (`FP64`)**、Mac 上的 **Apple Accelerate AMX / Metal** 或普通轻薄本的 **多核矢量化 CPU**；内置纯 BSD 约束 Delaunay 保形网格器（零 GPL 传染依赖），可自由商业化或打包独立桌面软件。

---

## 快速上手（macOS 与 Windows 通用）

### 第一步：安装 `uv` 并克隆仓库

```bash
# macOS / Linux 安装 uv：
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows PowerShell 安装 uv：
# irm https://astral.sh/uv/install.ps1 | iex

git clone https://github.com/ZhihaoRenKevin/openmrr-studio.git
cd openmrr-studio
```

### 第二步：按设备一键同步环境

```bash
# macOS (Apple Silicon M1–M5 / Intel)：
uv sync --extra desktop --extra apple

# Windows / Linux（仅 CPU 轻薄本）：
uv sync --extra desktop

# Windows / Linux（配备 NVIDIA RTX CUDA 显卡工作站）：
uv sync --extra desktop --extra cuda
```

### 第三步：启动桌面软件或网页工作台

```bash
# 启动原生桌面窗口（若未装 pywebview 会自动在默认浏览器打开）：
uv run openmrr

# 或直接在浏览器（Chrome / Safari / Edge）中打开：
uv run openmrr browser

# 也可直接双击启动脚本：
#   macOS   : launchers/OpenMRR_macOS.command
#   Windows : launchers\OpenMRR_Windows.bat
```

### 第四步：运行循序渐进的 Cookbook 示例脚本

```bash
# 0. 检查硬件加速后端、10万波长点 TMM 速度及 18 种材料折射率表：
uv run python examples/00_getting_started/00_check_environment.py

# 1. 扫描 400 nm Si3N4 波导宽度，自动定位 TE0 单模截止宽度（TE1 出现点）：
uv run python examples/00_getting_started/01_waveguide_dispersion_sweep.py

# 2. 设计 220 nm SOI 四端口跑道微环并执行耦合间距容差扫描：
uv run python examples/01_devices_and_sweeps/01_soi_point_and_racetrack.py

# 3. 综合 4H-SiC 同心滑轮微环临界耦合包角（ER > 60 dB）与 X切铌酸锂电光调谐：
uv run python examples/01_devices_and_sweeps/02_sin_and_sic_pulley_cc.py

# 4. 生成单微环版图及 5 器件 MPW 扫参阵列 .gds + KLayout .lyp：
uv run python examples/02_gds_roundtrip/01_create_mrr_and_sweep_array_gds.py

# 5. 读取任意外部 .gds 版图 -> 自动提取几何参数 -> 求解模场与透射谱：
uv run python examples/02_gds_roundtrip/02_upload_and_simulate_gds.py

# 6. 实验透射谱拟合（背向散射双峰劈裂 Q_int / Q_ext / 2g 与多 FSR 群折射率提取）：
uv run python examples/03_lab_spectrum_fitting/01_fit_doublet_and_multifsr.py
```

---

## 详细使用教学

### 1. 如何用左侧 Chatbot 从零设计微环？
打开软件后，左侧 **Photonics Design Copilot** 会引导你分三步确认需求（可直接点击气泡下方的快捷按钮，或输入中/英文自然语言）：
1. **输入材料与晶圆厚度**：例如输入 `600 nm 4H-SiC strip, SiO2 clad, TE0 at 1550 nm`（或 `400nm 氮化硅 条形波导 1550nm TE0`）。助手会自动调用 2D 有限元扫描波导宽度，给出单模最大宽度 `W_SM,max` 并填入推荐的 `W_bus` 和 `W_ring`。
2. **输入目标 FSR 与拓扑**：例如输入 `FSR 150 GHz, pulley all-pass`（或 `FSR 200 GHz 滑轮全通微环`）。助手会根据有限元算出的群折射率 $n_g$ 反解精确半径 $R$，完成全矢量弯曲模场与耦合积分，并给出**临界耦合目标值**。
3. **扫参优化与导出 GDS**：点击 `Apply Critical Coupling` 一键达到临界耦合，输入 `扫间距` / `Sweep gap 180 to 300 nm` 评估工艺容差，最后点击 `Create 5-Ring Sweep Array .GDS` 直接下载可投片的阵列 `.gds` 与 KLayout `.lyp`！

### 2. 如何上传已有 `.gds` 版图进行检查与光谱预测？
点击左侧聊天框顶部的 **`+ .GDS`**（或切到 **Tab 2** 拖入 `.gds`/`.oas` 文件）：
- 右侧画布立即渲染分层多边形（支持滚轮缩放、拖拽平移、图层开关）并用红色标尺显示实测 `gap`；
- 聊天框列出自动识别的拓扑、半径、波导宽和耦合间距，点击对应的晶圆膜厚预设（如 `400 nm Si3N4 + Simulate GDS`）即可立刻仿真光谱。

### 3. 如何接入 `Codex`、`Claude Code` 与本地大模型（单次调用 `< 150 Tokens` + 100% 本地算力）？
仓库根目录已内置 [`AGENTS.md`](./AGENTS.md)、[`CLAUDE.md`](./CLAUDE.md)、[`.mcp.json`](./.mcp.json)、`.agents/skills/` 与 `.claude/skills/`，并提供原生 **MCP 协议服务端**（`uv run openmrr mcp`）及极简 **Agent 命令行**（`uv run openmrr agent ...`）：
- **重计算全部走本地 CPU / Apple AMX / NVIDIA CUDA + SSD 本征模缓存**：首次求解 2D FEM 后自动写入 `outputs/.mode_cache/`，后续间距/包角/温升扫参在本地 **`< 0.2 秒`** 完成，零云端算力开销；
- **拒绝向大模型倾倒长数组（节省 99% Token）**：完整的透射谱 `.csv` 与版图 `.gds`/`.lyp` 直接保存在本地 `outputs/agent_runs/`，返回给 Codex / Claude 的永远是 **`< 150 Tokens` 的单行精炼指标 JSON**（详见 [Codex 与 Claude 极省 Token 接入指南](./docs/tutorials/ai_agents_codex_claude.md)）：

```bash
uv run openmrr agent design --top pulley_ap --mat 4H-SiC --h 0.60 --w-ring 1.10 --w-bus 0.82 --fsr 150 --gap 0.24 --cc --gds
```

---

## 免责声明与许可证

本仓库材料模型与默认层号源自公开学术文献，仅供光学设计、教学与流片前快速原型评估；正式流片前请务必使用目标代工厂官方 PDK 与 DRC 规则核验。本项目为独立开源项目，与 Ansys、Synopsys、COMSOL 无隶属或背书关系。代码遵循 [MIT 许可证](./LICENSE) 开源发布。
