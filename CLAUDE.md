# CLAUDE.md - Technical Notes for LLM Council

This file contains technical details, architectural decisions, and important implementation notes for future development sessions.

**Last Updated:** January 2026

## Project Overview

LLM Council is a 3-stage deliberation system where multiple LLMs collaboratively answer user questions. The key innovation is anonymized peer review in Stage 2, preventing models from playing favorites.

## Current State Summary

### Completed Features (Features 1-12 + Auth/Onboarding)

| Feature | Status | Description |
|---------|--------|-------------|
| Core 3-Stage Council | ✅ Complete | Stage 1 (responses), Stage 2 (peer ranking), Stage 3 (synthesis) |
| Streaming Responses | ✅ Complete | Real-time SSE streaming for all stages |
| Dark Theme UI | ✅ Complete | Modern dark theme with CSS variables |
| Responsive Header | ✅ Complete | Adaptive layout with breakpoints for all screen sizes |
| Voice Mode Toggle | ✅ Complete | Toggle button in header (UI ready) |
| Analytics Button | ✅ Complete | Toggle button in header |
| Config Panel | ✅ Complete | Settings/configuration panel |
| Sidebar | ✅ Complete | Conversation history with collapsible sidebar |
| User Authentication | ✅ Complete | JWT-based auth with registration/login |
| User Profile Dropdown | ✅ Complete | Profile menu with stats and logout |
| Onboarding Wizard | ✅ Complete | Multi-step tour for new users |
| Conversation Memory | ✅ Complete | Persistent conversation storage |

### Pending Features (from Plan)

The following 5 high-impact features are planned but NOT YET implemented:

| Phase | Feature | Purpose |
|-------|---------|---------|
| 1 | Smart Query Router | Route simple queries to 1 model, complex to full council (60-70% cost reduction) |
| 2 | Semantic Caching | Cache responses by semantic similarity for instant repeat responses |
| 3 | Factual Verification (Stage 1.5) | Cross-check factual claims between Stage 1 responses |
| 4 | Agentic Council (Tools) | Web search, calculator, code execution during Stage 1 |
| 5 | API Gateway Mode | OpenAI-compatible /v1/chat/completions endpoint |

See the plan file at `~/.claude/plans/humming-churning-hellman.md` for detailed implementation specs.

---

## Architecture

### Backend Structure (`backend/`)

**`config.py`**
- Contains `COUNCIL_MODELS` (list of OpenRouter model identifiers)
- Contains `CHAIRMAN_MODEL` (model that synthesizes final answer)
- Uses environment variable `OPENROUTER_API_KEY` from `.env`
- Backend runs on **port 8001** (NOT 8000 - user had another app on 8000)

**`openrouter.py`**
- `query_model()`: Single async model query
- `query_models_parallel()`: Parallel queries using `asyncio.gather()`
- Returns dict with 'content' and optional 'reasoning_details'
- Graceful degradation: returns None on failure, continues with successful responses

**`council.py`** - The Core Logic
- `stage1_collect_responses()`: Parallel queries to all council models
- `stage2_collect_rankings()`:
  - Anonymizes responses as "Response A, B, C, etc."
  - Creates `label_to_model` mapping for de-anonymization
  - Prompts models to evaluate and rank (with strict format requirements)
  - Returns tuple: (rankings_list, label_to_model_dict)
  - Each ranking includes both raw text and `parsed_ranking` list
- `stage3_synthesize_final()`: Chairman synthesizes from all responses + rankings
- `parse_ranking_from_text()`: Extracts "FINAL RANKING:" section, handles both numbered lists and plain format
- `calculate_aggregate_rankings()`: Computes average rank position across all peer evaluations

**`storage.py`**
- JSON-based conversation storage in `data/conversations/`
- Each conversation: `{id, created_at, messages[]}`
- Assistant messages contain: `{role, stage1, stage2, stage3}`
- Note: metadata (label_to_model, aggregate_rankings) is NOT persisted to storage, only returned via API

**`auth/`** - Authentication Module
- `models.py`: User and UserInDB Pydantic models
- `password.py`: PBKDF2-SHA256 password hashing with salt
- `jwt_handler.py`: JWT token creation and verification
- `storage.py`: JSON-based user storage in `data/users.json`

**`main.py`**
- FastAPI app with CORS enabled for localhost:5173, localhost:3000, and production URLs
- SSE streaming endpoint: `/api/conversations/{id}/message/stream`
- Auth endpoints: `/api/auth/register`, `/api/auth/login`, `/api/auth/me`
- Uses `Header` from FastAPI for Authorization header parsing

### Frontend Structure (`frontend/src/`)

**`App.jsx`**
- Main orchestration: manages conversations list and current conversation
- Mode toggles: Council, Voice, Analytics, Config
- Responsive header with toggle groups
- User profile integration

**`contexts/UserContext.jsx`**
- React Context for global auth state
- Manages user login/logout state
- Provides `useUser()` hook

**`components/ChatInterface.jsx`**
- Multiline textarea (3 rows, resizable)
- Enter to send, Shift+Enter for new line
- Streaming response display with real-time updates

**`components/auth/`**
- `UserProfile.jsx`: Profile button and dropdown menu
- `AuthModal.jsx`: Login/Register modal dialog
- `UserProfile.css`: Dark theme styling for auth components

**`components/onboarding/`**
- `OnboardingTour.jsx`: Multi-step wizard component
- `OnboardingTour.css`: Overlay with flexbox centering, pointer-events handling

**`components/Stage1.jsx`, `Stage2.jsx`, `Stage3.jsx`**
- Tab views for each deliberation stage
- ReactMarkdown rendering with syntax highlighting
- De-anonymization display in Stage 2

**Styling**
- `App.css`: Main layout, responsive header with breakpoints
- `index.css`: Global styles, CSS variables for theming
- Dark theme colors defined in `:root` variables

### CSS Variables (Theme)
```css
:root {
  --bg-primary: #0f0f1a;
  --bg-secondary: #1a1a2e;
  --bg-tertiary: #252542;
  --text-primary: #ffffff;
  --text-secondary: #a0a0b0;
  --accent-blue: #4a90e2;
  --accent-green: #22c55e;
  --accent-purple: #8b5cf6;
}
```

---

## Key Design Decisions

### Stage 2 Prompt Format
The Stage 2 prompt is very specific to ensure parseable output:
```
1. Evaluate each response individually first
2. Provide "FINAL RANKING:" header
3. Numbered list format: "1. Response C", "2. Response A", etc.
4. No additional text after ranking section
```

### De-anonymization Strategy
- Models receive: "Response A", "Response B", etc.
- Backend creates mapping: `{"Response A": "openai/gpt-5.1", ...}`
- Frontend displays model names in **bold** for readability
- Users see explanation that original evaluation used anonymous labels

### Authentication Flow
- No email verification required (user preference)
- JWT tokens stored in localStorage
- Tokens validated on each protected request via Authorization header
- Password hashing: PBKDF2-SHA256 with random salt

### Responsive Header Design
- Breakpoints: 1100px (full labels), 899px (icons only), 768px (tablet), 650px (mobile), 480px (small mobile)
- User profile uses `margin-left: auto` on large screens
- Mobile: absolute positioning for user profile to stay at far right
- Toggle groups use pill-style background with active state highlighting

### Onboarding Wizard
- Uses overlay with `pointer-events: none` except on dialog
- Dialog centered via flexbox on overlay
- Progress dots for step indication
- Skip button always available

---

## Important Implementation Details

### Relative Imports
All backend modules use relative imports (e.g., `from .config import ...`) not absolute imports. This is critical for Python's module system to work correctly when running as `python -m backend.main`.

### Port Configuration
- Backend: 8001 (changed from 8000 to avoid conflict)
- Frontend: 5173 (Vite default)
- Production: Deployed on Railway

### Required FastAPI Imports
```python
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, Header
```
Note: `Header` is required for parsing Authorization headers in auth endpoints.

### Markdown Rendering
All ReactMarkdown components must be wrapped in `<div className="markdown-content">` for proper spacing.

---

## Common Gotchas

1. **Module Import Errors**: Always run backend as `python -m backend.main` from project root
2. **CORS Issues**: Frontend must match allowed origins in `main.py` CORS middleware
3. **Header Import**: Missing `Header` import causes NameError on auth endpoints
4. **Onboarding Clicks**: Dialog needs `pointer-events: auto` and `position: relative`
5. **Responsive Overflow**: Avoid `overflow-x: auto` on header - causes scroll issues

---

## Deployment

### Railway
- Backend and frontend deployed separately
- Environment variables set in Railway dashboard
- OPENROUTER_API_KEY required for backend
- Frontend builds with Vite

### Git Repository
- Remote: https://github.com/ghwmelite-dotcom/my-llm-council.git
- Branch: master

---

## Next Steps (When Continuing)

1. **Smart Query Router (Phase 1)**: Implement complexity analysis and routing
   - Create `backend/routing/` module
   - Add complexity scoring based on query length, sub-questions, technical terms
   - Route simple queries to single model, complex to full council

2. **Semantic Caching (Phase 2)**: Add response caching
   - Create `backend/cache/` module
   - Implement TF-IDF similarity matching
   - Cache hit threshold: 0.85 similarity

3. **Factual Verification (Phase 3)**: Add Stage 1.5
   - Extract claims from responses
   - Detect contradictions between models
   - Inject findings into Stage 2 context

4. **Agentic Tools (Phase 4)**: Enable tool use
   - Web search, calculator, code execution
   - Tool registry pattern
   - Parallel tool execution

5. **API Gateway (Phase 5)**: OpenAI-compatible endpoint
   - /v1/chat/completions endpoint
   - Model name mapping to councils
   - Streaming support

---

## Data Flow Summary

```
User Query
    ↓
[Future: Smart Router → decides council size]
    ↓
[Future: Cache Check → return if hit]
    ↓
Stage 1: Parallel queries → [individual responses]
    ↓
[Future: Stage 1.5 Verification → check contradictions]
    ↓
Stage 2: Anonymize → Parallel ranking queries → [evaluations + parsed rankings]
    ↓
Aggregate Rankings Calculation → [sorted by avg position]
    ↓
Stage 3: Chairman synthesis with full context
    ↓
[Future: Cache Store → save for future]
    ↓
Return: {stage1, stage2, stage3, metadata}
    ↓
Frontend: Display with tabs + validation UI
```

The entire flow is async/parallel where possible to minimize latency.
