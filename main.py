import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from supabase import create_client, Client
from pytube import Playlist

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Set up basic logging
logging.basicConfig(level=logging.DEBUG)

def init_supabase():
    url =  'https://ashrzqwhbvbxgrvvbxdr.supabase.co'
    key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFzaHJ6cXdoYnZieGdydnZieGRyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjQ2NzgwODYsImV4cCI6MjA0MDI1NDA4Nn0._HO8PGvO5YG5vVj-cJDJeT3eKL_6Ht6GVe987_xqoAY'
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
        subject_id = get_or_create_subject(supabase, subject_name)
        playlist = Playlist(playlist_url)
        chapter_name = playlist.title

        chapter_insert = supabase.from_("Chapters").insert({
            "subject_id": subject_id,
            "name": chapter_name
        }).execute()
        chapter_id = chapter_insert.data[0]['id']

        lectures_to_insert = []
        for video in playlist.videos:
            lecture_name = video.title
            lecture_url = video.watch_url
            video_duration = video.length

            lectures_to_insert.append({
                "chapter_id": chapter_id,
                "name": lecture_name,
                "file_path": lecture_url,
                "duration": video_duration
            })

        supabase.from_("Lectures").insert(lectures_to_insert).execute()
        logging.debug("Lectures added successfully")
        return "Lectures added successfully"
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
