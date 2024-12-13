from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import os
import pickle

def load_config():
    """Load configuration from config.json file."""
    config_file = 'config.json'
    example_config_file = 'config.example.json'
    
    if not os.path.exists(config_file):
        if os.path.exists(example_config_file):
            print(f"Please copy {example_config_file} to {config_file} and update with your settings")
        else:
            print(f"Neither {config_file} nor {example_config_file} found!")
        exit(1)
    
    with open(config_file, 'r') as f:
        return json.load(f)

CONFIG = load_config()
SCOPES = CONFIG['scopes']

def get_authenticated_service():
    """Get authenticated YouTube service with token caching."""
    creds = None
    # Token file to store the user's access and refresh tokens
    token_file = CONFIG['token_file']
    
    # Load existing credentials if they exist
    if os.path.exists(token_file):
        try:
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            print(f"Error loading credentials: {e}")
    
    # If there are no valid credentials available, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                creds = None
        
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(
                CONFIG['client_secrets_file'],
                SCOPES,
                redirect_uri='http://localhost'
            )
            creds = flow.run_local_server(
                port=0,
                prompt='consent'
            )
        
        # Save the credentials for future use
        with open(token_file, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('youtube', 'v3', credentials=creds)

def get_playlists():
    """Fetch all playlists for the authenticated user."""
    try:
        youtube = get_authenticated_service()
        
        # Get playlists
        request = youtube.playlists().list(
            part='snippet,contentDetails',
            mine=True,
            maxResults=50  # Adjust this number as needed
        )
        
        playlists = []
        while request:
            response = request.execute()
            
            for playlist in response['items']:
                playlist_info = {
                    'title': playlist['snippet']['title'],
                    'id': playlist['id'],
                    'description': playlist['snippet']['description'],
                    'item_count': playlist['contentDetails']['itemCount']
                }
                playlists.append(playlist_info)
            
            # Get next page of results
            request = youtube.playlists().list_next(request, response)
        
        return playlists

    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred: {e.content}')
        return None

def create_playlist(youtube, title, description="", privacy_status="private"):
    """Create a new playlist."""
    try:
        request = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description
                },
                "status": {
                    "privacyStatus": privacy_status
                }
            }
        )
        response = request.execute()
        print(f"Created playlist: {response['snippet']['title']}")
        return response['id']
    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred: {e.content}')
        return None

def delete_playlist(youtube, playlist_id):
    """Delete a playlist by ID."""
    try:
        youtube.playlists().delete(
            id=playlist_id
        ).execute()
        print(f"Successfully deleted playlist with ID: {playlist_id}")
        return True
    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred: {e.content}')
        return False

def delete_all_playlists(youtube):
    """Delete all playlists of the authenticated user."""
    try:
        playlists = get_playlists()
        if not playlists:
            print("No playlists found to delete.")
            return False
        
        print(f"\nWARNING: This will delete all {len(playlists)} playlists:")
        for playlist in playlists:
            print(f"- {playlist['title']} (ID: {playlist['id']})")
        
        confirm = input("\nAre you sure you want to delete ALL playlists? Type 'DELETE ALL' to confirm: ")
        if confirm != "DELETE ALL":
            print("Operation cancelled.")
            return False
        
        success_count = 0
        fail_count = 0
        
        for playlist in playlists:
            try:
                youtube.playlists().delete(
                    id=playlist['id']
                ).execute()
                print(f"Deleted playlist: {playlist['title']}")
                success_count += 1
            except HttpError as e:
                print(f"Failed to delete playlist {playlist['title']}: {e.resp.status}")
                fail_count += 1
        
        print(f"\nOperation completed: {success_count} playlists deleted, {fail_count} failed")
        return True
        
    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred: {e.content}')
        return False

def search_youtube_videos(youtube, query, max_results=10):
    """Search for YouTube videos with specific query."""
    try:
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            videoDuration="long",  # Only long videos (likely full albums)
            maxResults=max_results
        )
        response = request.execute()
        return response.get('items', [])
    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred: {e.content}')
        return []

def add_video_to_playlist(youtube, playlist_id, video_id):
    """Add a video to a playlist."""
    try:
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": playlist_id,
                    "position": 0,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        ).execute()
        return True
    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred: {e.content}')
        return False

def create_boc_playlist():
    """Create a Boards of Canada chronological album playlist."""
    youtube = get_authenticated_service()
    
    # Boards of Canada releases in chronological order (including EPs)
    boc_albums = [
        "Twoism (1995)",
        "Hi Scores EP (1996)",
        "Music Has the Right to Children (1998)",
        "In A Beautiful Place Out In The Country EP (2000)",
        "Geogaddi (2002)",
        "The Campfire Headphase (2005)",
        "Trans Canada Highway EP (2006)",
        "Tomorrow's Harvest (2013)"
    ]
    
    # Create the playlist
    playlist_id = create_playlist(
        youtube,
        title="Boards of Canada - Full Albums (Chronological)",
        description="Complete Boards of Canada studio albums in chronological order.",
        privacy_status="private"
    )
    
    if not playlist_id:
        print("Failed to create playlist")
        return
    
    print("\nSearching for albums...")
    for album in boc_albums:
        print(f"\nSearching for: {album}")
        search_query = f"Boards of Canada {album} full album"
        results = search_youtube_videos(youtube, search_query, max_results=5)
        
        if not results:
            print(f"No results found for {album}")
            continue
        
        print("\nFound potential matches:")
        for i, video in enumerate(results, 1):
            title = video['snippet']['title']
            video_id = video['id']['videoId']
            print(f"{i}. {title}")
        
        choice = input("\nEnter the number of the correct video (or 's' to skip): ")
        if choice.lower() == 's':
            continue
        
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(results):
                video = results[choice_idx]
                video_id = video['id']['videoId']
                if add_video_to_playlist(youtube, playlist_id, video_id):
                    print(f"Added {video['snippet']['title']} to playlist")
                else:
                    print("Failed to add video to playlist")
            else:
                print("Invalid choice")
        except ValueError:
            print("Invalid input")
    
    print("\nPlaylist creation completed!")

def main():
    youtube = get_authenticated_service()
    
    while True:
        print("\nYouTube Playlist Manager")
        print("1. List all playlists")
        print("2. Create new playlist")
        print("3. Delete playlist")
        print("4. Delete ALL playlists")
        print("5. Create BoC Albums playlist")  # New option
        print("6. Exit")
        
        choice = input("Enter your choice (1-6): ")
        
        if choice == "1":
            playlists = get_playlists()
            if playlists:
                print(f'\nFound {len(playlists)} playlists:')
                for playlist in playlists:
                    print(f"\nTitle: {playlist['title']}")
                    print(f"ID: {playlist['id']}")
                    print(f"Number of videos: {playlist['item_count']}")
                    print(f"Description: {playlist['description']}")
        
        elif choice == "2":
            title = input("Enter playlist title: ")
            description = input("Enter playlist description (optional): ")
            privacy = input("Enter privacy status (public/private/unlisted) [default: private]: ").lower() or "private"
            
            if privacy not in ["public", "private", "unlisted"]:
                print("Invalid privacy status. Using 'private'")
                privacy = "private"
            
            playlist_id = create_playlist(youtube, title, description, privacy)
            if playlist_id:
                print(f"Playlist created successfully! ID: {playlist_id}")
        
        elif choice == "3":
            playlist_id = input("Enter playlist ID to delete: ")
            confirm = input(f"Are you sure you want to delete playlist {playlist_id}? (yes/no): ")
            if confirm.lower() == "yes":
                if delete_playlist(youtube, playlist_id):
                    print("Playlist deleted successfully!")
            else:
                print("Deletion cancelled.")
        
        elif choice == "4":
            delete_all_playlists(youtube)
        elif choice == "5":
            create_boc_playlist()
        elif choice == "6":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main() 