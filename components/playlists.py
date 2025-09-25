import streamlit as st
import json
from pathlib import Path

def render_playlists():
    """Render the playlist management page"""
    st.header("📝 Playlists")
    
    # Playlist management tabs
    tab1, tab2 = st.tabs(["📋 My Playlists", "➕ Create Playlist"])
    
    with tab1:
        render_playlist_list()
    
    with tab2:
        render_create_playlist()

def render_playlist_list():
    """Display all user playlists"""
    playlists = st.session_state.playlists
    
    if not playlists:
        st.info("You haven't created any playlists yet. Use the 'Create Playlist' tab to get started!")
        return
    
    # Display playlists
    for playlist_name, tracks in playlists.items():
        with st.expander(f"📝 {playlist_name} ({len(tracks)} tracks)", expanded=False):
            
            # Playlist controls
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("▶️ Play All", key=f"play_playlist_{playlist_name}"):
                    play_playlist(playlist_name)
            
            with col2:
                if st.button("🔀 Shuffle", key=f"shuffle_playlist_{playlist_name}"):
                    shuffle_and_play_playlist(playlist_name)
            
            with col3:
                if st.button("✏️ Rename", key=f"rename_playlist_{playlist_name}"):
                    rename_playlist(playlist_name)
            
            with col4:
                if st.button("🗑️ Delete", key=f"delete_playlist_{playlist_name}"):
                    delete_playlist(playlist_name)
            
            st.divider()
            
            # Display tracks in playlist
            if tracks:
                for i, track in enumerate(tracks):
                    display_playlist_track(track, i, playlist_name)
            else:
                st.info("This playlist is empty. Add some tracks from your library or search results.")

def render_create_playlist():
    """Interface for creating new playlists"""
    st.subheader("Create New Playlist")
    
    with st.form("create_playlist_form"):
        playlist_name = st.text_input(
            "Playlist Name",
            placeholder="Enter playlist name...",
            help="Choose a unique name for your playlist"
        )
        
        playlist_description = st.text_area(
            "Description (Optional)",
            placeholder="Describe your playlist...",
            help="Add a description for your playlist"
        )
        
        is_public = st.checkbox("Make playlist public", value=False)
        
        submitted = st.form_submit_button("🎵 Create Playlist", type="primary")
        
        if submitted:
            if not playlist_name.strip():
                st.error("Please enter a playlist name")
            elif playlist_name in st.session_state.playlists:
                st.error("A playlist with this name already exists")
            else:
                # Create new playlist
                st.session_state.playlists[playlist_name] = []
                
                # Save playlist metadata (if needed)
                playlist_metadata = {
                    'name': playlist_name,
                    'description': playlist_description,
                    'is_public': is_public,
                    'created_date': str(st.session_state.get('current_time', '')),
                    'track_count': 0
                }
                
                save_playlists()
                st.success(f"✅ Created playlist '{playlist_name}'!")
                st.rerun()
    
    # Quick playlist templates
    st.subheader("🚀 Quick Start Templates")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎸 Rock Favorites", use_container_width=True):
            create_template_playlist("Rock Favorites", "My favorite rock songs")
    
    with col2:
        if st.button("🎵 Recently Played", use_container_width=True):
            create_template_playlist("Recently Played", "Songs I've been listening to lately")
    
    with col3:
        if st.button("💖 Liked Songs", use_container_width=True):
            create_template_playlist("Liked Songs", "Songs I've liked")

def display_playlist_track(track, index, playlist_name):
    """Display a single track in a playlist"""
    col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 1, 1, 1])
    
    with col1:
        source_emoji = "🎵" if track.get('source') == 'spotify' else "📺" if track.get('source') == 'youtube' else "💿"
        st.write(f"{source_emoji} **{track.get('title', 'Unknown Title')}**")
    
    with col2:
        st.write(f"👨‍🎤 {track.get('artist', 'Unknown Artist')}")
    
    with col3:
        st.write(f"💿 {track.get('album', 'Unknown Album')}")
    
    with col4:
        if st.button("▶️", key=f"play_track_{playlist_name}_{index}", help="Play"):
            play_track_from_playlist(track, playlist_name, index)
    
    with col5:
        if st.button("⬆️", key=f"move_up_{playlist_name}_{index}", help="Move up"):
            move_track_up(playlist_name, index)
    
    with col6:
        if st.button("🗑️", key=f"remove_track_{playlist_name}_{index}", help="Remove"):
            remove_track_from_playlist(playlist_name, index)

def play_playlist(playlist_name):
    """Play all tracks in a playlist"""
    tracks = st.session_state.playlists.get(playlist_name, [])
    
    if not tracks:
        st.warning("Playlist is empty")
        return
    
    st.session_state.current_playlist = tracks.copy()
    st.session_state.current_track_index = 0
    st.session_state.current_track = tracks[0]
    st.session_state.is_playing = True
    
    st.success(f"▶️ Playing playlist '{playlist_name}' ({len(tracks)} tracks)")

def shuffle_and_play_playlist(playlist_name):
    """Shuffle and play a playlist"""
    import random
    
    tracks = st.session_state.playlists.get(playlist_name, [])
    
    if not tracks:
        st.warning("Playlist is empty")
        return
    
    shuffled_tracks = tracks.copy()
    random.shuffle(shuffled_tracks)
    
    st.session_state.current_playlist = shuffled_tracks
    st.session_state.current_track_index = 0
    st.session_state.current_track = shuffled_tracks[0]
    st.session_state.is_playing = True
    
    st.success(f"🔀 Shuffling and playing '{playlist_name}' ({len(tracks)} tracks)")

def play_track_from_playlist(track, playlist_name, track_index):
    """Play a specific track from a playlist"""
    tracks = st.session_state.playlists.get(playlist_name, [])
    
    st.session_state.current_playlist = tracks.copy()
    st.session_state.current_track_index = track_index
    st.session_state.current_track = track
    st.session_state.is_playing = True
    
    st.success(f"▶️ Playing: {track.get('title', 'Unknown')} from '{playlist_name}'")

def move_track_up(playlist_name, track_index):
    """Move a track up in the playlist"""
    tracks = st.session_state.playlists.get(playlist_name, [])
    
    if track_index > 0:
        # Swap tracks
        tracks[track_index], tracks[track_index - 1] = tracks[track_index - 1], tracks[track_index]
        save_playlists()
        st.success("Track moved up")
        st.rerun()
    else:
        st.warning("Track is already at the top")

def remove_track_from_playlist(playlist_name, track_index):
    """Remove a track from the playlist"""
    tracks = st.session_state.playlists.get(playlist_name, [])
    
    if 0 <= track_index < len(tracks):
        removed_track = tracks.pop(track_index)
        save_playlists()
        st.success(f"Removed '{removed_track.get('title', 'Unknown')}' from playlist")
        st.rerun()
    else:
        st.error("Invalid track index")

def rename_playlist(old_name):
    """Rename a playlist"""
    new_name = st.text_input(
        f"Rename '{old_name}' to:",
        value=old_name,
        key=f"rename_input_{old_name}"
    )
    
    if st.button("✅ Confirm Rename", key=f"confirm_rename_{old_name}"):
        if new_name and new_name != old_name:
            if new_name in st.session_state.playlists:
                st.error("A playlist with this name already exists")
            else:
                # Rename playlist
                st.session_state.playlists[new_name] = st.session_state.playlists.pop(old_name)
                save_playlists()
                st.success(f"Renamed playlist to '{new_name}'")
                st.rerun()
        else:
            st.warning("Please enter a different name")

def delete_playlist(playlist_name):
    """Delete a playlist with confirmation"""
    st.warning(f"Are you sure you want to delete '{playlist_name}'?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Yes, Delete", key=f"confirm_delete_{playlist_name}", type="primary"):
            del st.session_state.playlists[playlist_name]
            save_playlists()
            st.success(f"Deleted playlist '{playlist_name}'")
            st.rerun()
    
    with col2:
        if st.button("❌ Cancel", key=f"cancel_delete_{playlist_name}"):
            st.info("Delete cancelled")

def create_template_playlist(name, description):
    """Create a playlist from template"""
    if name in st.session_state.playlists:
        st.error(f"Playlist '{name}' already exists")
    else:
        st.session_state.playlists[name] = []
        save_playlists()
        st.success(f"Created playlist '{name}'")
        st.rerun()

def save_playlists():
    """Save playlists to local storage"""
    # In a real application, this would save to a file or database
    # For now, playlists are stored in session state
    playlists_file = Path("data/playlists.json")
    playlists_file.parent.mkdir(exist_ok=True)
    
    with open(playlists_file, 'w') as f:
        json.dump(st.session_state.playlists, f, indent=2)

def load_playlists():
    """Load playlists from local storage"""
    playlists_file = Path("data/playlists.json")
    
    if playlists_file.exists():
        with open(playlists_file, 'r') as f:
            return json.load(f)
    
    return {}
