from flask import Flask, request, jsonify
import os
import json
import hashlib
from collections import defaultdict
import libsql_client

app = Flask(__name__)

# Turso DB setup
TURSO_URL = os.getenv("TURSO_URL")
TURSO_TOKEN = os.getenv("TURSO_TOKEN")

print("🔍 TURSO_URL =", TURSO_URL)
print("🔍 TURSO_TOKEN =", TURSO_TOKEN[:10] + "..." if TURSO_TOKEN else "MISSING")


conn = libsql_client.create_client_sync(
    url=os.getenv("TURSO_URL"),
    auth_token=os.getenv("TURSO_TOKEN")
)


# --- Create tables if they don't exist ---
conn.execute("""
    CREATE TABLE IF NOT EXISTS stories (
        id TEXT PRIMARY KEY,
        data TEXT
    )
""")

conn.execute("""
    CREATE TABLE IF NOT EXISTS milestones (
        story_id TEXT,
        data TEXT
    )
""")

conn.execute("""
    CREATE TABLE IF NOT EXISTS characters (
        id TEXT PRIMARY KEY,
        data TEXT
    )
""")

# ---------------------------
# In-memory cache
# ---------------------------
stories = {}
relationships = defaultdict(lambda: defaultdict(str))

# Load all stories into memory
def load_all_stories():
    result = conn.execute("SELECT id, data FROM stories")
    for row in result.rows:
        stories[row["id"]] = json.loads(row["data"])

load_all_stories()

# ---------------------------
# DB Persistence Helpers
# ---------------------------
def load_story_from_db(story_id):
    result = conn.execute("SELECT data FROM stories WHERE id = ?", [story_id])
    if not result.rows:
        return False
    stories[story_id] = json.loads(result.rows[0]["data"])
    return True

def save_story_to_db(story_id):
    conn.execute(
        "INSERT OR REPLACE INTO stories (id, data) VALUES (?, ?)",
        [story_id, json.dumps(stories[story_id])]
    )

def save_milestone_to_db(story_id, milestone_data):
    conn.execute(
        "INSERT INTO milestones (story_id, data) VALUES (?, ?)",
        [story_id, json.dumps(milestone_data)]
    )

def get_milestones(story_id):
    result = conn.execute("SELECT data FROM milestones WHERE story_id = ?", [story_id])
    return [json.loads(row["data"]) for row in result.rows]

def save_character_to_db(character_id, data):
    conn.execute(
        "INSERT OR REPLACE INTO characters (id, data) VALUES (?, ?)",
        [character_id, json.dumps(data)]
    )

def get_character_from_db(character_id):
    result = conn.execute("SELECT data FROM characters WHERE id = ?", [character_id])
    return json.loads(result.rows[0]["data"]) if result.rows else None

def list_all_characters():
    result = conn.execute("SELECT id, data FROM characters")
    return {row["id"]: json.loads(row["data"]) for row in result.rows}

# ---------------------------
# Canon & Characters Setup
# ---------------------------
canon_rules = [
    "Gossip Girl's narration ended in Season 6 finale. Dan was revealed as Gossip Girl.",
    "Chuck and Blair are married and have a son, Henry.",
    "Chuck was legally adopted by Lily van der Woodsen during her marriage to Bart Bass.",
    "Serena is the daughter of Lily and William. Her brother is Eric.",
    "Lily and William were shown together in the finale, suggesting remarriage.",
    "Chuck and Serena are adoptive siblings. Their relationship is loyal and emotionally bonded.",
    "Niklaus Von Wolfram is not romantically involved with Serena by default. All intimacy must be earned narratively.",
    "Narrative voice must be third-person limited, elevated, and emotionally nuanced.",
    "No meta-commentary, fanfic tropes, or anachronisms unless in AU mode.",
    "Each option must dramatize change, emotion, or truth—not simply offer filler or directionless choices.",
    "Do not pre-load romantic intimacy unless canon or established in-story."
]

character_aliases = {
    "serena": "serena", "serena van der woodsen": "serena",
    "blair": "blair", "blair waldorf": "blair", "blair waldorf bass": "blair",
    "chuck": "chuck", "charles": "chuck", "chuck bass": "chuck",
    "lily": "lily", "lily van der woodsen": "lily", "lily bass": "lily", "lily rhodes": "lily",
    "niklaus": "niklaus", "nik": "niklaus", "klaus": "niklaus", "niklaus von wolfram": "niklaus",
    "noah": "noah", "noah von wolfram": "noah",
    "dan": "dan", "daniel": "dan", "dan humphrey": "dan",
    "vivian": "vivian", "vivian taylor": "vivian"
}

# -------------------------------
# Canonical Character Profiles
# -------------------------------
canonical_characters = {
    "serena": {
        "name": "Serena van der Woodsen",
        "personality": "Warm, magnetic, laid-back, spontaneous, and emotionally intuitive.",
        "voiceTraits": ["Light but emotionally weighted", "Charismatic", "Playful subtext"],
        "relationships": {
            "blair": "Best friend, rival", "dan": "Ex-husband", "chuck": "Adoptive brother",
            "lily": "Mother", "william": "Father", "noah": "Romantic partner"
        },
        "speechStyle": "Witty, soft, unfiltered, emotionally immediate."
    },
    "blair": {
        "name": "Blair Waldorf",
        "personality": "Ambitious, strategic, fashion-forward, sharp-tongued.",
        "voiceTraits": ["Witty", "Poised", "Emotionally barbed"],
        "relationships": {
            "serena": "Best friend and rival", "chuck": "Husband", "eleanor": "Mother"
        },
        "speechStyle": "Elegant, biting, performative."
    },
    "noah": {
        "name": "Noah von Wolfram",
        "personality": "Disciplined, exacting, emotionally reserved, and logical.",
        "voiceTraits": ["Dry wit", "Minimalist", "Introspective"],
        "relationships": {
            "serena": "Romantic partner", "otto": "Father", "niklaus": "Cousin"
        },
        "speechStyle": "Minimal, deliberate."
    },
    "niklaus": {
        "name": "Niklaus von Wolfram",
        "personality": "F1 driver and architect. Brilliant, sensual, emotionally complex.",
        "voiceTraits": ["Quiet intensity", "Boyish charm", "European polish"],
        "relationships": {
            "noah": "Cousin", "otto": "Uncle", "vivian": "Half-sister"
        },
        "speechStyle": "Clipped, intelligent, formal with subtext."
    },
    "vivian": {
        "name": "Vivian Taylor",
        "personality": "British wit, glamorous, sardonic. Emotionally guarded.",
        "voiceTraits": ["Sardonic", "Charismatic", "Complex"],
        "relationships": {
            "niklaus": "Half-brother", "noah": "Half-cousin"
        },
        "speechStyle": "Elegant, sharp, ironic."
    },
    "lily": {
        "name": "Lily van der Woodsen",
        "personality": "Elegant, composed, maternal. Privately conflicted.",
        "voiceTraits": ["Sincere", "Polished", "Resilient"],
        "relationships": {
            "serena": "Daughter", "chuck": "Adoptive son"
        },
        "speechStyle": "Measured, warm, restrained."
    },
    "chuck": {
        "name": "Chuck Bass",
        "personality": "Darkly romantic, intelligent, controlled. Deeply loyal.",
        "voiceTraits": ["Seductive", "Calculated", "Emotionally charged"],
        "relationships": {
            "blair": "Wife", "serena": "Adoptive sister", "lily": "Adoptive mother"
        },
        "speechStyle": "Low, deliberate, suggestive."
    }
}

# --- Inject characters into Turso DB if not already there ---
def ensure_characters_exist():
    existing = list_all_characters()
    for cid in canonical_characters:
        if cid not in existing:
            save_character_to_db(cid, canonical_characters[cid])

ensure_characters_exist()  # ✅ This must be called after canonical_characters

# -------------------------------
# Routes
# -------------------------------
@app.route("/", methods=["GET"])
def home():
    return "Gossip Girl API with Turso storage is running."

@app.route("/canon-rules", methods=["GET"])
def get_canon_rules():
    return jsonify({"rules": canon_rules})

@app.route("/characters", methods=["GET"])
def get_characters():
    return jsonify(list_all_characters())

@app.route("/characters/<name>", methods=["GET"])
def get_character(name):
    key = character_aliases.get(name.lower())
    if not key:
        return jsonify({"error": "Character not found"}), 404
    character = get_character_from_db(key)
    if not character:
        return jsonify({"error": "Character not found in DB"}), 404
    return jsonify(character)

@app.route("/characters/<name>", methods=["POST"])
def create_or_update_character(name):
    data = request.json
    save_character_to_db(name.lower(), data)
    return jsonify({"status": f"{name} saved"})

@app.route("/stories", methods=["GET"])
def list_stories():
    return jsonify([
        {
            "id": sid,
            "title": s["title"],
            "characters": s["characters"],
            "events": len(s["events"])
        }
        for sid, s in stories.items()
    ])

@app.route("/story", methods=["POST"])
def create_story():
    data = request.json
    story_id = f"story-{len(stories)+1}"
    stories[story_id] = {
        "title": data["title"],
        "characters": data["characters"],
        "events": [],
        "summary": ""
    }
    save_story_to_db(story_id)
    return jsonify({"storyId": story_id})

@app.route("/story/<story_id>/events", methods=["POST"])
def add_event(story_id):
    data = request.json or {}
    scene_text = data.get("sceneText", "")
    char_list = data.get("charactersInScene", [])
    emotion_map = data.get("emotions", {})

    if not scene_text:
        return jsonify({"error": "sceneText is required"}), 400

    if story_id not in stories:
        if not load_story_from_db(story_id):
            return jsonify({"error": "Story not found"}), 404

    stories[story_id]["events"].append(data)
    save_story_to_db(story_id)

    if is_milestone_worthy(scene_text) and not already_logged(story_id, scene_text):
        milestone = {
            "scene": scene_text,
            "characters": char_list,
            "emotions": emotion_map,
            "hash": hashlib.md5(scene_text.strip().encode()).hexdigest(),
            "source": "auto"
        }
        save_milestone_to_db(story_id, milestone)

    return jsonify({"status": "event added"})

@app.route("/story/<story_id>/summary", methods=["GET"])
def get_summary(story_id):
    if story_id not in stories:
        if not load_story_from_db(story_id):
            return jsonify({"error": "Story not found"}), 404
    story = stories[story_id]
    summary = " ".join(e["sceneText"] for e in story.get("events", []))[:500]
    return jsonify({
        "summary": summary,
        "majorEvents": [e["sceneText"][:60] for e in story.get("events", [])]
    })

@app.route("/story/<story_id>/events", methods=["GET"])
def get_all_events(story_id):
    if story_id not in stories:
        if not load_story_from_db(story_id):
            return jsonify({"error": "Story not found"}), 404
    return jsonify(stories[story_id].get("events", []))

@app.route("/milestones/<story_id>", methods=["GET"])
def view_milestones(story_id):
    return jsonify({"milestones": get_milestones(story_id)})

@app.route("/milestones/<story_id>", methods=["POST"])
def save_manual_milestone(story_id):
    data = request.json
    data["hash"] = hashlib.md5(data.get("scene", "").strip().encode()).hexdigest()
    data["source"] = "manual"
    save_milestone_to_db(story_id, data)
    return jsonify({"status": "milestone saved"})

@app.route("/story/<story_id>/fork", methods=["POST"])
def fork_story(story_id):
    if story_id not in stories:
        if not load_story_from_db(story_id):
            return jsonify({"error": "Source story not found"}), 404

    new_id = f"story-{len(stories)+1}"
    stories[new_id] = {
        "title": stories[story_id]["title"] + " (Fork)",
        "characters": stories[story_id]["characters"],
        "events": list(stories[story_id]["events"]),
        "summary": stories[story_id]["summary"],
        "forkedFrom": story_id
    }
    save_story_to_db(new_id)
    return jsonify({"forkedId": new_id})

@app.route("/story/<story_id>", methods=["DELETE"])
def delete_story(story_id):
    stories.pop(story_id, None)
    conn.execute("DELETE FROM stories WHERE id = ?", [story_id])
    conn.execute("DELETE FROM milestones WHERE story_id = ?", [story_id])
    return jsonify({"status": f"{story_id} deleted"})

@app.route("/reset-characters", methods=["POST"])
def reset_characters():
    for char_id, profile in canonical_characters.items():
        save_character_to_db(char_id, profile)
    return jsonify({"status": "Canonical characters injected into DB."})


# -------------------------------
# Helpers
# -------------------------------
def is_milestone_worthy(text):
    text = text.lower()
    return any(kw in text for kw in [
        "i love you", "i’m pregnant", "we broke up", "move in", "divorced",
        "engaged", "kissed", "cried", "birthday", "met gala", "stormed out",
        "confession", "in labor", "he proposed", "she said yes", "got married"
    ])

def already_logged(story_id, scene_text):
    hash_value = hashlib.md5(scene_text.strip().encode()).hexdigest()
    milestones = get_milestones(story_id)
    return any(m["hash"] == hash_value for m in milestones)

# -------------------------------
# Server Launch
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
