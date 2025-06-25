from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# In-memory storage for stories
stories = {}

@app.route("/", methods=["GET"])
def home():
    return "Gossip Girl Storytelling API is running!"

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

@app.route("/story/<story_id>/events", methods=["POST"])
def add_event(story_id):
    data = request.json
    stories[story_id]["events"].append(data)
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
# Canon rules endpoint
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
# Character profiles (case-insensitive)
# -------------------------------
character_aliases = {
    "serena": "serena",
    "blair": "blair",
    "chuck": "chuck",
    "charles": "chuck",
    "lily": "lily",
    "lilian": "lily",
    "niklaus": "niklaus",
    "nik": "niklaus",
    "klaus": "niklaus",
    "noah": "noah",
    "nate": "nate",
    "nathaniel": "nate",
    "dan": "dan",
    "daniel": "dan",
    "eric": "eric",
    "rufus": "rufus",
    "william": "william",
    "vivian": "vivian"
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
    },
    "blair": {
        "name": "Blair Waldorf",
        "personality": "Razor-sharp, ambitious, emotionally vulnerable beneath control. Loyal, competitive, complex.",
        "voiceTraits": ["Fast-paced", "Witty", "Defensive sarcasm"],
        "relationships": {
            "chuck": "Husband, soulmate",
            "serena": "Best friend, deep history",
            "dan": "Complicated ally"
        },
        "backstory": "Daughter of Eleanor Waldorf and Harold Waldorf. Married Chuck and had a son, Henry. Formerly married to Prince Louis Grimaldi.",
        "speechStyle": "Layered, clever, always curated for power. Wields wit like a weapon."
    },
    "chuck": {
        "name": "Chuck Bass",
        "personality": "Magnetic, guarded, fiercely loyal once earned. Expresses love through acts, not words.",
        "voiceTraits": ["Sardonic", "Dry", "Loaded with unspoken meaning"],
        "relationships": {
            "blair": "Wife",
            "serena": "Adoptive sister",
            "lily": "Adoptive mother"
        },
        "backstory": "Inherited Bass Industries after the death of Bart Bass. Married Blair. Father of Henry.",
        "speechStyle": "Quiet, deliberate. Emotion leaks through when walls drop. Mostly communicates with silence and tension."
    },
    "lily": {
        "name": "Lily van der Woodsen",
        "personality": "Polished, elegant, protective through control. Proud and emotionally complex.",
        "voiceTraits": ["Restrained", "Maternal", "Elegant"],
        "relationships": {
            "serena": "Daughter",
            "eric": "Son",
            "william": "Current husband",
            "chuck": "Adopted son",
            "rufus": "Former husband"
        },
        "backstory": "Former art dealer and Manhattan socialite. Married multiple times. Matriarch of the van der Woodsen family.",
        "speechStyle": "Understated, sharp when needed. Rarely raises her voice, but every word lands."
    },
    "niklaus": {
        "name": "Niklaus Von Wolfram",
        "personality": "Once a reckless prodigy, now a composed, multifaceted man. Blends seriousness, introversion, and moments of boyish warmth.",
        "voiceTraits": ["Precise", "Dry charm", "European-accented"],
        "relationships": {
            "noah": "Cousin (strained)",
            "otto": "Uncle (mentor)",
            "dietrich": "Father (demanding)",
            "vivian": "Half-sister (supportive)",
            "serena": "Potential romantic interest (TBD in-story)"
        },
        "backstory": "Born in Slovenia, raised between Germany, Vienna and Monaco. Karted from age 6, Ferrari Academy by 12, and became a 3-time F1 World Champion. Took a hiatus to earn his M.Arch under pressure from his father. Now balances racing, architecture, and a complicated family legacy.",
        "speechStyle": "Measured, quiet, non-performative. Charm appears in glimpses. Often speaks through action, not words."
    }
}

@app.route("/characters/<name>", methods=["GET"])
def get_character_profile(name):
    key = name.lower()
    true_key = character_aliases.get(key)
    if not true_key:
        return jsonify({"error": "Character not found"}), 404
    character = characters.get(true_key)
    return jsonify(character)

# -------------------------------
# Deployment
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
