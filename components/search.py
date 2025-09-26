import streamlit as st
import requests
from utils.spotify_client import SpotifyClient
from utils.youtube_client import YouTubeClient
from utils.network_utils import check_internet_connection

def render_search():
    """Render the search page for online music discovery"""
    st.header("🔍 Search Music")
    
    if not st.session_state.network_connected:
        st.error("🌐 No internet connection. Search functionality requires online access.")
        if st.button("🔄 Retry Connection"):
            st.session_state.network_connected = check_internet_connection()
            st.rerun()
        return
    
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None

    with st.form(key="search_form"):
        search_query = st.text_input(
            "Search for songs, artists, or albums",
            placeholder="Enter your search query and press Enter...",
            help="Search across Spotify and YouTube for music"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            search_spotify = st.checkbox("🎵 Spotify", value=True)
        with col2:
            search_youtube = st.checkbox("📺 YouTube", value=True)
        
        # The form is submitted when the user presses Enter in the text_input.
        if st.form_submit_button("Search", use_container_width=True, type="primary"):
            if search_query:
                with st.spinner("Searching for music..."):
                    st.session_state.search_results = perform_search(search_query, search_spotify, search_youtube)

    if st.session_state.search_results:
        display_search_results(st.session_state.search_results)


def perform_search(query, include_spotify=True, include_youtube=True):
    """Perform search across selected platforms"""
    results = {
        'spotify': [],
        'youtube': []
    }
    
    # Search Spotify
    if include_spotify:
        try:
            spotify_client = SpotifyClient()
            if spotify_client.is_configured:
                spotify_results = spotify_client.search(query)
                results['spotify'] = spotify_results
            else:
                st.warning("Spotify credentials are not configured. Please set `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` environment variables to enable Spotify search.")
        except Exception as e:
            st.error(f"Spotify search failed: {str(e)}")
    
    # Search YouTube
    if include_youtube:
        try:
            youtube_client = YouTubeClient()
            youtube_results = youtube_client.search(query)
            results['youtube'] = youtube_results
        except Exception as e:
            st.error(f"YouTube search failed: {str(e)}")
    
    return results

def display_search_results(results):
    """Display search results in organized tabs"""
    
    # Create tabs for different sources
    tabs = []
    if results['spotify']:
        tabs.append("🎵 Spotify")
    if results['youtube']:
        tabs.append("📺 YouTube")
    
    if not tabs:
        st.warning("No results found")
        return
    
    tab_objects = st.tabs(tabs)
    
    # Display Spotify results
    if results['spotify'] and "🎵 Spotify" in tabs:
        with tab_objects[tabs.index("🎵 Spotify")]:
            st.subheader("Spotify Results")
            for track in results['spotify'][:10]:  # Show top 10 results
                display_track_card(track, source="spotify")
    
    # Display YouTube results
    if results['youtube'] and "📺 YouTube" in tabs:
        with tab_objects[tabs.index("📺 YouTube")]:
            st.subheader("YouTube Results")
            for track in results['youtube'][:10]:  # Show top 10 results
                display_track_card(track, source="youtube")

def display_track_card(track, source):
    """Display individual track card with play and add options"""
    
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        
        with col1:
            st.markdown(f"**{track.get('title', 'Unknown Title')}**")
            st.markdown(f"*{track.get('artist', 'Unknown Artist')}*")
            if track.get('album'):
                st.caption(f"Album: {track.get('album')}")

        with col2:
            duration = track.get('duration', 'Unknown')
            if isinstance(duration, int):
                minutes, seconds = divmod(duration // 1000, 60)
                duration = f"{minutes}:{seconds:02d}"
            st.markdown(f"⏱️ {duration}")
            
            if track.get('popularity'):
                st.markdown(f"🔥 {track['popularity']}/100")
        
        with col3:
            if st.button("▶️", key=f"play_{track.get('id', hash(str(track)))}", help="Play now"):
                play_track_from_search(track, source)
        
        with col4:
            if st.button("➕", key=f"add_{track.get('id', hash(str(track)))}", help="Add to playlist"):
                # Set the track to be added in session state to show the form
                st.session_state.track_to_add = track.get('id', hash(str(track)))
                st.rerun()

    # If a track is selected to be added, show the form
    if st.session_state.get('track_to_add') == track.get('id', hash(str(track))):
        add_track_to_playlist_form(track, source)


def play_track_from_search(track, source, add_to_queue=False):
    """Play a track from search results"""
    try:
        playable_track = None

        if source == 'spotify':
            with st.spinner(f"Finding '{track.get('title')}' on YouTube..."):
                # For Spotify, find the equivalent on YouTube to stream
                youtube_client = YouTubeClient()
                query = f"{track.get('title')} {track.get('artist')}"
                yt_results = youtube_client.search(query, max_results=1)

                if yt_results:
                    yt_track = yt_results[0]
                    playable_track = {
                        'title': track.get('title'), # Keep original Spotify metadata
                        'artist': track.get('artist'),
                        'album': track.get('album'),
                        'id': yt_track.get('id'), # Use YouTube ID for streaming
                        'source': 'youtube', # Source is now youtube for playback
                        'album_art': track.get('album_art') or yt_track.get('thumbnail')
                    }
                    st.info(f"Found on YouTube: '{yt_track.get('title')}'")
                else:
                    st.error("Could not find a matching track on YouTube to play.")
                    return
        elif source == 'youtube':
            # It's already a YouTube track, just format it
            playable_track = {
                **track,
                'album_art': track.get('thumbnail')
            }


        if playable_track:
            st.session_state.current_track = playable_track
            st.session_state.current_playlist = [playable_track]
            st.session_state.current_track_index = 0
            st.session_state.audio_manager.play_track(playable_track)
            st.success(f"Now playing: {playable_track['title']} by {playable_track['artist']}")

    except Exception as e:
        st.error(f"Failed to play track: {str(e)}")

def add_track_to_playlist_form(track, source):
    """Display a form to add a track to a playlist."""
    playlist_names = list(st.session_state.playlists.keys())

    if not playlist_names:
        st.warning("No playlists found. Create a playlist first.")
        if st.button("Cancel", key=f"cancel_add_{track.get('id')}"):
            del st.session_state.track_to_add
            st.rerun()
        return

    with st.form(f"add_to_playlist_{track.get('id', hash(str(track)))}"):
        selected_playlist = st.selectbox(
            "Select playlist",
            playlist_names,
            key=f"playlist_select_{track.get('id', hash(str(track)))}"
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("✅ Add to Playlist")
        with col2:
            cancelled = st.form_submit_button("❌ Cancel")

        if submitted:
            track_data = {
                'title': track.get('title', 'Unknown Title'),
                'artist': track.get('artist', 'Unknown Artist'),
                'album': track.get('album', 'Unknown Album'),
                'id': track.get('id'),
                'source': source,
                'album_art': track.get('album_art') or track.get('thumbnail')
            }

            if selected_playlist not in st.session_state.playlists:
                st.session_state.playlists[selected_playlist] = []

            track_exists = any(
                existing_track.get('id') == track_data.get('id')
                for existing_track in st.session_state.playlists[selected_playlist]
            )

            if not track_exists:
                st.session_state.playlists[selected_playlist].append(track_data)
                st.success(f"Added '{track_data['title']}' to '{selected_playlist}'")
            else:
                st.warning("Track already exists in this playlist")
            
            del st.session_state.track_to_add
            st.rerun()
        
        if cancelled:
            del st.session_state.track_to_add
            st.rerun()
