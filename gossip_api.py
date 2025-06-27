from flask import Flask, request, jsonify
import os
import json
import hashlib
from collections import defaultdict

app = Flask(__name__)

# Ensure required directories exist
os.makedirs("stories", exist_ok=True)
os.makedirs("milestones", exist_ok=True)

# -------------------------------
# In-memory story tracking
# -------------------------------
stories = {}
relationships = defaultdict(lambda: defaultdict(str))

# -------------------------------
# Persistence Helpers
# -------------------------------
def load_story_from_disk(story_id):
    try:
        with open(f"stories/{story_id}.json", "r") as f:
            stories[story_id] = json.load(f)
            print(f"[DEBUG] Reloaded {story_id} from disk")
            return True
    except Exception as e:
        print(f"[ERROR] Could not load {story_id}: {e}")
        return False

def save_story_to_disk(story_id):
    try:
        with open(f"stories/{story_id}.json", "w") as f:
            json.dump(stories[story_id], f)
    except Exception as e:
        print(f"[ERROR] Could not save {story_id}: {e}")

# Auto-load all stories from disk
for filename in os.listdir("stories"):
    if filename.endswith(".json"):
        story_id = filename[:-5]
        load_story_from_disk(story_id)

# -------------------------------
# Canon rules
# -------------------------------
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

# -------------------------------
# Character Profiles
# -------------------------------
character_aliases = {
    "serena": "serena", "blair": "blair", "chuck": "chuck", "charles": "chuck",
    "lily": "lily", "niklaus": "niklaus", "nik": "niklaus", "klaus": "niklaus",
    "noah": "noah", "dan": "dan", "daniel": "dan", "vivian": "vivian"
}

characters = {
    "serena": {
        "name": "Serena van der Woodsen",
        "personality": "Warm, magnetic, laid-back, spontaneous, and emotionally intuitive.",
        "voiceTraits": ["Light but emotionally weighted", "Charismatic", "Playful subtext"],
        "relationships": {
            "blair": "Best friend, rival",
            "dan": "Ex-husband",
            "chuck": "Adoptive brother",
            "lily": "Mother",
            "william": "Father",
            "noah": "Romantic partner"
        },
        "speechStyle": "Witty, soft, unfiltered, emotionally immediate."
    },
    "blair": {
        "name": "Blair Waldorf",
        "personality": "Ambitious, strategic, fashion-forward, sharp-tongued.",
        "voiceTraits": ["Witty", "Poised", "Emotionally barbed"],
        "relationships": {
            "serena": "Best friend and rival",
            "chuck": "Husband",
            "eleanor": "Mother"
        },
        "speechStyle": "Elegant, biting, performative."
    },
    "noah": {
        "name": "Noah von Wolfram",
        "personality": "Disciplined, exacting, emotionally reserved, and logical.",
        "voiceTraits": ["Dry wit", "Minimalist", "Introspective"],
        "relationships": {
            "serena": "Romantic partner",
            "otto": "Father",
            "niklaus": "Cousin"
        },
        "speechStyle": "Minimal, deliberate."
    },
    "niklaus": {
        "name": "Niklaus von Wolfram",
        "personality": "F1 driver and architect. Brilliant, sensual, emotionally complex.",
        "voiceTraits": ["Quiet intensity", "Boyish charm", "European polish"],
        "relationships": {
            "noah": "Cousin",
            "otto": "Uncle",
            "vivian": "Half-sister"
        },
        "speechStyle": "Clipped, intelligent, formal with subtext."
    },
    "vivian": {
        "name": "Vivian Taylor",
        "personality": "British wit, glamorous, sardonic. Emotionally guarded.",
        "voiceTraits": ["Sardonic", "Charismatic", "Complex"],
        "relationships": {
            "niklaus": "Half-brother",
            "noah": "Half-cousin"
        },
        "speechStyle": "Elegant, sharp, ironic."
    },
    "lily": {
        "name": "Lily van der Woodsen",
        "personality": "Elegant, composed, maternal. Privately conflicted.",
        "voiceTraits": ["Sincere", "Polished", "Resilient"],
        "relationships": {
            "serena": "Daughter",
            "chuck": "Adoptive son"
        },
        "speechStyle": "Measured, warm, restrained."
    },
    "chuck": {
        "name": "Chuck Bass",
        "personality": "Darkly romantic, intelligent, controlled. Deeply loyal.",
        "voiceTraits": ["Seductive", "Calculated", "Emotionally charged"],
        "relationships": {
            "blair": "Wife",
            "serena": "Adoptive sister",
            "lily": "Adoptive mother"
        },
        "speechStyle": "Low, deliberate, suggestive."
    }
}
characters_data = characters  # alias for prompt generator

# -------------------------------
# Routes
# -------------------------------
@app.route("/", methods=["GET"])
def home():
    return "Gossip Girl Storytelling API is running!"

@app.route("/canon-rules", methods=["GET"])
def get_canon_rules():
    return jsonify({"rules": canon_rules})

@app.route("/characters/<name>", methods=["GET"])
def get_character_profile(name):
    key = name.lower()
    true_key = character_aliases.get(key)
    if not true_key:
        return jsonify({"error": "Character not found"}), 404
    return jsonify(characters[true_key])

@app.route("/relationships/<character>", methods=["GET"])
def get_relationships(character):
    character = character.lower()
    return jsonify({"relationships": relationships.get(character, {})})

@app.route("/stories", methods=["GET"])
def list_stories():
    return jsonify({
        "stories": [
            {
                "id": sid,
                "title": s["title"],
                "characters": s["characters"],
                "events": len(s["events"])
            }
            for sid, s in stories.items()
        ]
    })

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
    save_story_to_disk(story_id)
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
        if not load_story_from_disk(story_id):
            return jsonify({"error": "Story not found"}), 404

    stories[story_id]["events"].append(data)
    save_story_to_disk(story_id)

    # Auto-log milestone-worthy
    if is_milestone_worthy(scene_text) and not already_logged(story_id, scene_text):
        milestone = {
            "scene": scene_text,
            "characters": char_list,
            "emotions": emotion_map,
            "hash": hashlib.md5(scene_text.strip().encode()).hexdigest(),
            "source": "auto"
        }
        with open(os.path.join("milestones", f"{story_id}.json"), "a") as f:
            f.write(json.dumps(milestone) + "\n")

    # Update relationship graph
    for i, c1 in enumerate(char_list):
        for c2 in char_list[i+1:]:
            emotional_context = emotion_map.get(c1) or emotion_map.get(c2) or "interacted"
            prev = relationships[c1][c2]
            if emotional_context and emotional_context not in prev:
                relationships[c1][c2] += f"{emotional_context}, "

    return jsonify({"status": "event added"})

@app.route("/story/<story_id>/summary", methods=["GET"])
def get_summary(story_id):
    if story_id not in stories:
        if not load_story_from_disk(story_id):
            return jsonify({"error": "Story not found"}), 404
    story = stories[story_id]
    summary = " ".join(e["sceneText"] for e in story.get("events", []))[:500]
    return jsonify({
        "summary": summary,
        "majorEvents": [e["sceneText"][:60] for e in story.get("events", [])]
    })

@app.route("/story/<story_id>/fork", methods=["POST"])
def fork_story(story_id):
    if story_id not in stories:
        if not load_story_from_disk(story_id):
            return jsonify({"error": "Source story not found"}), 404

    new_id = f"story-{len(stories)+1}"
    stories[new_id] = {
        "title": stories[story_id]["title"] + " (Fork)",
        "characters": stories[story_id]["characters"],
        "events": list(stories[story_id]["events"]),
        "summary": stories[story_id]["summary"],
        "forkedFrom": story_id
    }
    save_story_to_disk(new_id)
    return jsonify({"forkedId": new_id})

@app.route("/story/<story_id>/restart", methods=["POST"])
def restart_story(story_id):
    if story_id not in stories:
        if not load_story_from_disk(story_id):
            return jsonify({"error": "Story not found"}), 404
    stories[story_id]["events"] = []
    stories[story_id]["summary"] = ""
    save_story_to_disk(story_id)
    return jsonify({"status": f"{story_id} restarted, milestones retained"})

@app.route("/story/<story_id>", methods=["DELETE"])
def delete_story(story_id):
    stories.pop(story_id, None)
    os.remove(os.path.join("stories", f"{story_id}.json")) if os.path.exists(os.path.join("stories", f"{story_id}.json")) else None
    os.remove(os.path.join("milestones", f"{story_id}.json")) if os.path.exists(os.path.join("milestones", f"{story_id}.json")) else None
    return jsonify({"status": f"{story_id} deleted"})

@app.route("/milestones/<story_id>", methods=["GET"])
def view_milestones(story_id):
    path = os.path.join("milestones", f"{story_id}.json")
    if not os.path.exists(path):
        return jsonify({"milestones": []})
    with open(path, "r") as f:
        return jsonify({"milestones": [json.loads(line) for line in f]})

@app.route("/milestones/<story_id>", methods=["POST"])
def save_milestone(story_id):
    data = request.json
    path = os.path.join("milestones", f"{story_id}.json")
    with open(path, "a") as f:
        f.write(json.dumps(data) + "\n")
    return jsonify({"status": "milestone saved"})

@app.route("/generate-prompt/<story_id>", methods=["GET"])
def generate_prompt(story_id):
    if story_id not in stories:
        if not load_story_from_disk(story_id):
            return jsonify({"error": "Story not found"}), 404

    story = stories[story_id]
    title = story.get("title", "Untitled Story")
    characters = story.get("characters", [])
    events = story.get("events", [])
    summary = story.get("summary", "")

    # Load recent milestone if exists
    milestone_path = os.path.join("milestones", f"{story_id}.json")
    recent_milestones = []
    if os.path.exists(milestone_path):
        with open(milestone_path, "r") as f:
            all_milestones = [json.loads(line) for line in f]
            recent_milestones = all_milestones[-3:]

    recent_events = [e["sceneText"] for e in events[-2:]] if not recent_milestones else []

    prompt_lines = [
        "GOSSIP GIRL CONTINUATION — SERIALIZED CANON FORMAT",
        "",
        f"Title: {title}",
        "",
        "Main Characters:",
        *[f"{characters_data[c]['name']}: {characters_data[c]['personality']}" for c in characters if c in characters_data],
        "",
        "Story Summary:",
        summary or "No summary saved.",
        "",
        "Recent Milestones:" if recent_milestones else "Recent Events:",
        *(f"- {m['scene'][:280]}..." for m in recent_milestones) if recent_milestones else (f"- {e[:280]}..." for e in recent_events),
        "",
        "Continue the scene or provide dramatic story options that build on this context:"
    ]

    return jsonify({"prompt": "\n".join(prompt_lines)})

# -------------------------------
# Utility Functions
# -------------------------------
def is_milestone_worthy(text):
    text = text.lower()
    return any(kw in text for kw in [
        "i love you", "i’m pregnant", "we broke up", "move in", "divorced",
        "engaged", "kissed", "cried", "birthday", "met gala", "stormed out",
        "confession", "in labor", "he proposed", "she said yes", "got married"
    ])

def already_logged(story_id, scene_text):
    path = os.path.join("milestones", f"{story_id}.json")
    hash_value = hashlib.md5(scene_text.strip().encode()).hexdigest()
    if not os.path.exists(path):
        return False
    with open(path, "r") as f:
        return any(json.loads(line).get("hash") == hash_value for line in f)

# -------------------------------
# Run the Server
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
