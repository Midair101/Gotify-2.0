import streamlit as st
import json
import os
from pathlib import Path
try:
    from mutagen import File
    from mutagen.id3 import ID3NoHeaderError
except ImportError:
    # Fallback if imports fail
    File = None
    ID3NoHeaderError = Exception

def render_library():
    """Render the local music library management page"""
    st.header("📚 Music Library")
    
    # Library tabs
    tab1, tab2, tab3 = st.tabs(["🎵 All Tracks", "👨‍🎤 Artists", "💿 Albums"])
    
    with tab1:
        render_all_tracks()
    
    with tab2:
        render_artists_view()
    
    with tab3:
        render_albums_view()
    
    # File upload section
    st.divider()
    render_file_upload()

def render_all_tracks():
    """Display all tracks in the library"""
    tracks = st.session_state.local_library.get("tracks", [])
    
    if not tracks:
        st.info("Your local library is empty. Upload some music files to get started!")
        return
    
    # Search within library
    search_term = st.text_input("🔍 Search your library", placeholder="Search by title, artist, or album...")
    
    # Filter tracks based on search
    if search_term:
        filtered_tracks = [
            track for track in tracks
            if (search_term.lower() in track.get('title', '').lower() or
                search_term.lower() in track.get('artist', '').lower() or
                search_term.lower() in track.get('album', '').lower())
        ]
    else:
        filtered_tracks = tracks
    
    # Sort options
    sort_by = st.selectbox(
        "Sort by",
        ["Title", "Artist", "Album", "Date Added"],
        index=0
    )
    
    # Sort tracks
    if sort_by == "Title":
        filtered_tracks.sort(key=lambda x: x.get('title', '').lower())
    elif sort_by == "Artist":
        filtered_tracks.sort(key=lambda x: x.get('artist', '').lower())
    elif sort_by == "Album":
        filtered_tracks.sort(key=lambda x: x.get('album', '').lower())
    elif sort_by == "Date Added":
        filtered_tracks.sort(key=lambda x: x.get('date_added', ''), reverse=True)
    
    st.write(f"Showing {len(filtered_tracks)} tracks")
    
    # Display tracks
    for i, track in enumerate(filtered_tracks):
        display_library_track(track, i)

def render_artists_view():
    """Display library organized by artists"""
    tracks = st.session_state.local_library.get("tracks", [])
    artists = {}
    
    # Group tracks by artist
    for track in tracks:
        artist = track.get('artist', 'Unknown Artist')
        if artist not in artists:
            artists[artist] = []
        artists[artist].append(track)
    
    if not artists:
        st.info("No artists found in your library.")
        return
    
    # Display artists
    for artist, artist_tracks in sorted(artists.items()):
        with st.expander(f"👨‍🎤 {artist} ({len(artist_tracks)} tracks)"):
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if st.button(f"▶️ Play All", key=f"play_artist_{artist}"):
                    play_artist_tracks(artist_tracks)
            
            with col2:
                if st.button(f"➕ Add to Playlist", key=f"add_artist_{artist}"):
                    add_tracks_to_playlist(artist_tracks)
            
            # List tracks
            for track in artist_tracks:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"🎵 {track.get('title', 'Unknown Title')}")
                with col2:
                    st.write(f"💿 {track.get('album', 'Unknown Album')}")
                with col3:
                    if st.button("▶️", key=f"play_track_{track.get('file_path', '')}_{artist}"):
                        play_single_track(track)

def render_albums_view():
    """Display library organized by albums"""
    tracks = st.session_state.local_library.get("tracks", [])
    albums = {}
    
    # Group tracks by album
    for track in tracks:
        album = track.get('album', 'Unknown Album')
        artist = track.get('artist', 'Unknown Artist')
        album_key = f"{album} - {artist}"
        
        if album_key not in albums:
            albums[album_key] = {
                'album': album,
                'artist': artist,
                'tracks': []
            }
        albums[album_key]['tracks'].append(track)
    
    if not albums:
        st.info("No albums found in your library.")
        return
    
    # Display albums
    for album_key, album_data in sorted(albums.items()):
        with st.expander(f"💿 {album_data['album']} by {album_data['artist']} ({len(album_data['tracks'])} tracks)"):
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if st.button(f"▶️ Play Album", key=f"play_album_{album_key}"):
                    play_artist_tracks(album_data['tracks'])
            
            with col2:
                if st.button(f"➕ Add to Playlist", key=f"add_album_{album_key}"):
                    add_tracks_to_playlist(album_data['tracks'])
            
            # List tracks
            for i, track in enumerate(album_data['tracks'], 1):
                col1, col2, col3 = st.columns([1, 3, 1])
                with col1:
                    st.write(f"{i:02d}")
                with col2:
                    st.write(f"🎵 {track.get('title', 'Unknown Title')}")
                with col3:
                    if st.button("▶️", key=f"play_track_{track.get('file_path', '')}_{album_key}"):
                        play_single_track(track)

def render_file_upload():
    """Handle music file uploads"""
    st.subheader("📁 Add Music to Library")
    
    uploaded_files = st.file_uploader(
        "Upload music files",
        type=['mp3', 'wav', 'flac', 'ogg', 'm4a'],
        accept_multiple_files=True,
        help="Supported formats: MP3, WAV, FLAC, OGG, M4A"
    )
    
    if uploaded_files:
        if st.button("📥 Add to Library", type="primary"):
            progress_bar = st.progress(0)
            total_files = len(uploaded_files)
            
            for i, uploaded_file in enumerate(uploaded_files):
                try:
                    # Save file
                    file_path = save_uploaded_file(uploaded_file)
                    
                    # Extract metadata
                    metadata = extract_metadata(file_path)
                    
                    # Add to library
                    track_data = {
                        'title': metadata.get('title', uploaded_file.name),
                        'artist': metadata.get('artist', 'Unknown Artist'),
                        'album': metadata.get('album', 'Unknown Album'),
                        'file_path': str(file_path),
                        'file_size': uploaded_file.size,
                        'date_added': str(st.session_state.get('current_time', '')),
                        'source': 'local'
                    }
                    
                    # Check if track already exists
                    existing_track = next(
                        (track for track in st.session_state.local_library.get('tracks', [])
                         if track.get('file_path') == str(file_path)), None
                    )
                    
                    if not existing_track:
                        st.session_state.local_library.setdefault('tracks', []).append(track_data)
                        st.success(f"Added: {track_data['title']}")
                    else:
                        st.warning(f"Already exists: {track_data['title']}")
                    
                    # Update progress
                    progress_bar.progress((i + 1) / total_files)
                        
                except Exception as e:
                    st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                
                # Save library
                save_local_library()
                st.success(f"Successfully processed {total_files} files!")

def save_uploaded_file(uploaded_file):
    """Save uploaded file to local storage"""
    # Create uploads directory
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    
    # Save file
    file_path = uploads_dir / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def extract_metadata(file_path):
    """Extract metadata from audio file"""
    try:
        audio_file = File(file_path)
        if audio_file is None:
            return {}
        
        metadata = {}
        
        # Common tags
        if 'TIT2' in audio_file:  # Title
            metadata['title'] = str(audio_file['TIT2'])
        elif 'TITLE' in audio_file:
            metadata['title'] = str(audio_file['TITLE'][0])
        
        if 'TPE1' in audio_file:  # Artist
            metadata['artist'] = str(audio_file['TPE1'])
        elif 'ARTIST' in audio_file:
            metadata['artist'] = str(audio_file['ARTIST'][0])
        
        if 'TALB' in audio_file:  # Album
            metadata['album'] = str(audio_file['TALB'])
        elif 'ALBUM' in audio_file:
            metadata['album'] = str(audio_file['ALBUM'][0])
        
        return metadata
        
    except (ID3NoHeaderError, Exception):
        return {}

def display_library_track(track, index):
    """Display a single track from the library"""
    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
    
    with col1:
        st.write(f"🎵 **{track.get('title', 'Unknown Title')}**")
    
    with col2:
        st.write(f"👨‍🎤 {track.get('artist', 'Unknown Artist')}")
    
    with col3:
        st.write(f"💿 {track.get('album', 'Unknown Album')}")
    
    with col4:
        if st.button("▶️", key=f"play_lib_{index}", help="Play"):
            play_single_track(track)
    
    with col5:
        if st.button("➕", key=f"add_lib_{index}", help="Add to playlist"):
            add_track_to_playlist_modal(track)

def play_single_track(track):
    """Play a single track from library"""
    st.session_state.current_track = track
    st.session_state.current_playlist = [track]
    st.session_state.current_track_index = 0
    st.session_state.is_playing = True
    st.success(f"Now playing: {track.get('title', 'Unknown')}")

def play_artist_tracks(tracks):
    """Play all tracks from an artist"""
    st.session_state.current_playlist = tracks
    st.session_state.current_track_index = 0
    st.session_state.current_track = tracks[0]
    st.session_state.is_playing = True
    st.success(f"Playing {len(tracks)} tracks")

def add_tracks_to_playlist(tracks):
    """Add multiple tracks to a playlist"""
    if not st.session_state.playlists:
        st.warning("No playlists found. Create a playlist first.")
        return
    
    # This would open a modal or form to select playlist
    st.info(f"Would add {len(tracks)} tracks to selected playlist")

def add_track_to_playlist_modal(track):
    """Show modal to add track to playlist"""
    if not st.session_state.playlists:
        st.warning("No playlists found. Create a playlist first.")
        return
    
    st.info(f"Would add '{track.get('title', 'Unknown')}' to selected playlist")

def save_local_library():
    """Save the local library to JSON file"""
    library_file = Path("data/local_library.json")
    library_file.parent.mkdir(exist_ok=True)
    
    with open(library_file, 'w') as f:
        json.dump(st.session_state.local_library, f, indent=2)
