# PullData Documentation

Complete documentation for PullData - Turn Documents into Deliverables.

---

## 📚 Documentation Index

### Getting Started
- **[Quick Start](../QUICKSTART.md)** - Get up and running in 5 minutes
- **[Features Status](FEATURES_STATUS.md)** - Current implementation status (~95% complete)

### Configuration
- **[Config Quick Start](CONFIG_QUICKSTART.md)** ⭐ - Quick reference for changing settings
- **[Configuration Guide](CONFIG_GUIDE.md)** - Complete configuration reference with examples
- **[API Configuration](API_CONFIGURATION.md)** - Detailed API provider setup (OpenAI, LM Studio, Ollama, etc.)

### Using PullData
- **[Web UI Guide](WEB_UI_GUIDE.md)** ⭐ - Complete guide for using the Web interface and REST API

### Contributing
- **[Contributing Guide](../CONTRIBUTING.md)** - How to contribute to PullData

---

## 📖 Quick Links by Use Case

### "I want to use the Web UI"
1. [Quick Start](../QUICKSTART.md) - Install and start server
2. [Web UI Guide](WEB_UI_GUIDE.md) - Learn the interface

### "I want to use API embeddings (LM Studio, OpenAI, etc.)"
1. [Config Quick Start](CONFIG_QUICKSTART.md) - TL;DR version
2. [Configuration Guide](CONFIG_GUIDE.md) - Detailed examples for each provider

### "I want to use the Python API"
1. [Quick Start](../QUICKSTART.md) - Installation and basic usage
2. [Configuration Guide](CONFIG_GUIDE.md) - Advanced configuration options

### "I want to contribute"
1. [Contributing Guide](../CONTRIBUTING.md) - Guidelines and setup
2. [Features Status](FEATURES_STATUS.md) - What needs work

---

## 📂 Documentation Organization

```
docs/
├── README.md                  # This file - Documentation index
├── CONFIG_QUICKSTART.md       # Quick config reference (start here!)
├── CONFIG_GUIDE.md            # Complete config guide with examples
├── API_CONFIGURATION.md       # API provider setup details
├── WEB_UI_GUIDE.md           # Web UI and REST API guide
└── FEATURES_STATUS.md        # Current implementation status
```

---

## 🔧 Most Common Tasks

### Change Embeddings/LLM Settings
See: [Config Quick Start](CONFIG_QUICKSTART.md)

```bash
# Edit config before starting server
notepad configs/lm_studio.yaml

# Start server
python run_server.py

# Select config in Web UI dropdown
```

### Start the Web UI
See: [Web UI Guide](WEB_UI_GUIDE.md)

```bash
python run_server.py
# Open: http://localhost:8000/ui/
```

### Use Different API Providers
See: [API Configuration](API_CONFIGURATION.md)

- LM Studio (local, free)
- OpenAI (GPT-3.5, GPT-4)
- Ollama (local, free)
- Groq (fast, cloud)
- And more...

---

## 💡 Tips

1. **Start with Config Quick Start** if you want to change settings
2. **Use the Web UI** for easiest experience
3. **Check Features Status** to see what's implemented
4. **Read API Configuration** for provider-specific setup

---

**Need Help?**
- Issues: https://github.com/pulldata/pulldata/issues
- Discussions: https://github.com/pulldata/pulldata/discussions

---

**Last Updated:** 2024-12-18
