# admin_app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
import sqlite3, os
from datetime import datetime

# --- Config ---
try:
    from config import ADMIN_PORT, SQLITE_DB
except Exception:
    ADMIN_PORT = int(os.getenv("ADMIN_PORT", "5001"))
    SQLITE_DB = os.getenv("SQLITE_DB", "project2.db")

app = Flask(__name__, template_folder="templates")
CORS(app)

# --- DB Connection ---
def conn():
    c = sqlite3.connect(SQLITE_DB)
    c.row_factory = sqlite3.Row
    return c

# --- Initialize DB (auto-create tables if missing) ---
def init_db():
    c = conn()
    c.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            requested_by TEXT,
            status TEXT NOT NULL,
            partitions INTEGER DEFAULT 1,
            replication_factor INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # Add 'updated_at' column if not present
    cols = [r["name"] for r in c.execute("PRAGMA table_info(topics)")]
    if "updated_at" not in cols:
        c.execute("ALTER TABLE topics ADD COLUMN updated_at DATETIME;")
    # user_subscriptions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            topic_name TEXT NOT NULL,
            subscribed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, topic_name)
        );
    """)
    c.commit()
    c.close()

# --- Health endpoint ---
@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat() + "Z"})

# --- Topic APIs ---
@app.route("/topics/request", methods=["POST"])
def request_topic():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    desc = (data.get("description") or "").strip()
    requested_by = (data.get("requested_by") or "anonymous").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    c = conn()
    try:
        c.execute("INSERT INTO topics (name, description, requested_by, status) VALUES (?,?,?,?)",
                  (name, desc, requested_by, "pending"))
        c.commit()
    except sqlite3.IntegrityError:
        c.close()
        return jsonify({"error": "topic exists"}), 400
    c.close()
    return jsonify({"msg": "requested", "name": name}), 200

@app.route("/topics/approve/<name>", methods=["POST"])
def approve_topic(name):
    c = conn()
    c.execute("UPDATE topics SET status='approved', updated_at=CURRENT_TIMESTAMP WHERE name=?", (name,))
    c.commit()
    c.close()
    return jsonify({"msg": "approved", "name": name}), 200

@app.route("/topics/reject/<name>", methods=["POST"])
def reject_topic(name):
    c = conn()
    c.execute("UPDATE topics SET status='rejected', updated_at=CURRENT_TIMESTAMP WHERE name=?", (name,))
    c.commit()
    c.close()
    return jsonify({"msg": "rejected", "name": name}), 200

@app.route("/topics/activate/<name>", methods=["POST"])
def activate_topic(name):
    c = conn()
    c.execute("UPDATE topics SET status='active', updated_at=CURRENT_TIMESTAMP WHERE name=?", (name,))
    c.commit()
    c.close()
    return jsonify({"msg": "activated", "name": name}), 200

@app.route("/topics/deactivate/<name>", methods=["POST"])
def deactivate_topic(name):
    c = conn()
    c.execute("UPDATE topics SET status='deactivated', updated_at=CURRENT_TIMESTAMP WHERE name=?", (name,))
    c.commit()
    c.close()
    return jsonify({"msg": "deactivated", "name": name}), 200

@app.route("/topics/delete/<name>", methods=["POST"])
def delete_topic(name):
    c = conn()
    c.execute("DELETE FROM topics WHERE name=?", (name,))
    c.commit()
    c.close()
    return jsonify({"msg": "deleted", "name": name}), 200

# --- Main topic list endpoints ---
@app.route("/topics", methods=["GET"])
def list_topic_names():
    """Returns only topic names — for Producer/Consumer."""
    status = request.args.get("status")
    c = conn()
    if status:
        cur = c.execute("SELECT name FROM topics WHERE status=? ORDER BY name", (status,))
    else:
        cur = c.execute("SELECT name FROM topics ORDER BY name")
    names = [r["name"] for r in cur.fetchall()]
    c.close()
    return jsonify({"topics": names})

@app.route("/topics/full", methods=["GET"])
def list_topics_full():
    """Full topic details — for UI or debugging."""
    c = conn()
    cur = c.execute("SELECT * FROM topics ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    c.close()
    return jsonify(rows)

# --- Subscription APIs ---
@app.route("/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json(force=True) or {}
    user = data.get("user_id")
    topic = data.get("topic")
    if not user or not topic:
        return jsonify({"error": "user_id and topic required"}), 400
    c = conn()
    try:
        c.execute("INSERT INTO user_subscriptions (user_id, topic_name) VALUES (?,?)", (user, topic))
        c.commit()
    except sqlite3.IntegrityError:
        c.close()
        return jsonify({"error": "already subscribed"}), 400
    c.close()
    return jsonify({"msg": "subscribed"}), 200

@app.route("/unsubscribe", methods=["POST"])
def unsubscribe():
    data = request.get_json(force=True) or {}
    user = data.get("user_id")
    topic = data.get("topic")
    if not user or not topic:
        return jsonify({"error": "user_id and topic required"}), 400
    c = conn()
    c.execute("DELETE FROM user_subscriptions WHERE user_id=? AND topic_name=?", (user, topic))
    c.commit()
    c.close()
    return jsonify({"msg": "unsubscribed"}), 200

@app.route("/subscriptions", methods=["GET"])
def list_subscriptions():
    c = conn()
    cur = c.execute("SELECT user_id, topic_name, subscribed_at FROM user_subscriptions ORDER BY subscribed_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    c.close()
    return jsonify(rows)

# --- UI Pages ---
@app.route("/")
def index():
    return redirect(url_for("view_topics"))

@app.route("/ui/topics")
def view_topics():
    c = conn()
    cur = c.execute("SELECT * FROM topics ORDER BY created_at DESC")
    topics = [dict(r) for r in cur.fetchall()]
    c.close()
    return render_template("topics.html", topics=topics)

@app.route("/ui/subscriptions")
def view_subs():
    c = conn()
    cur = c.execute("SELECT * FROM user_subscriptions ORDER BY subscribed_at DESC")
    subs = [dict(r) for r in cur.fetchall()]
    c.close()
    return render_template("subscriptions.html", subs=subs)

# --- Main entrypoint ---
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=ADMIN_PORT)
