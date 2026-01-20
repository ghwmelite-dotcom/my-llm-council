# LLM Council

<div align="center">

![LLM Council](https://img.shields.io/badge/LLM-Council-blue?style=for-the-badge&logo=openai)
![Python](https://img.shields.io/badge/Python-3.10+-green?style=for-the-badge&logo=python)
![React](https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi)
![Three.js](https://img.shields.io/badge/Three.js-3D-black?style=for-the-badge&logo=threedotjs)

**A sophisticated multi-LLM deliberation system where AI models collaborate, debate, and synthesize answers through democratic consensus.**

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [Usage](#-usage) • [API Reference](#-api-reference)

</div>

---

## Overview

LLM Council is an advanced AI deliberation platform that harnesses the collective intelligence of multiple large language models. Instead of relying on a single AI's response, the Council brings together diverse models (GPT, Claude, Gemini, Grok) to debate, evaluate each other's responses through anonymous peer review, and synthesize the best possible answer.

### The Three-Stage Process

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER QUERY                                        │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: INDEPENDENT RESPONSES                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                       │
│  │  GPT-5  │ │ Gemini  │ │ Claude  │ │  Grok   │                       │
│  │         │ │   Pro   │ │ Sonnet  │ │    4    │                       │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘                       │
│       │           │           │           │                             │
│       └───────────┴───────────┴───────────┘                             │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: ANONYMOUS PEER REVIEW                                         │
│                                                                          │
│  Responses anonymized as "Response A", "Response B", etc.               │
│  Each model evaluates and ranks ALL responses (including its own)       │
│  Models cannot identify which response belongs to which model           │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │  "Response C provides the most accurate analysis..."     │          │
│  │  "Response A lacks depth in addressing..."               │          │
│  │  FINAL RANKING: 1. Response C, 2. Response A, 3...       │          │
│  └──────────────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: CHAIRMAN SYNTHESIS                                            │
│                                                                          │
│  The Chairman model synthesizes the final answer considering:           │
│  • All original responses                                                │
│  • Peer review evaluations and rankings                                  │
│  • Aggregate voting results                                              │
│  • Dissenting opinions and minority views                               │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │              FINAL SYNTHESIZED ANSWER                     │          │
│  └──────────────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Features

### Tier 1: Immersive Experience

#### 🎮 3D Council Chamber
- **Interactive 3D visualization** using Three.js and React Three Fiber
- **Crystalline model avatars** positioned around a circular council table
- **Real-time animations** showing which model is speaking
- **Thought connection lines** between agreeing models
- **Dynamic lighting and particles** that respond to deliberation stages

#### 🔊 Voice Debate Mode
- **Text-to-speech synthesis** for each model's response
- **Distinct voice profiles** per model (pitch, rate, accent)
- **Playback controls** (play, pause, speed adjustment, skip)
- **Sequential narration** through all stages

### Tier 2: Deeper Deliberation

#### ⚔️ Multi-Round Debate
- **Rebuttal rounds** where criticized models can defend their positions
- **Automatic consensus detection** to stop debates early when agreement is reached
- **Configurable debate depth** (1-5 rounds)

#### 😈 Devil's Advocate
- **Automatic challenge generation** for the top-ranked response
- **Critical analysis** identifying potential weaknesses
- **Strengthens final synthesis** by addressing counterarguments

#### 👤 User Participation
- **Join the council** by submitting your own response
- **Anonymous evaluation** alongside AI models
- **See your ranking** compared to the models

### Tier 3: Living System

#### 🧠 Persistent Memory
- **Conversation memory extraction** (facts, decisions, insights)
- **Semantic memory retrieval** for relevant context injection
- **Model relationship tracking** (agreement patterns over time)

#### 🏛️ Specialized Sub-Councils
| Council | Models | Use Case |
|---------|--------|----------|
| **Math** | o1, Claude, Gemini | Complex calculations |
| **Ethics** | Claude, GPT, Gemini | Moral dilemmas |
| **Creative** | Claude, GPT, Grok | Creative writing |
| **Supreme** | All models | Appeals & arbitration |

- **Automatic query routing** based on topic detection

#### 🌐 Real-time World Connection
- **News feed integration** (NewsAPI)
- **Weather context** (OpenWeatherMap)
- **Current events** (Wikipedia)
- **Smart context injection** for time-sensitive queries

### Tier 4: Meta & Experimental

#### 🎲 Prediction Markets
- **Predict the winner** before deliberation concludes
- **Confidence-weighted scoring** (higher confidence = higher risk/reward)
- **Elo rating system** tracking model performance over time
- **User leaderboards** for prediction accuracy

#### 📜 Constitutional Governance
**5 Core Articles:**
1. 🎯 Truth and Accuracy
2. ⚖️ Ethical Consideration
3. 💡 Simplicity Preference
4. 📝 Recording of Dissent
5. 🚫 Prohibition of Deception

- **Amendment system** for proposing and voting on changes
- **Automatic enforcement** via prompt injection

#### 🔬 Observer Model (Meta-Cognition)
- **Cognitive bias detection**: Groupthink, Anchoring, Confirmation Bias
- **Deliberation quality metrics**: Diversity, Ranking Quality, Synthesis Completeness
- **Health scoring** with actionable recommendations
- **Historical trend analysis**

---

## 🏗️ Architecture

```
llm-council/
├── backend/
│   ├── main.py              # FastAPI application & endpoints
│   ├── council.py           # Core 3-stage deliberation logic
│   ├── openrouter.py        # LLM API integration
│   ├── storage.py           # Conversation persistence
│   ├── config.py            # Configuration & feature flags
│   │
│   ├── memory/              # Tier 3: Persistent Memory
│   │   ├── storage.py       # Memory persistence
│   │   ├── retrieval.py     # Semantic search
│   │   ├── injection.py     # Context injection
│   │   ├── extraction.py    # Memory extraction
│   │   └── relationships.py # Model agreement tracking
│   │
│   ├── councils/            # Tier 3: Specialized Councils
│   │   ├── definitions.py   # Council configurations
│   │   ├── router.py        # Query routing
│   │   ├── appeals.py       # Appeal system
│   │   └── executor.py      # Council execution
│   │
│   ├── feeds/               # Tier 3: World Connection
│   │   ├── manager.py       # Feed management
│   │   ├── aggregator.py    # Feed aggregation
│   │   └── injector.py      # Context injection
│   │
│   ├── predictions/         # Tier 4: Prediction Markets
│   │   ├── betting.py       # Prediction placement
│   │   ├── scoring.py       # Point calculation
│   │   ├── elo.py           # Elo ratings
│   │   └── leaderboard.py   # Rankings
│   │
│   ├── constitution/        # Tier 4: Governance
│   │   ├── templates.py     # Article templates
│   │   ├── storage.py       # Constitution persistence
│   │   ├── enforcement.py   # Prompt injection
│   │   └── amendments.py    # Amendment voting
│   │
│   └── observer/            # Tier 4: Meta-Cognition
│       ├── analyzer.py      # Quality analysis
│       ├── bias_detector.py # Bias detection
│       └── reporter.py      # Report generation
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main application
│   │   ├── api.js           # Backend communication
│   │   │
│   │   ├── components/
│   │   │   ├── ChatInterface.jsx
│   │   │   ├── Stage1.jsx, Stage2.jsx, Stage3.jsx
│   │   │   │
│   │   │   ├── immersive/   # 3D Council Chamber
│   │   │   ├── voice/       # Voice Synthesis
│   │   │   ├── debate/      # Tier 2 Features
│   │   │   ├── predictions/ # Prediction Markets
│   │   │   ├── constitution/# Governance UI
│   │   │   └── observer/    # Meta-Cognition UI
│   │   │
│   │   ├── stores/          # Zustand State Management
│   │   └── config/          # Model Profiles
│   │
│   └── package.json
│
└── data/                    # Persistent Storage
    ├── conversations/
    ├── memory/
    ├── predictions/
    └── constitution/
```

---

## 📦 Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- OpenRouter API key

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/ghwmelite-dotcom/my-llm-council.git
cd my-llm-council

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn httpx python-dotenv

# Configure environment
echo "OPENROUTER_API_KEY=your_key_here" > .env
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# 3D and state management packages are included
```

---

## 🎯 Usage

### Starting the Application

```bash
# Terminal 1: Start backend
python -m backend.main
# Server runs on http://localhost:8001

# Terminal 2: Start frontend
cd frontend && npm run dev
# App runs on http://localhost:5173
```

### Basic Query

1. Open the application in your browser
2. Type your question in the input field
3. Watch as the council deliberates through all three stages
4. Review individual responses, peer evaluations, and the final synthesis

### Immersive Mode

Toggle **"Immersive Mode"** in the header to experience:
- 3D council chamber visualization
- Animated avatars representing each model
- Visual connections between agreeing models

### Voice Mode

Toggle **"Voice Mode"** to hear:
- Each model's response read aloud
- Distinct voice characteristics per model
- Full deliberation narration

---

## 📡 API Reference

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/conversations` | GET | List all conversations |
| `/api/conversations` | POST | Create new conversation |
| `/api/conversations/{id}` | GET | Get conversation details |
| `/api/conversations/{id}/message/stream` | POST | Send message (streaming) |
| `/api/conversations/{id}/message/stream/v2` | POST | Send with Tier 2 features |

### Prediction Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/predictions/{conversation_id}` | POST | Place a prediction |
| `/api/predictions/{conversation_id}/resolve` | POST | Resolve predictions |
| `/api/leaderboard` | GET | Get rankings |
| `/api/predictions/summary` | GET | Market summary |

### Constitution Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/constitution` | GET | Get current constitution |
| `/api/amendments` | GET | Get pending amendments |
| `/api/amendments` | POST | Propose amendment |
| `/api/amendments/{id}/vote` | POST | Vote on amendment |

### Observer Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/observer/analyze/{conversation_id}` | POST | Run analysis |
| `/api/observer/report/{conversation_id}` | GET | Get report |
| `/api/observer/health/{conversation_id}` | GET | Get health score |

---

## ⚙️ Configuration

### Council Models

Edit `backend/config.py` to customize:

```python
COUNCIL_MODELS = [
    "openai/gpt-5.1",
    "google/gemini-3-pro-preview",
    "anthropic/claude-sonnet-4.5",
    "x-ai/grok-4"
]

CHAIRMAN_MODEL = "google/gemini-3-pro-preview"
```

### Feature Flags

```python
DEBATE_CONFIG = {
    "enabled": True,
    "max_rounds": 3,
    "consensus_threshold": 0.8,
}

DEVILS_ADVOCATE_CONFIG = {
    "enabled": True,
    "challenge_top_n": 1,
}

CONSTITUTION_CONFIG = {
    "enabled": True,
    "inject_into_prompts": True,
}

OBSERVER_CONFIG = {
    "enabled": True,
    "auto_analyze": True,
}
```

---

## 🤔 Why LLM Council?

### The Problem with Single-Model Responses

| Issue | Impact |
|-------|--------|
| **Bias** | Each model has inherent biases from training data |
| **Blind spots** | Individual models miss edge cases |
| **Overconfidence** | No self-correction mechanism |
| **Limited perspective** | Single viewpoint on complex issues |

### The Council Solution

| Advantage | How It Works |
|-----------|--------------|
| **Diverse perspectives** | Multiple models with different training approaches |
| **Peer review** | Anonymous evaluation prevents favoritism |
| **Democratic consensus** | Aggregate rankings surface the best answer |
| **Transparency** | Full visibility into the deliberation process |
| **Meta-cognition** | Observer detects biases and quality issues |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI, Python 3.10+, async httpx |
| **Frontend** | React 18, Vite, Zustand |
| **3D Graphics** | Three.js, React Three Fiber, Drei |
| **Voice** | Web Speech Synthesis API |
| **LLM Access** | OpenRouter API |
| **Storage** | JSON files (conversations, memory, predictions) |

---

## 🙏 Acknowledgments

- Original concept inspired by [Andrej Karpathy's LLM Council](https://github.com/karpathy/llm-council)
- Built with [FastAPI](https://fastapi.tiangolo.com/), [React](https://reactjs.org/), [Three.js](https://threejs.org/)
- LLM access via [OpenRouter](https://openrouter.ai/)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with collective AI intelligence** 🤖🤖🤖🤖

[⬆ Back to Top](#llm-council)

</div>
