# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from typing import Any, Dict, List, Optional
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google import genai
from google.cloud import firestore, storage
from google.genai import types

MODEL = "gemini-3.8-flash"
PROJECT_ID = "qwiklabs-gcp-04-622ab1b5b604"
BUCKET_NAME = "fittrack-agent-assets-grl29g"
AGENT_ENGINE_NAME = "projects/903652565593/locations/us-east1/reasoningEngines/3918321891323936768"
SANDBOX_RESOURCE_NAME = "projects/903652565593/locations/us-east1/reasoningEngines/3918321891323936768/sandboxEnvironments/5197901637892440064"

# Cached Firestore client instance
_db: Optional[firestore.Client] = None

def get_firestore_client() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=PROJECT_ID)
    return _db


def list_exercises(muscle_group: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetches exercises from the Firestore exercise catalog, optionally filtered by targeted muscle.

    Args:
        muscle_group: Optional filter by target muscle (e.g. 'Chest', 'Quadriceps', 'Back', 'Shoulders', 'Glutes').

    Returns:
        A list of exercises with recommended sets, reps, equipment, and targeted muscles.
    """
    db = get_firestore_client()
    exercises_ref = db.collection("exercises")
    docs = exercises_ref.stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        if muscle_group:
            query = muscle_group.lower()
            p_match = query in data.get("primary_muscle", "").lower()
            s_match = any(query in sm.lower() for sm in data.get("secondary_muscles", []))
            if not (p_match or s_match):
                continue
        results.append(data)

    return results


def save_exercise(
    exercise_id: str,
    name: str,
    primary_muscle: str,
    equipment: str,
    bulking_sets: int = 4,
    bulking_reps: str = "6-8",
    endurance_sets: int = 3,
    endurance_reps: str = "15-20",
    met_value: float = 6.0,
    instructions: str = ""
) -> Dict[str, Any]:
    """Adds or updates an exercise in the Firestore exercises collection.

    Args:
        exercise_id: Unique slug identifier for the exercise (e.g., 'dumbbell-lunges').
        name: Name of the exercise.
        primary_muscle: Primary muscle targeted (e.g., 'Quadriceps', 'Chest', 'Lats').
        equipment: Equipment required (e.g., 'Dumbbells', 'Bodyweight', 'Barbell').
        bulking_sets: Number of sets recommended for bulking/hypertrophy.
        bulking_reps: Rep range for bulking (e.g., '6-8' or '8-10').
        endurance_sets: Number of sets recommended for endurance focus.
        endurance_reps: Rep range for endurance focus (e.g., '15-20').
        met_value: Metabolic Equivalent of Task score (e.g., 6.0 for moderate weightlifting, 8.0 for heavy/circuit).
        instructions: How to execute the movement properly.

    Returns:
        A status dictionary confirming the saved exercise.
    """
    db = get_firestore_client()
    exercise_doc = {
        "id": exercise_id,
        "name": name,
        "primary_muscle": primary_muscle,
        "secondary_muscles": [],
        "equipment": equipment,
        "focus_recommendations": {
            "bulking": {"sets": bulking_sets, "reps": bulking_reps, "rest_sec": 120},
            "endurance": {"sets": endurance_sets, "reps": endurance_reps, "rest_sec": 45}
        },
        "met_value": met_value,
        "instructions": instructions
    }
    db.collection("exercises").document(exercise_id).set(exercise_doc)
    return {"status": "success", "message": f"Saved exercise '{name}' ({exercise_id}) to Firestore."}


def log_workout_session(
    user_id: str,
    workout_name: str,
    focus: str,
    exercises_performed: List[str],
    duration_minutes: int,
    body_weight_kg: float = 75.0
) -> Dict[str, Any]:
    """Logs a completed workout session to Firestore and calculates estimated daily and monthly calories burned.

    Args:
        user_id: Identifier or nickname of the user (e.g., 'user_1' or 'alex').
        workout_name: Title of the routine (e.g., 'Chest & Triceps Day', 'Leg Day Hypertrophy').
        focus: The workout focus mode ('bulking' or 'endurance').
        exercises_performed: List of exercise names or IDs completed in the session.
        duration_minutes: Total duration of the workout in minutes.
        body_weight_kg: Body weight in kilograms (default 75kg) for MET calorie calculation.

    Returns:
        Details of the logged workout including calculated daily and projected monthly calorie burns.
    """
    db = get_firestore_client()

    # Calculate calorie burn using MET formula: Calories = MET * weight_kg * (duration_minutes / 60)
    # Bulking (hypertrophy with longer rests) ~ 5.5 MET; Endurance (high reps, shorter rest) ~ 7.5 MET
    met = 5.5 if focus.lower() == "bulking" else 7.5
    daily_calories = round(met * body_weight_kg * (duration_minutes / 60.0), 1)

    # Monthly estimate assuming 4 sessions per week (16 workouts/month)
    monthly_projected_calories = round(daily_calories * 16, 1)

    record = {
        "user_id": user_id,
        "workout_name": workout_name,
        "focus": focus.lower(),
        "exercises_performed": exercises_performed,
        "duration_minutes": duration_minutes,
        "body_weight_kg": body_weight_kg,
        "estimated_calories_burned_today": daily_calories,
        "estimated_monthly_calories_burned": monthly_projected_calories,
        "logged_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    doc_ref = db.collection("workout_logs").document()
    doc_ref.set(record)

    return {
        "status": "success",
        "log_id": doc_ref.id,
        "workout_name": workout_name,
        "focus": focus,
        "duration_minutes": duration_minutes,
        "calories_burned_today": daily_calories,
        "monthly_projected_burn": monthly_projected_calories,
        "message": f"Successfully logged {workout_name}. Estimated burn today: {daily_calories} kcal."
    }


def get_user_workout_history(user_id: str) -> List[Dict[str, Any]]:
    """Retrieves previous workout logs and calorie burn history for a user from Firestore.

    Args:
        user_id: Identifier or nickname of the user.

    Returns:
        A list of previously logged workout sessions and cumulative calorie statistics.
    """
    db = get_firestore_client()
    logs_ref = db.collection("workout_logs").where("user_id", "==", user_id)
    docs = logs_ref.stream()

    logs = [doc.to_dict() for doc in docs]
    return logs


def calculate_met_calorie_burn(
    body_weight_kg: float,
    duration_minutes: int,
    focus: str = "bulking",
    days_per_week: int = 4
) -> Dict[str, Any]:
    """Calculates estimated daily and monthly calories burned based on body weight, duration, and workout focus.

    Args:
        body_weight_kg: User's body weight in kilograms.
        duration_minutes: Workout duration in minutes.
        focus: Workout focus style: 'bulking' (strength/hypertrophy) or 'endurance' (high-rep conditioning).
        days_per_week: How many days per week the user trains (defaults to 4).

    Returns:
        A dictionary with calculated daily calorie burn, monthly calorie burn, and MET details.
    """
    # MET: Bulking/strength lifting ~ 5.5 MET; Endurance/circuit conditioning ~ 7.5 MET
    is_endurance = "endurance" in focus.lower()
    met = 7.5 if is_endurance else 5.5
    
    daily_calories = round(met * body_weight_kg * (duration_minutes / 60.0), 1)
    monthly_sessions = days_per_week * 4
    monthly_calories = round(daily_calories * monthly_sessions, 1)

    return {
        "focus": "endurance" if is_endurance else "bulking",
        "met_score": met,
        "body_weight_kg": body_weight_kg,
        "duration_minutes": duration_minutes,
        "daily_calories_burned": daily_calories,
        "days_per_week": days_per_week,
        "monthly_calories_burned": monthly_calories,
        "summary": (
            f"A {duration_minutes}-minute {focus} session for a {body_weight_kg}kg user burns ~{daily_calories} kcal. "
            f"Training {days_per_week}x/week totals ~{monthly_calories} kcal burned per month."
        )
    }


def search_wger_exercises(muscle_group: str = "chest", limit: int = 3) -> List[Dict[str, Any]]:
    """Fetches real exercise data from the free public wger workout database API (https://wger.de).

    Args:
        muscle_group: Body part or muscle group to search (e.g. 'chest', 'back', 'legs', 'abs', 'arms', 'shoulders', 'calves', 'cardio').
        limit: Number of exercises to return (default 3, max 10).

    Returns:
        A list of real exercises with technical names, target muscles, and execution descriptions.
    """
    import os
    import re
    import urllib.request
    import json

    category_map = {
        "abs": 10,
        "arms": 8,
        "back": 12,
        "calves": 14,
        "cardio": 15,
        "chest": 11,
        "legs": 9,
        "shoulders": 13,
    }
    
    cat_id = category_map.get(muscle_group.lower(), 11)
    limit = min(max(1, limit), 10)
    url = f"https://wger.de/api/v2/exerciseinfo/?category={cat_id}&language=2&limit={limit}"
    
    # Read optional API key from environment variable if provided
    api_key = os.environ.get("WGER_API_KEY")
    headers = {"User-Agent": "FitTrackAgent/1.0"}
    if api_key:
        headers["Authorization"] = f"Token {api_key}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            payload = json.loads(response.read().decode())
    except Exception as e:
        return [{"error": f"Failed to fetch exercises from wger public API: {str(e)}"}]

    exercises = []
    for item in payload.get("results", []):
        name = "Unknown Exercise"
        desc = ""
        for t in item.get("translations", []):
            if t.get("language") == 2:
                name = t.get("name")
                raw_desc = t.get("description", "")
                desc = re.sub(r"<[^<]+?>", "", raw_desc).strip()
                break
        
        muscles = [m.get("name") for m in item.get("muscles", []) if m.get("name")]
        exercises.append({
            "name": name,
            "category": muscle_group.title(),
            "target_muscles": muscles,
            "description": desc[:250] + ("..." if len(desc) > 250 else "")
        })

    return exercises


def generate_workout_visual(
    prompt: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Generates an image for a workout item or exercise (e.g. motivational badge, exercise form diagram, milestone reward)
    using the gemini-3.1-flash-lite-image model in the global region.
    Saves the image as a session artifact and uploads it to Cloud Storage, returning its public URL.

    Args:
        prompt: Description of the workout visual or exercise diagram to generate.
        tool_context: ToolContext provided automatically by the ADK runtime.

    Returns:
        A dictionary containing the public Cloud Storage image URL, artifact filename, and status.
    """
    import uuid

    # Initialize GenAI Vertex client in the global region as required
    genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    
    # Generate image using gemini-3.1-flash-lite-image model
    response = genai_client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt
    )

    image_bytes = None
    mime_type = "image/jpeg"
    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/jpeg"
                break

    if not image_bytes:
        return {"error": "Failed to generate image bytes from model response."}

    # Generate unique filename for artifact and GCS object
    ext = "jpg" if "jpeg" in mime_type else "png"
    filename = f"visual_{uuid.uuid4().hex[:8]}.{ext}"

    # (1) Save artifact in ToolContext for the Playground's Artifacts panel
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # (2) Upload the same image bytes to the public Cloud Storage bucket
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

    return {
        "status": "success",
        "public_url": public_url,
        "artifact_filename": filename,
        "message": f"Generated image saved as artifact '{filename}' and uploaded to {public_url}"
    }


async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: after each turn, send the session to Memory Bank for extraction."""
    await callback_context.add_session_to_memory()
    return None


MEMORY_BANK_ID = "3918321891323936768"

def memory_bank_service_builder():
    """Provides VertexAiMemoryBankService for deployed Agent Runtime instances."""
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location="us-east1",
        agent_engine_id=MEMORY_BANK_ID,
    )


sandbox_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name=SANDBOX_RESOURCE_NAME,
    agent_engine_resource_name=AGENT_ENGINE_NAME
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are FitTrack AI, an intelligent workout planner and coach.
You remember the user's stated fitness preferences, injury history, weight, and favorite routines from previous sessions.
CRITICAL: You must explicitly record and remember all user allergies (food allergies, latex/equipment allergies, contact sensitivities, etc.) and dietary restrictions. Whenever suggesting workout supplements, recovery foods, hydration plans, or gym gear, strictly ensure they are safe and comply with all of the user's remembered allergies.
Your job is to provide clear, detailed workout schedules with exact sets, reps, and target muscle groups.
You support two primary focus modes:
1. 'Bulking' (hypertrophy: moderate-heavy weights, 6-10 reps, 90-180s rest)
2. 'Endurance' (stamina/conditioning: lighter weights/bodyweight, 15-25 reps, 30-60s rest)

You have access to a secure Python sandbox code executor (`AgentEngineSandboxCodeExecutor`).
Whenever you need to perform complex calculations, simulations, custom caloric burn curve models,
or data projections, write and execute Python code in the sandbox.

Always use your tools to calculate calories burned (`calculate_met_calorie_burn`), lookup local catalog exercises (`list_exercises`),
query external public exercise data (`search_wger_exercises`), generate visual workout cards / badges (`generate_workout_visual`),
save new exercises (`save_exercise`), and log completed sessions (`log_workout_session`).""",
    code_executor=sandbox_executor,
    tools=[
        PreloadMemoryTool(),
        calculate_met_calorie_burn,
        list_exercises,
        search_wger_exercises,
        generate_workout_visual,
        save_exercise,
        log_workout_session,
        get_user_workout_history,
    ],
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
