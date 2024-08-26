from flask import Flask, render_template, request, redirect, url_for, flash, request, jsonify
import psycopg2
from pytube import Playlist

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management and flashing messages

def connect_to_db():
    try:
        connection = psycopg2.connect(
            dbname='neondb',
            user='neondb_owner',
            password='F91ZkptcqXQm',
            host='ep-winter-hat-a55yv5ct-pooler.us-east-2.aws.neon.tech',
            sslmode='require'
        )
        return connection
    except Exception as e:
        print("Error connecting to the database:", e)
        return None

def get_or_create_subject(cursor, subject_name):
    cursor.execute("SELECT id FROM Subjects WHERE name = %s", (subject_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    cursor.execute("INSERT INTO Subjects (name) VALUES (%s) RETURNING id", (subject_name,))
    return cursor.fetchone()[0]

def process_playlist(subject_name, playlist_url, user_id):
    try:
        connection = connect_to_db()
        if connection is None:
            return "Failed to connect to the database"

        cursor = connection.cursor()
        subject_id = get_or_create_subject(cursor, subject_name)
        playlist = Playlist(playlist_url)
        chapter_name = playlist.title

        cursor.execute(
            "INSERT INTO Chapters (subject_id, name) VALUES (%s, %s) RETURNING id",
            (subject_id, chapter_name)
        )
        chapter_id = cursor.fetchone()[0]

        for video in playlist.videos:
            lecture_name = video.title
            lecture_url = video.watch_url
            video_duration = video.length  # Duration in seconds

            cursor.execute(
                "INSERT INTO Lectures (chapter_id, user_id, name, file_path, watched, duration) VALUES (%s, %s, %s, %s, %s, %s)",
                (chapter_id, user_id, lecture_name, lecture_url, False, video_duration)
            )

        connection.commit()
        cursor.close()
        connection.close()
        return "Lectures added successfully"
    except Exception as e:
        print("Error processing playlist:", e)
        return "Failed to process playlist"

@app.route('/process_user', methods=['POST'])
def process_user():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    # For simplicity, let's assume you have some predefined subject_name and playlist_url
    subject_name = 'Default Subject'  # You might want to get this dynamically
    playlist_url = 'https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID'  # Replace with actual playlist URL

    message = process_playlist(subject_name, playlist_url, user_id)
    return jsonify({'message': message})

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        playlist_url = request.form['playlist_url']
        user_id = request.form['user_id']

        message = process_playlist(subject_name, playlist_url, user_id)
        flash(message)
        return redirect(url_for('index'))

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Change port if necessary
