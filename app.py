import streamlit as st
import os
import json
from pathlib import Path

# Import components
from components.player import render_player
from components.search import render_search
from components.library import render_library
from components.playlists import render_playlists
from utils.network_utils import check_internet_connection
from utils.audio_manager import AudioManager

# Configure page
st.set_page_config(
    page_title="Gotify - Music Streaming",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def initialize_session_state():
    if 'current_track' not in st.session_state:
        st.session_state.current_track = None
    if 'is_playing' not in st.session_state:
        st.session_state.is_playing = False
    if 'current_playlist' not in st.session_state:
        st.session_state.current_playlist = []
    if 'current_track_index' not in st.session_state:
        st.session_state.current_track_index = 0
    if 'volume' not in st.session_state:
        st.session_state.volume = 0.7
    if 'audio_manager' not in st.session_state:
        st.session_state.audio_manager = AudioManager()
    if 'local_library' not in st.session_state:
        st.session_state.local_library = load_local_library()
    if 'playlists' not in st.session_state:
        st.session_state.playlists = {}
    if 'network_connected' not in st.session_state:
        st.session_state.network_connected = check_internet_connection()
    if 'page' not in st.session_state:
        st.session_state.page = "🏠 Home"

def load_local_library():
    """Load local music library from JSON file"""
    library_file = Path("data/local_library.json")
    if library_file.exists():
        with open(library_file, 'r') as f:
            return json.load(f)
    return {"tracks": [], "artists": {}, "albums": {}}

def save_local_library():
    """Save local music library to JSON file"""
    library_file = Path("data/local_library.json")
    library_file.parent.mkdir(exist_ok=True)
    with open(library_file, 'w') as f:
        json.dump(st.session_state.local_library, f, indent=2)

def main():
    initialize_session_state()
    
    # Custom CSS for Spotify-like appearance
    st.markdown("""
    <style>
    /* Main app background */
    .stApp {
        background-color: #121212;
        color: #ffffff;
    }

    /* Card for displaying tracks */
    .track-card {
        background-color: #181818;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        transition: background-color 0.2s;
    }
    .track-card:hover {
        background-color: #282828;
    }

    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: #040404;
    }

    .main-content {
        /* No longer need padding since player is in sidebar */
    }

    /* Hide the volume slider's value tooltip by targeting its container */
    .volume-slider-container div[data-testid="stSlider"] > div[data-baseweb="slider"] > div:nth-child(3) {
        display: none;
    }

    </style>
    """, unsafe_allow_html=True)
    
    # Header
    # Sidebar navigation
    with st.sidebar:
        st.title("🎵 Gotify")
        st.caption("Your personal music streamer")
        # Network status
        if st.session_state.network_connected:
            st.success("🌐 Online")
        else:
            st.warning("📶 Offline")
            
        if st.button("🔄 Refresh Connection"):
            st.session_state.network_connected = check_internet_connection()
            st.rerun()
        
        st.divider()
        
        # Navigation
        page_options = ["🏠 Home", "🔍 Search", "📚 Library", "📝 Playlists"]
        
        # Find the index of the current page for the selectbox
        try:
            current_page_index = page_options.index(st.session_state.page)
        except ValueError:
            current_page_index = 0 # Default to Home if page is invalid

        st.session_state.page = st.selectbox(
            "Navigate",
            page_options,
            index=current_page_index
        )
        
        st.divider()
        
        # Quick stats
        st.metric("Local Tracks", len(st.session_state.local_library.get("tracks", [])))
        st.metric("Playlists", len(st.session_state.playlists))

        # --- Music Player in Sidebar ---
        st.divider()
        st.subheader("Now Playing")
        render_player()
    
    # Main content area
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    if st.session_state.page == "🏠 Home":
        render_home()
    elif st.session_state.page == "🔍 Search":
        render_search()
    elif st.session_state.page == "📚 Library":
        render_library()
    elif st.session_state.page == "📝 Playlists":
        render_playlists()
    st.markdown('</div>', unsafe_allow_html=True)
    

def render_home():
    """Render the home page with recently played and recommendations"""
    st.header("🏠 Welcome to Gotify")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎵 Now Playing")
        if st.session_state.current_track:
            track = st.session_state.current_track
            st.markdown(f"""
            <div class="track-card">
                <h4>{track.get('title', 'Unknown Title')}</h4>
                <p>by {track.get('artist', 'Unknown Artist')}</p>
                <p>from {track.get('album', 'Unknown Album')}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No track currently playing")
    
    with col2:
        st.subheader("📊 Quick Stats")
        
        # Display library statistics
        local_tracks = len(st.session_state.local_library.get("tracks", []))
        total_playlists = len(st.session_state.playlists)
        
        st.metric("Local Library", f"{local_tracks} tracks")
        st.metric("Your Playlists", total_playlists)
        
        if st.session_state.network_connected:
            st.success("Online features available")
        else:
            st.warning("Offline mode - local library only")
    
    # Recent activity
    st.subheader("🕒 Recent Activity")
    if st.session_state.current_playlist:
        st.write("**Current Playlist:**")
        for i, track in enumerate(st.session_state.current_playlist[:5]):
            status = "▶️" if i == st.session_state.current_track_index else "⏸️"
            st.write(f"{status} {track.get('title', 'Unknown')} - {track.get('artist', 'Unknown')}")
    else:
        st.info("No recent activity")
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Search Music", use_container_width=True):
            st.session_state.page = "🔍 Search"
            st.rerun()
    
    with col2:
        if st.button("📚 Browse Library", use_container_width=True):
            st.session_state.page = "📚 Library"
            st.rerun()
    
    with col3:
        if st.button("📝 Manage Playlists", use_container_width=True):
            st.session_state.page = "📝 Playlists"
            st.rerun()

if __name__ == "__main__":
    main()
