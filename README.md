# TerminalBot 🤖

AI-powered terminal troubleshooting assistant for Fedora Linux that executes diagnostic commands, analyzes system state, and provides actionable recommendations - eliminating the need to memorize commands.

## Features

- **Natural Language Queries**: Ask questions in plain English
- **Hybrid LLM Support**: Use local Ollama models or cloud APIs (OpenAI, Claude)
- **Lite Mode**: Rule-based matching without any LLM (< 50MB memory, instant responses)
- **Safe Execution**: Built-in safety checks for destructive commands
- **Resource Efficient**: < 100MB memory, < 3s startup time
- **Plugin Architecture**: Extensible system for adding new capabilities

## Quick Start

### Installation

```bash
# Clone the repository
cd /mnt/mydrive/Projects/TerminalBot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install (core only - no LLM)
pip install -e .

# Or install with LLM support
pip install -e ".[ollama]"           # Local LLM
pip install -e ".[cloud]"            # Cloud LLMs
pip install -e ".[full]"             # All features
pip install -e ".[dev]"              # Development tools
```

### Configuration

```bash
# Initialize configuration
terminalbot init

# Edit config file (optional)
nano ~/.config/terminalbot/config.yaml

# Or set environment variables
cp .env.example .env
nano .env
```

### Usage

```bash
# Simple queries (works with lite mode) - NO 'query' keyword needed!
terminalbot "is nginx running?" --lite
terminalbot "check disk space" --lite
terminalbot "show top CPU processes" --lite

# Even complex queries work directly
terminalbot "show or check uptime" --lite

# Force LLM for complex analysis
terminalbot "why is my system slow?" --force-llm

# Dry run (show what would be executed)
terminalbot "list all services" --dry-run

# Show available capabilities
terminalbot capabilities
```

## Architecture

### Resource Efficiency

**Performance Targets:**
- **Startup**: < 1s (lite mode), < 3s (with LLM)
- **Memory**: < 50MB (lite), < 100MB (with LLM, excluding model)
- **Install Size**: ~15MB (core), ~30MB (with LLM deps)
- **LLM Model**: llama3.2:1b (1.3GB RAM) recommended

**Key Optimizations:**
1. **Lazy Loading** - LLM loaded only when needed
2. **Optional Dependencies** - Install only what you use
3. **Small Models** - 1B params sufficient for troubleshooting
4. **Rule-Based Fallback** - Instant responses without AI
5. **Async I/O** - Non-blocking operations
6. **Resource Limits** - 30s timeout, 10MB output cap

### Modes

1. **Lite Mode** (No LLM)
   - Rule-based regex matching
   - Zero memory overhead
   - Instant responses
   - Works offline

2. **Local LLM Mode** (Ollama)
   - Uses local model (llama3.2:1b)
   - Privacy-preserving
   - Free, no API costs
   - ~1.3GB RAM for model

3. **Cloud Mode** (OpenAI/Claude)
   - Most capable analysis
   - Requires API key
   - Pay-per-use
   - Best for complex queries

### Plugins

**Built-in Plugins:**
- `system` - System info, uptime, disk, memory
- `processes` - Find, list, monitor processes

**Future Plugins:**
- `services` - systemd service management
- `network` - Network diagnostics
- `logs` - Log analysis

## Configuration

### Config File

Default location: `~/.config/terminalbot/config.yaml`

```yaml
llm:
  primary: ollama           # Primary LLM (ollama, openai, anthropic, null)
  fallback: openai          # Fallback if primary fails
  enable_lite_mode: false   # Disable LLM entirely

  ollama:
    model: llama3.2:1b      # Lightweight model
    base_url: http://localhost:11434
    timeout: 10

  openai:
    model: gpt-4o-mini
    api_key: env:OPENAI_API_KEY

execution:
  command_timeout: 30       # seconds
  max_output_size: 10485760 # 10MB

safety:
  require_confirmation: true
  protected_processes:
    - systemd
    - sshd
```

### Environment Variables

```bash
# OpenAI API Key
export OPENAI_API_KEY=sk-your-key

# Anthropic API Key
export ANTHROPIC_API_KEY=sk-ant-your-key

# Override config with env vars
export TERMINALBOT_LLM__PRIMARY=openai
export TERMINALBOT_EXECUTION__COMMAND_TIMEOUT=60
```

## Examples

### System Information

```bash
# Check system status
terminalbot "check system info"

# Disk space
terminalbot "show disk usage"

# Memory usage
terminalbot "how much memory is free?"
```

### Process Management

```bash
# Find a process
terminalbot "is nginx running?"

# Top processes
terminalbot "show top 5 CPU-intensive processes"

# Check specific process
terminalbot "find python processes"
```

### Context-Aware Queries

```bash
# Works with current directory
cd /var/log
terminalbot "analyze recent errors in error.log"

# Relative paths
cd /etc/systemd/system
terminalbot "check service files here"
```

## Development

### Setup

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run linter
ruff check src/

# Run formatter
ruff format src/

# Run tests
pytest tests/ -v

# Type checking
mypy src/
```

### Project Structure

```
src/terminalbot/
├── cli/            # Click CLI interface
├── llm/            # LLM providers (Ollama, OpenAI, Claude)
├── executor/       # Safe command execution
├── agent/          # Agent coordinator, prompts, safety
├── plugins/        # Plugin system (system, processes)
├── config/         # Configuration management
└── utils/          # Utilities
```

### Adding a Plugin

```python
from terminalbot.plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    @property
    def name(self) -> str:
        return "myplugin"

    @property
    def description(self) -> str:
        return "My custom plugin"

    def get_tools(self) -> List[Dict[str, Any]]:
        return [{
            "name": "my_tool",
            "description": "What my tool does",
            "function": self.my_function,
            "parameters": {...}
        }]

    def my_function(self, arg: str) -> Dict[str, Any]:
        # Implement tool logic
        return {"success": True, "result": ...}
```

## Performance Benchmarking

```bash
# Test startup time
time terminalbot --lite "echo test"
# Expected: < 1 second

# Test memory usage
/usr/bin/time -v terminalbot "check system info" 2>&1 | grep "Maximum resident"
# Expected: < 100MB

# Test throughput (no memory leaks)
for i in {1..100}; do terminalbot --lite "uptime"; done
```

## Troubleshooting

### Ollama Not Available

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull lightweight model
ollama pull llama3.2:1b

# Verify
ollama list
```

### API Key Issues

```bash
# Check environment variables
echo $OPENAI_API_KEY

# Or set in config
terminalbot config set llm.openai.api_key "sk-your-key"
```

### Enable Debug Logging

```bash
terminalbot --verbose "your query"

# Or set in environment
export TERMINALBOT_LOGGING__LEVEL=DEBUG
```

## Roadmap

### Phase 1 (Current)
- ✅ Core command execution
- ✅ Rule-based matching (lite mode)
- ✅ Hybrid LLM support
- ✅ Basic plugins (system, processes)
- ✅ Safety mechanisms

### Phase 2 (Next)
- [ ] Additional plugins (services, network, logs)
- [ ] Full LangChain tool integration
- [ ] Interactive REPL mode
- [ ] Command history with autocomplete

### Phase 3 (Future)
- [ ] HTML report export
- [ ] Trend analysis
- [ ] PyPI package publication
- [ ] Fedora COPR repository

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure linting passes (`ruff check`)
5. Submit a pull request

## Support

- **Issues**: https://github.com/terminalbot/terminalbot/issues
- **Documentation**: See this README and inline comments
- **Questions**: Open a GitHub discussion
