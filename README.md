# Bambu Forge MCP

All-in-one MCP (Model Context Protocol) server for Bambu Lab 3D printers. Covers the full pipeline from model creation to printed object: parametric model generation, printability analysis, slicing optimization, printer control via MQTT, and a learning system that improves recommendations over time.

**35 tools** across 5 toolsets. Works with Cursor, Claude Code, or any MCP-compatible client.

**Supported printers:** P1P, P1S, X1, X1C, X1E, A1 Mini, A1, P2S, H2S, H2D, H2C, H2D Pro, H2D Laser Edition.

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| macOS | Full support | Design iteration auto-replaces the Bambu Studio plate |
| Windows | Supported | Auto-opens models in Bambu Studio |
| Linux | Supported | Auto-opens models via `xdg-open` |

The core server (model generation, printer control, profiles, safety) is fully cross-platform. The only macOS-specific feature is the "quit and reopen" behavior that gives you a clean plate on each design iteration. On Windows and Linux, generated models open in Bambu Studio but are added to the current plate.

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/pizzasuprema/bambu-forge-mcp.git
cd bambu-forge-mcp
uv sync
```

### 2. Connect to your AI coding agent

Replace `/path/to/bambu-forge-mcp` with the actual path where you cloned the repo. All platforms use the same env vars for printer configuration.

#### Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "bambu-forge": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--project", "/path/to/bambu-forge-mcp", "bambu-forge-mcp"],
      "env": {
        "BAMBU_PRINTER_IP": "192.168.1.100",
        "BAMBU_ACCESS_CODE": "12345678",
        "BAMBU_SERIAL_NUMBER": "YOUR_SERIAL",
        "BAMBU_PRINTER_MODEL": "H2C"
      }
    }
  }
}
```

#### Claude Code

```bash
claude mcp add bambu-forge \
  -e BAMBU_PRINTER_IP=192.168.1.100 \
  -e BAMBU_ACCESS_CODE=12345678 \
  -e BAMBU_SERIAL_NUMBER=YOUR_SERIAL \
  -e BAMBU_PRINTER_MODEL=H2C \
  -- uv run --project /path/to/bambu-forge-mcp bambu-forge-mcp
```

#### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "bambu-forge": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/bambu-forge-mcp", "bambu-forge-mcp"],
      "env": {
        "BAMBU_PRINTER_IP": "192.168.1.100",
        "BAMBU_ACCESS_CODE": "12345678",
        "BAMBU_SERIAL_NUMBER": "YOUR_SERIAL",
        "BAMBU_PRINTER_MODEL": "H2C"
      }
    }
  }
}
```

#### Any MCP-compatible client

The server uses stdio transport. Run it with:

```bash
BAMBU_PRINTER_IP=192.168.1.100 \
BAMBU_ACCESS_CODE=12345678 \
BAMBU_SERIAL_NUMBER=YOUR_SERIAL \
BAMBU_PRINTER_MODEL=H2C \
uv run --project /path/to/bambu-forge-mcp bambu-forge-mcp
```

### 3. Try Mock Mode (no printer needed)

Set `"BAMBU_FORGE_MOCK": "true"` in the env block to test without a real printer. Works with all clients above.

---

## Usage Examples

Once configured, just talk to your AI assistant. It calls the tools automatically.

### Design and Print a Part

> **You:** Make me a phone stand angled at 15 degrees for my desk

The assistant will:
1. Call `generate_model` with CadQuery code for an angled cradle
2. Call `analyze_printability` to check for issues
3. Call `optimize_settings` with priority "quality"
4. Call `estimate_cost` to calculate filament and time
5. Call `slice_model` to prepare for printing
6. Call `start_print` to send it to your printer

> **You:** Check on my print

Calls `printer_status` — returns progress %, temperatures, layer count, remaining time.

> **You:** Take a snapshot of the print

Calls `camera_snapshot` — captures an image from the printer camera for visual inspection.

### Iterate on Designs

> **You:** Make the phone stand 10mm wider

The assistant retrieves the original CadQuery source from Design DNA (via `list_designs`), modifies the parameters, and regenerates — no starting from scratch.

> **You:** Cut the top off at 80mm height

Calls `modify_model` with a cut operation at z=80mm.

> **You:** Combine this bracket with the mounting plate

Calls `combine_models` with a "union" boolean operation.

### Optimize for Your Printer

> **You:** Optimize this for speed on my H2C

Calls `optimize_settings` with priority "speed" — adjusts layer height, wall count, infill, and speeds based on the H2C's capabilities (350°C nozzle, enclosed chamber, dual nozzle).

> **You:** What's the best profile for this model?

Calls `recommend_profile` — matches saved profiles against the model geometry, boosted by historical success rates from previous prints.

### Manage Profiles and Materials

> **You:** Save these settings as "Fast PLA"

Calls `save_profile` with base profile and overrides.

> **You:** Import my Bambu Studio profiles

Calls `import_studio_config` — reads your existing profiles with full inheritance resolution.

> **You:** What filaments do I have?

Calls `list_filaments` to show available materials with temperature ranges and properties.

### Printer Control

> **You:** Pause the print

Calls `control_print` with action "pause".

> **You:** Set the nozzle to 215 degrees

Calls `manage_printer` — validates against the printer's safety limits before sending.

> **You:** Set nozzle to 500 degrees

Blocked by safety validation — returns `TEMP_OUT_OF_RANGE` error. The H2C max is 350°C.

> **You:** What's the AMS status?

Calls `manage_ams` with action "status" — returns tray info, filament types, colors, and remaining percentages.

### Search and Discover

> **You:** Search MakerWorld for cable organizers

Calls `search_marketplace` — returns models with names, creators, print counts, and download links.

> **You:** Find printers on my network

Calls `discover_printers` via SSDP — lists all Bambu Lab printers with IP, model, serial, and firmware version.

### Laser and Cut Patterns (H2C/H2D)

> **You:** Create an SVG pattern for laser engraving my logo

Calls `generate_2d_pattern` with svgwrite code — outputs an SVG file for the H2C's laser mode.

### Track Print History

> **You:** Log this print as successful, quality was excellent

Calls `log_print_outcome` with outcome, quality grade, and the profile used.

> **You:** Show me my print insights

Calls `get_print_insights` — total prints, success rate, average print time, filament usage, most common failure modes.

> **You:** How much have I printed this month?

Calls `list_print_history` — shows recent prints with outcomes, times, and filament usage.

---

## All 35 Tools

### Model Generation (10)

| Tool | Description |
|------|-------------|
| `generate_model` | Create a 3D model from CadQuery code |
| `generate_model_ai` | Submit an AI text-to-3D generation job (Meshy/Tripo3D) |
| `check_generation` | Poll AI generation job status |
| `list_designs` | Search/list previous designs from Design DNA store |
| `modify_model` | Apply operations (scale, rotate, mirror, translate, cut) to a mesh |
| `combine_models` | Boolean operation (union, difference, intersection) on two meshes |
| `generate_2d_pattern` | Generate SVG/DXF patterns for laser cutting |
| `search_marketplace` | Search MakerWorld for existing models |
| `list_templates` | List available parametric templates |
| `render_template` | Render a template with custom parameters |

### Prepare Stage (6)

| Tool | Description |
|------|-------------|
| `analyze_printability` | 7-dimension analysis: overhangs, thin walls, bridging, adhesion, supports, warping, thermal stress |
| `slice_model` | Slice via Bambu Studio CLI |
| `arrange_plate` | Auto-arrange models on build plate (compact/accessible/batch) |
| `optimize_settings` | Optimize settings for speed, quality, strength, material efficiency, or silent |
| `estimate_cost` | Calculate filament, power, and time costs |
| `export_project` | Export ready-to-print 3MF (planned) |

### Printer Control (8)

| Tool | Description |
|------|-------------|
| `printer_status` | Full printer state: temps, progress, AMS, errors |
| `start_print` | Upload and start printing |
| `control_print` | Pause, resume, stop, change speed, skip objects |
| `send_gcode` | Send a single G-code line (safety validated) |
| `manage_ams` | AMS/Vortek status, switch, configure trays |
| `manage_printer` | Set temperatures, lights, sound (safety validated) |
| `calibrate` | Trigger flow dynamics, bed leveling, nozzle offset calibration |
| `camera_snapshot` | Capture image from printer camera |

### Profiles & Learning (10)

| Tool | Description |
|------|-------------|
| `list_profiles` | List saved print profiles |
| `get_profile` | Get profile details with inheritance resolved |
| `save_profile` | Save settings as a named profile |
| `delete_profile` | Delete a profile |
| `recommend_profile` | AI-powered profile recommendation (history-boosted) |
| `list_filaments` | List filament materials with properties |
| `import_studio_config` | Import profiles from Bambu Studio |
| `log_print_outcome` | Log print success/failure with quality grade |
| `list_print_history` | Browse recent print history |
| `get_print_insights` | Analytics: success rate, filament usage, failure patterns |

### Setup (2)

| Tool | Description |
|------|-------------|
| `discover_printers` | SSDP scan for Bambu Lab printers on LAN |
| `setup_printer` | Configure printer connection |

---

## Safety

Four-level safety architecture:

1. **G-code validation** — blocks dangerous commands (firmware reset, EEPROM wipe)
2. **Pre-flight checks** — validates printer state, build volume, material compatibility before every print
3. **Printer safety profiles** — per-model temperature and axis limits from Bambu Studio configs
4. **Heater watchdog** — auto-cools idle heaters after 30 minutes

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BAMBU_PRINTER_IP` | Yes | Printer IP address |
| `BAMBU_ACCESS_CODE` | Yes | 8-digit access code (never stored to disk) |
| `BAMBU_SERIAL_NUMBER` | Yes | Printer serial number |
| `BAMBU_PRINTER_MODEL` | No | Printer model (auto-detected via SSDP) |
| `BAMBU_FORGE_MOCK` | No | Set to "true" for testing without a printer |
| `MESHY_API_KEY` | No | For AI model generation via Meshy |
| `TRIPO3D_API_KEY` | No | For AI model generation via Tripo3D |

### Config File

Optional `~/.bambu-forge/config.json` for non-sensitive settings (slicer path, workspace dirs, cost rates). Environment variables always take precedence.

---

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest tests/ -v

# Run in mock mode
BAMBU_FORGE_MOCK=true BAMBU_PRINTER_MODEL=H2C uv run bambu-forge-mcp
```

124 tests covering all tools, safety validation, MQTT protocol, profile inheritance, and Design DNA lineage.

---

## License

MIT
