from flask import Flask, request, jsonify
import os
import json
import hashlib
from collections import defaultdict

app = Flask(__name__)

# -------------------------------
# In-memory story tracking
# -------------------------------
stories = {}
relationships = defaultdict(lambda: defaultdict(str))  # evolving relationship memory

@app.route("/", methods=["GET"])
def home():
    return "Gossip Girl Storytelling API is running!"

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
    return jsonify({"storyId": story_id})

@app.route("/story/<story_id>", methods=["DELETE"])
def delete_story(story_id):
    if story_id in stories:
        del stories[story_id]
        milestone_path = f"milestones/{story_id}.json"
        if os.path.exists(milestone_path):
            os.remove(milestone_path)
        return jsonify({"status": f"{story_id} deleted"})
    return jsonify({"error": "Story not found"}), 404

@app.route("/story/<story_id>/restart", methods=["POST"])
def restart_story(story_id):
    if story_id not in stories:
        return jsonify({"error": "Story not found"}), 404
    stories[story_id]["events"] = []
    stories[story_id]["summary"] = ""
    return jsonify({"status": f"{story_id} restarted, milestones retained"})

@app.route("/story/<story_id>/events", methods=["POST"])
def add_event(story_id):
    data = request.json
    scene_text = data.get("sceneText", "")
    char_list = data.get("charactersInScene", [])
    emotion_map = data.get("emotions", {})

    # Store the event
    stories[story_id]["events"].append(data)

    # Auto milestone logging
    if is_milestone_worthy(scene_text) and not already_logged(story_id, scene_text):
        milestone = {
            "scene": scene_text,
            "characters": char_list,
            "emotions": emotion_map,
            "hash": hashlib.md5(scene_text.strip().encode()).hexdigest(),
            "source": "auto"
        }
        with open(f"milestones/{story_id}.json", "a") as f:
            f.write(json.dumps(milestone) + "\n")

    # Auto-evolve relationships
    for i, c1 in enumerate(char_list):
        for c2 in char_list[i+1:]:
            emotional_context = emotion_map.get(c1) or emotion_map.get(c2) or "interacted"
            prev = relationships[c1][c2]
            if emotional_context and emotional_context not in prev:
                relationships[c1][c2] += f"{emotional_context}, "

    return jsonify({"status": "event added"})

@app.route("/story/<story_id>/summary", methods=["GET"])
def get_summary(story_id):
    story = stories.get(story_id, {})
    summary = " ".join(e["sceneText"] for e in story.get("events", []))[:500]
    return jsonify({
        "summary": summary,
        "majorEvents": [e["sceneText"][:60] for e in story.get("events", [])]
    })

@app.route("/relationships/<character>", methods=["GET"])
def get_relationships(character):
    character = character.lower()
    return jsonify({character: relationships.get(character, {})})

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

@app.route("/canon-rules", methods=["GET"])
def get_canon_rules():
    return jsonify({"rules": canon_rules})

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
        "personality": "Warm, magnetic, laid-back, spontaneous, and emotionally intuitive. Effortless charm. ESFP-like energy, but not driven by validation.",
        "voiceTraits": ["Light but emotionally weighted", "Charismatic", "Playful subtext", "Unfiltered elegance"],
        "relationships": {
            "blair": "Best friend, rival",
            "dan": "First love, husband (series finale)",
            "chuck": "Adoptive brother",
            "lily": "Mother",
            "william": "Father",
            "eric": "Younger brother",
            "noah": "Romantic partner"
        },
        "speechStyle": "uses wit, soft, emotionally immediate. Never rehearsed."
    },
    "noah": {
        "name": "Noah von Wolfram",
        "personality": "Disciplined, exacting, emotionally reserved, and fiercely logical. Prefers control and structure over unpredictability.",
        "voiceTraits": ["Dry wit", "Controlled", "Minimalist", "Introspective"],
        "relationships": {
            "serena": "Romantic partner",
            "otto": "Father",
            "niklaus": "Cousin",
            "vivian": "Half-cousin"
        },
        "speechStyle": "Minimal, calculated. Rarely expressive, but meaningful."
    },
    "niklaus": {
        "name": "Niklaus von Wolfram",
        "personality": "World champion F1 driver and architect. Brilliant, sensual, emotionally restrained. Boyish charm veils intense focus and integrity.",
        "voiceTraits": ["Dry, intelligent", "Quiet intensity", "Understated affection", "European formality"],
        "relationships": {
            "helena": "Mother; warm and close",
            "dietrich": "Father; mutual respect, high expectations",
            "otto": "Uncle; affectionate and playful",
            "vivian": "Half-sister; bonded",
            "noah": "Cousin; contrasts in temperament"
        },
        "speechStyle": "Elegant, clipped, powerful in brevity."
    },
    "blair": {
        "name": "Blair Waldorf",
        "personality": "Ambitious, strategic, fashion-forward, sharp-tongued. Privately vulnerable but fiercely self-controlled.",
        "voiceTraits": ["Witty", "Poised", "Emotionally barbed", "Controlled vulnerability"],
        "relationships": {
            "serena": "Best friend and rival",
            "chuck": "Husband, power couple",
            "eleanor": "Mother; approval-seeking dynamic",
            "lily": "Social ally, sometimes surrogate mother figure"
        },
        "speechStyle": "Ornate, biting, performative elegance."
    },
    "lily": {
        "name": "Lily van der Woodsen",
        "personality": "Elegant, composed, layered in regret and resilience. The matriarch in pearls.",
        "voiceTraits": ["Sincere", "Polished", "Soft-edged authority"],
        "relationships": {
            "serena": "Daughter",
            "eric": "Son",
            "chuck": "Adoptive son",
            "william": "Complicated romantic partner",
            "rufus": "Ex-husband"
        },
        "speechStyle": "Calm, maternal, slightly guarded."
    },
    "vivian": {
        "name": "Vivian Taylor",
        "personality": "British wit, emotionally armored, glamorous, edgy. Actress with an intellect sharper than most people expect.",
        "voiceTraits": ["Sardonic", "Charismatic", "Theatrical when it suits her"],
        "relationships": {
            "niklaus": "Half-brother; affection wrapped in barbs",
            "noah": "Half-cousin; distant respect"
        },
        "speechStyle": "Elegant, guarded, and emotionally complex with humor."
    },
    "chuck": {
        "name": "Chuck Bass",
        "personality": "Cynical, emotionally rich, protective, sharp-minded. Controlled danger, elevated by love for Blair.",
        "voiceTraits": ["Dark, seductive", "Emotionally complex", "Dry and deliberate"],
        "relationships": {
            "blair": "Wife, co-ruler, deeply in love",
            "serena": "Adoptive sister",
            "lily": "Adoptive mother"
        },
        "speechStyle": "Measured, heavy-lidded intimacy, often with a power undertone."
    }
}

@app.route("/characters/<name>", methods=["GET"])
def get_character_profile(name):
    key = name.lower()
    true_key = character_aliases.get(key)
    if not true_key:
        return jsonify({"error": "Character not found"}), 404
    return jsonify(characters[true_key])

# -------------------------------
# Milestone Utility Functions
# -------------------------------
def is_milestone_worthy(text):
    text = text.lower()
    keywords = [
        "i love you", "i’m pregnant", "we broke up", "move in", "divorced",
        "engaged", "kissed", "cried", "birthday", "met gala", "stormed out",
        "confession", "in labor", "he proposed", "she said yes", "got married"
    ]
    return any(phrase in text for phrase in keywords)

def already_logged(story_id, scene_text):
    path = f"milestones/{story_id}.json"
    hash_value = hashlib.md5(scene_text.strip().encode()).hexdigest()
    if not os.path.exists(path):
        return False
    with open(path, "r") as f:
        return any(json.loads(line).get("hash") == hash_value for line in f)

# -------------------------------
# Milestone Logging
# -------------------------------
os.makedirs("milestones", exist_ok=True)

@app.route("/milestones/<story_id>", methods=["POST"])
def save_milestone(story_id):
    data = request.json
    with open(f"milestones/{story_id}.json", "a") as f:
        f.write(json.dumps(data) + "\n")
    return jsonify({"status": "milestone saved"})

@app.route("/milestones/<story_id>", methods=["GET"])
def view_milestones(story_id):
    path = f"milestones/{story_id}.json"
    if not os.path.exists(path):
        return jsonify({"milestones": []})
    with open(path, "r") as f:
        return jsonify({"milestones": [json.loads(line) for line in f]})

# -------------------------------
# Deployment
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
