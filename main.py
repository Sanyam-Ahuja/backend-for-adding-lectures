from flask import Flask, render_template, request, redirect, url_for, flash, request, jsonify
from supabase import create_client, Client
from pytube import Playlist
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management and flashing messages

# Initialize Supabase client
def init_supabase():
    # Directly use the strings or use environment variables
    url = 'https://ashrzqwhbvbxgrvvbxdr.supabase.co'
    key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFzaHJ6cXdoYnZieGdydnZieGRyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjQ2NzgwODYsImV4cCI6MjA0MDI1NDA4Nn0._HO8PGvO5YG5vVj-cJDJeT3eKL_6Ht6GVe987_xqoAY'
    supabase: Client = create_client(url, key)
    return supabase

supabase = init_supabase()

def get_or_create_subject(supabase, subject_name):
    # Check if subject exists
    subject_query = supabase.from_("Subjects").select("id").eq("name", subject_name).execute()
    if subject_query.data:
        return subject_query.data[0]['id']
    
    # Insert new subject and get its ID
    subject_insert = supabase.from_("Subjects").insert({"name": subject_name}).execute()
    return subject_insert.data[0]['id']

def process_playlist(subject_name, playlist_url):
    try:
        # Get or create the subject
        subject_id = get_or_create_subject(supabase, subject_name)
        playlist = Playlist(playlist_url)
        chapter_name = playlist.title

        # Insert new chapter
        chapter_insert = supabase.from_("Chapters").insert({
            "subject_id": subject_id,
            "name": chapter_name
        }).execute()
        chapter_id = chapter_insert.data[0]['id']

        # Process each video in the playlist
        lectures_to_insert = []
        for video in playlist.videos:
            lecture_name = video.title
            lecture_url = video.watch_url
            video_duration = video.length  # Duration in seconds

            lectures_to_insert.append({
                "chapter_id": chapter_id,
                "name": lecture_name,
                "file_path": lecture_url,
                "duration": video_duration
            })

        # Bulk insert lectures
        supabase.from_("Lectures").insert(lectures_to_insert).execute()
        return "Lectures added successfully"
    except Exception as e:
        print("Error processing playlist:", e)
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
    app.run(debug=True, port=5001)  # Change port if necessary
