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
    
    # Search input
    search_query = st.text_input(
        "Search for songs, artists, or albums",
        placeholder="Enter your search query...",
        help="Search across Spotify and YouTube for music"
    )
    
    # Search options
    col1, col2 = st.columns(2)
    with col1:
        search_spotify = st.checkbox("🎵 Search Spotify", value=True)
    with col2:
        search_youtube = st.checkbox("📺 Search YouTube", value=True)
    
    if search_query and st.button("🔍 Search", type="primary"):
        with st.spinner("Searching for music..."):
            search_results = perform_search(search_query, search_spotify, search_youtube)
            
            if search_results:
                display_search_results(search_results)
            else:
                st.warning("No results found. Try a different search term.")

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
            spotify_results = spotify_client.search(query)
            results['spotify'] = spotify_results
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
    
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        
        with col1:
            st.markdown(f"**{track.get('title', 'Unknown Title')}**")
            st.markdown(f"*{track.get('artist', 'Unknown Artist')}*")
            if track.get('album'):
                st.markdown(f"Album: {track.get('album')}")
            
            # Source badge
            source_emoji = "🎵" if source == "spotify" else "📺"
            st.markdown(f"{source_emoji} {source.title()}")
        
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
                add_track_to_playlist(track, source)
        
        st.divider()

def play_track_from_search(track, source):
    """Play a track from search results"""
    try:
        # Convert search result to playable track format
        playable_track = {
            'title': track.get('title', 'Unknown Title'),
            'artist': track.get('artist', 'Unknown Artist'),
            'album': track.get('album', 'Unknown Album'),
            'url': track.get('url', ''),
            'source': source,
            'id': track.get('id')
        }
        
        # If it's from YouTube, get the stream URL
        if source == "youtube":
            youtube_client = YouTubeClient()
            stream_url = youtube_client.get_stream_url(track.get('url', ''))
            playable_track['stream_url'] = stream_url
        
        # Set as current track and play
        st.session_state.current_track = playable_track
        st.session_state.current_playlist = [playable_track]
        st.session_state.current_track_index = 0
        st.session_state.is_playing = True
        
        st.success(f"Now playing: {playable_track['title']} by {playable_track['artist']}")
        
    except Exception as e:
        st.error(f"Failed to play track: {str(e)}")

def add_track_to_playlist(track, source):
    """Add track to a user playlist"""
    
    # Convert to standard track format
    track_data = {
        'title': track.get('title', 'Unknown Title'),
        'artist': track.get('artist', 'Unknown Artist'),
        'album': track.get('album', 'Unknown Album'),
        'url': track.get('url', ''),
        'source': source,
        'id': track.get('id'),
        'added_date': str(st.session_state.get('current_time', ''))
    }
    
    # Show playlist selection
    playlist_names = list(st.session_state.playlists.keys())
    
    if not playlist_names:
        st.warning("No playlists found. Create a playlist first.")
        return
    
    # Create a form for playlist selection
    with st.form(f"add_to_playlist_{track.get('id', hash(str(track)))}"):
        selected_playlist = st.selectbox(
            "Select playlist",
            playlist_names,
            key=f"playlist_select_{track.get('id', hash(str(track)))}"
        )
        
        if st.form_submit_button("Add to Playlist"):
            if selected_playlist not in st.session_state.playlists:
                st.session_state.playlists[selected_playlist] = []
            
            # Check if track already exists in playlist
            track_exists = any(
                existing_track.get('id') == track_data.get('id') 
                for existing_track in st.session_state.playlists[selected_playlist]
            )
            
            if not track_exists:
                st.session_state.playlists[selected_playlist].append(track_data)
                st.success(f"Added '{track_data['title']}' to '{selected_playlist}'")
            else:
                st.warning("Track already exists in this playlist")
