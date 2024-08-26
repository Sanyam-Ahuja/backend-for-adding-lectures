from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import psycopg2
from pytube import Playlist
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management and flashing messages

# Google Sheets API configuration
SERVICE_ACCOUNT_FILE = './hmm.json'  # Path to your service account file
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SHEET_ID = '1Yndq4S9SNnfP38oj5wl5sS3a6_PUiWN-CE9zTy8KfYo'  # Your Google Sheet ID
RANGE_NAME = 'Sheet1!A2:B'  # Range of cells to read

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

def fetch_sheets_data():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()

    result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])

    return values

@app.route('/process_user', methods=['POST'])
def process_user():
    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    # Fetch data from Google Sheets
    sheet_data = fetch_sheets_data()

    for row in sheet_data:
        if len(row) >= 2:
            subject_name = row[0]
            playlist_url = row[1]
            message = process_playlist(subject_name, playlist_url, user_id)
            return jsonify({'message': message})

    return jsonify({'error': 'No data found in Google Sheets'}), 404

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
