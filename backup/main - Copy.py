import psycopg2
from pytube import Playlist
import sys

def connect_to_db():
    try:
        connection = psycopg2.connect(
            dbname='neondb',        # Replace with your NeonDB database name
            user='neondb_owner',         # Replace with your NeonDB username
            password='F91ZkptcqXQm',     # Replace with your NeonDB password
            host='ep-winter-hat-a55yv5ct-pooler.us-east-2.aws.neon.tech',        # Replace with your NeonDB host (e.g., 'your-neon-host.getneon.com')
            sslmode='require'             # SSL mode required for NeonDB
        )
        return connection
    except Exception as e:
        print("Error connecting to the database:", e)
        sys.exit(1)

def get_or_create_subject(cursor, subject_name):
    # Check if the subject already exists
    cursor.execute("SELECT id FROM Subjects WHERE name = %s", (subject_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    # If the subject does not exist, create it
    cursor.execute("INSERT INTO Subjects (name) VALUES (%s) RETURNING id", (subject_name,))
    return cursor.fetchone()[0]

def process_playlist(subject_name, playlist_url, user_id):
    try:
        connection = connect_to_db()
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
        print("Lectures added successfully")
    except Exception as e:
        print("Error processing playlist:", e)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python main.py <subject_name> <playlist_url> <user_id>")
        sys.exit(1)

    subject_name = sys.argv[1]
    playlist_url = sys.argv[2]
    user_id = sys.argv[3]

    process_playlist(subject_name, playlist_url, user_id)

