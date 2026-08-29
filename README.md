# 🎓 Moodle-Bot

> Automated, AI-summarized Moodle LMS notifications delivered directly to WhatsApp.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Package Manager](https://img.shields.io/badge/uv-fast_package_manager-purple.svg)](https://github.com/astral-sh/uv)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.62%2B-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#license)

Moodle-Bot continuously tracks enrolled course updates on your university Moodle LMS (new lecture slides, tutorial sheets, assignment announcements, and due-date changes). When changes occur, it normalizes the content, filters out internal noise, generates student-friendly digests using an LLM (via OpenRouter), and dispatches notifications to your WhatsApp in real-time.

---

## ✨ Features

- **⚡ Automated Background Monitoring**: Periodically scans enrolled course contents without keeping your browser open.
- **🔍 Smart Differential Tracking**: Uses deterministic SHA-256 hashing and normalization to detect added, updated, and removed materials while ignoring volatile Moodle session metadata.
- **🤖 AI-Generated WhatsApp Digests**: Converts raw LMS course deltas into friendly, structured group chat messages with emojis, direct downloadable links, and deadline alerts.
- **💬 WhatsApp Delivery (Neonize)**: Seamless QR code pairing to link your WhatsApp account directly through the dashboard.
- **🎨 Interactive Setup Dashboard**: A Streamlit web dashboard for Google authentication, Moodle credential configuration, and bot status monitoring.
- **🔒 Secure by Design**: Credentials and runtime databases are decoupled from source code and ignored by Git.

---

## 🏗️ Architecture

```text
┌─────────────────────────┐
│     University LMS      │
└────────────┬────────────┘
             │ (Periodic API Fetch every 5 min)
             ▼
┌─────────────────────────┐
│  Moodle Course Tracker  │  ◄── Compute stable SHA-256 hash & extract deltas
└────────────┬────────────┘
             │ (If delta detected)
             ▼
┌─────────────────────────┐
│  AI Summary Generator   │  ◄── OpenRouter LLM + Tool calling for download links
└────────────┬────────────┘
             │ (Polished notification message)
             ▼
┌─────────────────────────┐
│  WhatsApp Bot (Neonize) │  ──► Dispatched to WhatsApp chat / group
└─────────────────────────┘
```

---

## 📁 Project Structure

```text
moodle-bot/
├── .env.example              # Template for environment configuration
├── .gitignore                # Comprehensive Git ignore rules
├── pyproject.toml            # Project packaging and dependencies
├── README.md                 # Project documentation
│
├── data/                     # Local runtime data (ignored in Git)
│   ├── cache/                # Course content caches
│   ├── lms_app.db            # SQLite database for sessions & courses
│   └── session.sqlite3       # WhatsApp Neonize session
│
├── src/
│   └── moodle_bot/
│       ├── __init__.py       # Package init & CLI entrypoint
│       ├── config.py         # Central settings & directory management
│       ├── models.py         # Peewee ORM database models
│       ├── ai/
│       │   ├── summarizer.py # LLM notification generation & tool calling
│       │   └── api.py        # Backward-compatibility alias
│       ├── chat/
│       │   ├── sender.py     # Neonize WhatsApp message dispatcher
│       │   └── send.py       # Backward-compatibility alias
│       ├── moodle/
│       │   ├── courses.py    # Course content fetching & normalization
│       │   ├── tracker.py    # Differential change detector & trigger
│       │   └── services/     # LMS authentication & helper services
│       └── web/
│           └── app.py        # Streamlit interactive setup & dashboard
│
└── tests/                    # Unit test suite
    └── test_normalized_diff.py
```

---

## 🚀 Quick Start

### 1. Prerequisites
- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** (recommended) or standard `pip`
- On Windows, WSL (Windows Subsystem for Linux) is supported and recommended for Neonize WhatsApp binary compatibility.

### 2. Installation

Clone the repository and install dependencies:

```bash
# Clone the repository
git clone https://github.com/your-username/moodle-bot.git
cd moodle-bot

# Install dependencies using uv
uv sync
```

Or using `pip`:
```bash
python -m venv .venv
source .venv/bin/activate  # Or on Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e .
```

### 3. Configuration

Copy the example environment file and configure your keys:

```bash
cp .env.example .env
```

Edit `.env` to add your OpenRouter API key and target phone number:
```env
OPENROUTER_API_KEY=sk-or-v1-...
DEFAULT_PHONE_NUMBER=94767123456
```

### 4. Running the Dashboard

Launch the application using either the CLI command or Streamlit directly:

```bash
# Using the CLI entry point
uv run moodle-bot

# Or directly with Streamlit
uv run streamlit run src/moodle_bot/web/app.py
```

1. **Step 1: Sign in with Google**
2. **Step 2: Connect Moodle** (enter username, password, and university LMS URL)
3. **Step 3: Link WhatsApp** (scan the generated QR code with your phone)
4. **Step 4: Bot Active!** The background worker will automatically begin monitoring course changes every 5 minutes.

---

## 🧪 Running Tests

To verify normalization, hashing, and course delta diffing:

```bash
uv run python -m unittest discover -s tests
```

---

## 🛡️ Security

- **Never commit `.env`** or any `*.db` / `*.sqlite3` files.
- Database sessions and WhatsApp credentials are automatically stored in the ignored `data/` folder.
- Course tokens and passwords are only used locally to communicate with your specified university Moodle server.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
