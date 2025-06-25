from flask import Flask, request, jsonify
app = Flask(__name__)

# Simulated in-memory story tracking
stories = {}

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

if __name__ == "__main__":
    app.run(port=5000)
