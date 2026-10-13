"""Seed script for FitTrack exercises catalog in Firestore."""
from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-622ab1b5b604"

SEED_EXERCISES = [
    {
        "id": "barbell-bench-press",
        "name": "Barbell Bench Press",
        "primary_muscle": "Chest",
        "secondary_muscles": ["Triceps", "Anterior Deltoids"],
        "equipment": "Barbell & Bench",
        "focus_recommendations": {
            "bulking": {"sets": 4, "reps": "6-8", "rest_sec": 120},
            "endurance": {"sets": 3, "reps": "15-20", "rest_sec": 45}
        },
        "met_value": 6.0,
        "instructions": "Lie on bench, grip barbell slightly wider than shoulder width, lower bar to mid-chest, press up to lockout."
    },
    {
        "id": "barbell-back-squat",
        "name": "Barbell Back Squat",
        "primary_muscle": "Quadriceps",
        "secondary_muscles": ["Glutes", "Hamstrings", "Core"],
        "equipment": "Barbell & Squat Rack",
        "focus_recommendations": {
            "bulking": {"sets": 4, "reps": "6-8", "rest_sec": 150},
            "endurance": {"sets": 4, "reps": "15-25", "rest_sec": 60}
        },
        "met_value": 7.5,
        "instructions": "Rest bar on upper back, feet shoulder-width apart, descend until thighs parallel ground, drive through heels."
    },
    {
        "id": "conventional-deadlift",
        "name": "Conventional Deadlift",
        "primary_muscle": "Posterior Chain (Hamstrings & Lower Back)",
        "secondary_muscles": ["Glutes", "Lats", "Traps", "Forearms"],
        "equipment": "Barbell & Plates",
        "focus_recommendations": {
            "bulking": {"sets": 3, "reps": "5", "rest_sec": 180},
            "endurance": {"sets": 3, "reps": "12-15", "rest_sec": 60}
        },
        "met_value": 8.0,
        "instructions": "Hinge at hips, grip bar with neutral spine, push the floor away, lockout hips at top."
    },
    {
        "id": "pull-ups",
        "name": "Pull-Ups",
        "primary_muscle": "Back (Lats)",
        "secondary_muscles": ["Biceps", "Rear Deltoids", "Core"],
        "equipment": "Pull-Up Bar",
        "focus_recommendations": {
            "bulking": {"sets": 4, "reps": "6-10 (weighted if possible)", "rest_sec": 90},
            "endurance": {"sets": 3, "reps": "15-20 or max reps", "rest_sec": 45}
        },
        "met_value": 6.5,
        "instructions": "Overhand grip wider than shoulders, pull chest to the bar by engaging lats, lower under full control."
    },
    {
        "id": "overhead-shoulder-press",
        "name": "Overhead Barbell Shoulder Press",
        "primary_muscle": "Shoulders (Deltoids)",
        "secondary_muscles": ["Triceps", "Upper Chest", "Core"],
        "equipment": "Barbell",
        "focus_recommendations": {
            "bulking": {"sets": 4, "reps": "6-8", "rest_sec": 120},
            "endurance": {"sets": 3, "reps": "15", "rest_sec": 45}
        },
        "met_value": 5.5,
        "instructions": "Stand tall with bar at collarbone height, press straight overhead locking elbows, lower smoothly."
    },
    {
        "id": "kettlebell-swings",
        "name": "Kettlebell Swings",
        "primary_muscle": "Glutes & Hamstrings",
        "secondary_muscles": ["Core", "Shoulders", "Cardiovascular"],
        "equipment": "Kettlebell",
        "focus_recommendations": {
            "bulking": {"sets": 3, "reps": "10-12 (heavy)", "rest_sec": 60},
            "endurance": {"sets": 5, "reps": "25-30", "rest_sec": 30}
        },
        "met_value": 8.5,
        "instructions": "Hinge hips back keeping flat back, explosively snap hips forward to swing bell to chest level."
    }
]

def seed():
    print(f"Connecting to Firestore for project: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)
    collection = db.collection("exercises")
    
    for item in SEED_EXERCISES:
        doc_id = item["id"]
        doc_ref = collection.document(doc_id)
        doc_ref.set(item)
        print(f"Seeded: {doc_id} -> {item['name']}")
        
    print("Seeding complete! Successfully added exercises.")

if __name__ == "__main__":
    seed()
