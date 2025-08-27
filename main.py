import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from supabase import create_client, Client
from yt_dlp import YoutubeDL

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Set up basic logging
logging.basicConfig(level=logging.DEBUG)

def init_supabase():
    url =  'https://kgdqcogapxlirrgvfrfm.supabase.co'
    key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtnZHFjb2dhcHhsaXJyZ3ZmcmZtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYwNjk3MTksImV4cCI6MjA3MTY0NTcxOX0.72skBCSX1YUzFXbXiQ8kXFHMsnufPjsnKNNqWQZRsJo'
    supabase: Client = create_client(url, key)
    return supabase

supabase = init_supabase()

def get_or_create_subject(supabase, subject_name):
    logging.debug(f"Attempting to find or create subject: {subject_name}")
    try:
        subject_query = supabase.from_("Subjects").select("id").eq("name", subject_name).execute()
        if subject_query.data:
            logging.debug(f"Found subject: {subject_name} with ID {subject_query.data[0]['id']}")
            return subject_query.data[0]['id']
        
        subject_insert = supabase.from_("Subjects").insert({"name": subject_name}).execute()
        logging.debug(f"Created subject: {subject_name} with ID {subject_insert.data[0]['id']}")
        return subject_insert.data[0]['id']
    except Exception as e:
        logging.error(f"Error in get_or_create_subject: {e}")
        raise

def process_playlist(subject_name, playlist_url):
    try:
        # Get or create subject
        subject_id = get_or_create_subject(supabase, subject_name)

        # Use yt-dlp to fetch playlist info (without downloading)
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,  # don't resolve each video fully
            'dump_single_json': True
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)

        chapter_name = info.get('title', 'Unknown Playlist')

        # Insert chapter into Supabase
        chapter_insert = supabase.from_("Chapters").insert({
            "subject_id": subject_id,
            "name": chapter_name
        }).execute()
        chapter_id = chapter_insert.data[0]['id']

        # Prepare lecture entries
        lectures_to_insert = []
        for entry in info.get('entries', []):
            lectures_to_insert.append({
                "chapter_id": chapter_id,
                "name": entry.get("title", "Unknown Video"),
                "file_path": f"https://www.youtube.com/watch?v={entry['id']}",
                "duration": entry.get("duration") or 0  # yt-dlp sometimes gives seconds
            })

        if lectures_to_insert:
            supabase.from_("Lectures").insert(lectures_to_insert).execute()
            logging.debug("Lectures added successfully")
            return "Lectures added successfully"
        else:
            return "No lectures found in playlist"

    except Exception as e:
        logging.error(f"Error processing playlist: {e}")
        return "Failed to process playlist"


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        playlist_url = request.form['playlist_url']

        message = process_playlist(subject_name, playlist_url)
        flash(message)
        return redirect(url_for('index'))

    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 4000))
    app.run(debug=True, host='0.0.0.0', port=port)
