import streamlit as st
import time
from utils.audio_manager import AudioManager

def render_player():
    """Render the music player component"""
    st.subheader("🎵 Music Player")
    
    if not st.session_state.current_track:
        st.info("No track selected. Search for music or select from your library.")
        return
    
    track = st.session_state.current_track
    audio_manager = st.session_state.audio_manager
    
    # Track information
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Album art placeholder (using emoji as we can't generate images)
        st.markdown("### 🎵")
    
    with col2:
        st.markdown(f"**{track.get('title', 'Unknown Title')}**")
        st.markdown(f"*{track.get('artist', 'Unknown Artist')}*")
        st.markdown(f"Album: {track.get('album', 'Unknown Album')}")
    
    # Player controls
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("⏮️", help="Previous track"):
            previous_track()
    
    with col2:
        if st.session_state.is_playing:
            if st.button("⏸️", help="Pause"):
                pause_track()
        else:
            if st.button("▶️", help="Play"):
                play_track()
    
    with col3:
        if st.button("⏭️", help="Next track"):
            next_track()
    
    with col4:
        if st.button("🔀", help="Shuffle"):
            shuffle_playlist()
    
    with col5:
        if st.button("🔁", help="Repeat"):
            toggle_repeat()
    
    # Progress bar (simulated)
    if st.session_state.is_playing:
        progress = st.progress(0.0)
        # In a real implementation, this would show actual playback progress
        for i in range(100):
            progress.progress(i / 100)
            time.sleep(0.01)
    
    # Playlist queue
    if st.session_state.current_playlist:
        with st.expander("📝 Current Queue"):
            for i, queue_track in enumerate(st.session_state.current_playlist):
                status = "▶️" if i == st.session_state.current_track_index else ""
                if st.button(
                    f"{status} {queue_track.get('title', 'Unknown')} - {queue_track.get('artist', 'Unknown')}",
                    key=f"queue_{i}",
                    use_container_width=True
                ):
                    st.session_state.current_track_index = i
                    st.session_state.current_track = queue_track
                    play_track()

def play_track():
    """Play the current track"""
    if st.session_state.current_track:
        track = st.session_state.current_track
        st.session_state.audio_manager.play(track)
        st.session_state.is_playing = True
        st.success(f"Now playing: {track.get('title', 'Unknown')}")

def pause_track():
    """Pause the current track"""
    st.session_state.audio_manager.pause()
    st.session_state.is_playing = False
    st.info("Playback paused")

def next_track():
    """Skip to next track in playlist"""
    if st.session_state.current_playlist:
        current_index = st.session_state.current_track_index
        if current_index < len(st.session_state.current_playlist) - 1:
            st.session_state.current_track_index = current_index + 1
            st.session_state.current_track = st.session_state.current_playlist[current_index + 1]
            play_track()
        else:
            st.warning("End of playlist")

def previous_track():
    """Go to previous track in playlist"""
    if st.session_state.current_playlist:
        current_index = st.session_state.current_track_index
        if current_index > 0:
            st.session_state.current_track_index = current_index - 1
            st.session_state.current_track = st.session_state.current_playlist[current_index - 1]
            play_track()
        else:
            st.warning("Already at first track")

def shuffle_playlist():
    """Shuffle the current playlist"""
    import random
    if st.session_state.current_playlist:
        current_track = st.session_state.current_track
        shuffled = st.session_state.current_playlist.copy()
        random.shuffle(shuffled)
        st.session_state.current_playlist = shuffled
        # Find the current track in the shuffled list
        for i, track in enumerate(shuffled):
            if track == current_track:
                st.session_state.current_track_index = i
                break
        st.success("Playlist shuffled!")

def toggle_repeat():
    """Toggle repeat mode"""
    if not hasattr(st.session_state, 'repeat_mode'):
        st.session_state.repeat_mode = False
    
    st.session_state.repeat_mode = not st.session_state.repeat_mode
    mode = "ON" if st.session_state.repeat_mode else "OFF"
    st.info(f"Repeat mode: {mode}")
