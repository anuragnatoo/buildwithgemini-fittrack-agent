# FitTrack AI 🏋️‍♂️

FitTrack AI is an intelligent workout planner and coach built on Google Cloud's Agent Development Kit (ADK) and Gemini. It creates personalized workout splits for **Bulking** (hypertrophy) and **Endurance** (stamina & conditioning), calculates metabolic calorie burn estimates, tracks user workout history, remembers long-term preferences and allergies across conversations, and generates workout visuals.

---

## What It Actually Does

The codebase in this repository implements the following real capabilities:

### 1. Persistent Long-Term Memory (Vertex AI Memory Bank)
- **PreloadMemoryTool:** Automatically preloads stored user context (injury history, baseline weight, fitness preferences, equipment availability) into the prompt at the beginning of each turn.
- **Custom Memory Extraction Topic (`USER_ALLERGIES`):** Captures and tracks user-stated food sensitivities, equipment allergies (such as latex resistance bands), and medical restrictions across conversations.
- **Background Extraction (`generate_memories_callback`):** Asynchronously passes turn transcripts to Vertex AI Memory Bank (`callback_context.add_session_to_memory`) after every interaction.

### 2. Firestore Workout & Exercise Catalog
Backed by a Cloud Firestore Native collection (`exercises`):
- `list_exercises(muscle_group)`: Fetches exercises from the Firestore catalog filtered by targeted muscle group (e.g., Chest, Quadriceps, Back, Shoulders).
- `save_exercise(id, name, primary_muscle, secondary_muscles, equipment, met_value, focus_recommendations, instructions)`: Adds custom exercises with focus-specific sets/reps protocols to the database.
- `log_workout_session(user_id, workout_name, duration_minutes, estimated_calories_burned, exercises_completed, notes)`: Stores completed workout logs with timestamps in Firestore (`user_workouts`).
- `get_user_workout_history(user_id, limit)`: Retrieves recent logged workouts for progress tracking.

### 3. Public Fitness API Integration
- `search_wger_exercises(muscle_group, limit)`: Queries the free public [wger Exercise API](https://wger.de/api/v2/exerciseinfo/) for real-time exercise descriptions and muscle mapping, supporting an optional `WGER_API_KEY` environment variable.

### 4. Deterministic Metabolic Calorie Estimation
- `calculate_met_calorie_burn(body_weight_kg, duration_minutes, focus, days_per_week)`: Computes exact per-session and projected monthly caloric burn using MET (Metabolic Equivalent of Task) formulas:
  $$\text{Calories Burned} = \text{Duration (hours)} \times \text{MET} \times \text{Body Weight (kg)}$$

### 5. Secure Python Code Sandbox (`AgentEngineSandboxCodeExecutor`)
- Powered by Vertex AI Agent Engine code execution sandbox environments.
- Allows the agent to dynamically execute Python scripts for complex workout volume calculations, nonlinear fatigue simulations, and custom caloric projection curves.

### 6. Workout Visual Generation & Cloud Storage
- `generate_workout_visual(prompt, tool_context)`: Generates visual workout milestone cards and diagrams using the `gemini-3.1-flash-lite-image` model on Vertex AI (`global` region).
- **Playground Artifacts:** Persists images locally via `tool_context.save_artifact` for display in the ADK Playground.
- **Public Cloud Storage:** Uploads the raw image bytes to a public Google Cloud Storage bucket (`fittrack-agent-assets-grl29g`) and returns a shareable HTTPS URL.

### 7. Conversational Chat Frontend
- A lightweight FastAPI proxy and HTML/CSS/JS frontend inside `frontend/` that speaks the A2A protocol.
- Renders conversational replies and includes a native client-side renderer for A2UI components (Cards, Columns, Rows, Lists, Images).

> **Note on planned vs. implemented features:**  
> Cloud Trace latency tracing and interactive UI modal forms from the initial concept brief are planned future enhancements and not currently implemented in the codebase.

---

## Project Structure

```
├── agents-cli-manifest.yaml   # Agent runtime manifest
├── app/
│   ├── __init__.py
│   └── agent.py               # Root agent, tools, callbacks, and sandbox executor
├── frontend/
│   ├── main.py                # FastAPI proxy communicating over A2A
│   ├── requirements.txt       # Frontend dependencies
│   └── static/
│       └── index.html         # FitTrack AI branded chat interface & A2UI renderer
├── pyproject.toml             # Python dependencies and agent package configuration
├── seed_firestore.py          # Seeding script for foundational exercise catalog
└── deployment_metadata.json   # Deployed Agent Runtime tracking metadata
```

---

## Local Setup & Run Instructions

### Prerequisites
- Python 3.11+
- `uv` package manager or standard `pip`
- Google Cloud SDK (`gcloud`) authenticated with Application Default Credentials (`gcloud auth application-default login`)

### 1. Run the Agent Playground Locally
Start the local ADK Web development server with long-term memory attached:

```bash
cd fittrack-agent
uv run adk web . --port 8080 --reload_agents --memory_service_uri=agentengine://<AGENT_ENGINE_ID>
```

### 2. Run the Custom Chat Frontend Locally
Open a separate terminal window to launch the FastAPI chat proxy and web interface:

```bash
cd fittrack-agent/frontend

# Install dependencies
pip install -r requirements.txt

# Export required environment variables
export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_ID>/locations/<REGION>/reasoningEngines/<AGENT_ENGINE_ID>"
export AGENT_DIRECTORY="app"

# Start the server
python main.py
```
Open your browser to the local address displayed in the console to chat with FitTrack AI.
