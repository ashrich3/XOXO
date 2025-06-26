from flask import Flask, request, jsonify
import os
import json
import hashlib

app = Flask(__name__)

# -------------------------------
# In-memory story tracking
# -------------------------------
stories = {}

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
    stories[story_id]["events"].append(data)

    # Auto milestone logging
    if is_milestone_worthy(scene_text) and not already_logged(story_id, scene_text):
        milestone = {
            "scene": scene_text,
            "characters": data.get("charactersInScene", []),
            "emotions": data.get("emotions", {}),
            "hash": hashlib.md5(scene_text.strip().encode()).hexdigest(),
            "source": "auto"
        }
        with open(f"milestones/{story_id}.json", "a") as f:
            f.write(json.dumps(milestone) + "\n")

    return jsonify({"status": "event added"})

@app.route("/story/<story_id>/summary", methods=["GET"])
def get_summary(story_id):
    story = stories.get(story_id, {})
    summary = " ".join(e["sceneText"] for e in story.get("events", []))[:500]
    return jsonify({
        "summary": summary,
        "majorEvents": [e["sceneText"][:60] for e in story.get("events", [])]
    })

# -------------------------------
# Canon rules
# -------------------------------
canon_rules = [
    "Gossip Girl's narration ended in Season 6 finale. Dan was revealed as Gossip Girl.",
    "Chuck and Blair are married and have a son, Henry.",
    "Serena is the daughter of Lily and William. Her brother is Eric.",
    "Chuck was adopted by Lily during her marriage to Bart Bass.",
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
    "lily": "lily", "lilian": "lily", "niklaus": "niklaus", "nik": "niklaus",
    "klaus": "niklaus", "noah": "noah", "nate": "nate", "nathaniel": "nate",
    "dan": "dan", "daniel": "dan", "eric": "eric", "rufus": "rufus",
    "william": "william", "vivian": "vivian"
}

characters = {
    "serena": {
        "name": "Serena van der Woodsen",
        "personality": "Warm, effortlessly charming, impulsive, romantic, emotionally weighted by her past.",
        "voiceTraits": ["Open", "Dreamy", "Unscripted intimacy"],
        "relationships": {
            "blair": "Best friend, rival",
            "dan": "First love, husband (series finale)",
            "chuck": "Adoptive brother, loyal friend",
            "lily": "Mother",
            "william": "Father",
            "eric": "Younger brother"
        },
        "backstory": "Former NYC socialite and Upper East Side icon. Returned from boarding school in Season 1 with secrets and emotional baggage. Marries Dan in the series finale.",
        "speechStyle": "Poetic, soft, emotionally immediate. Never rehearsed."
    }
    # Add other characters as needed
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
        return any(
            json.loads(line).get("hash") == hash_value for line in f
        )

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
