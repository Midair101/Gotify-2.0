import streamlit as st
import time

def render_player():
    """Render the music player component"""
    st.subheader("🎵 Music Player")
    
    if not st.session_state.current_track:
        st.info("No track selected. Search for music or select from your library.")
        return
    
    track = st.session_state.current_track
    audio_manager = st.session_state.audio_manager

    # Handle song finishing
    if st.session_state.get('song_finished', False):
        st.session_state.song_finished = False # Reset flag
        next_track(autoplay=True) # Move to next track
        st.rerun()
    
    # Track information
    col1, col2 = st.columns([1, 3])
    
    with col1:
        album_art_url = track.get('album_art') or track.get('thumbnail')
        if album_art_url:
            st.image(album_art_url, width=100)
        else:
            st.markdown("### 🎵")
    
    with col2:
        st.markdown(f"**{track.get('title', 'Unknown Title')}**")
        st.markdown(f"*{track.get('artist', 'Unknown Artist')}*")
    
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
                play_track(resume=True)
    
    with col3:
        if st.button("⏭️", help="Next track"):
            next_track()
    
    with col4:
        if st.button("🔀", help="Shuffle"):
            shuffle_playlist()
    
    with col5:
        repeat_mode = st.session_state.get('repeat_mode', 'off')
        repeat_icons = {'off': '🔁', 'playlist': '🔁', 'track': '🔂'}
        repeat_colors = {'off': 'grey', 'playlist': 'green', 'track': 'green'}
        st.markdown(f"""
        <div style="text-align: center; font-size: 24px; color: {repeat_colors[repeat_mode]};">
            {repeat_icons[repeat_mode]}
        </div>
        """, unsafe_allow_html=True)
        if st.button("Repeat", key="repeat_button_hidden", help="Toggle Repeat (Off -> Playlist -> Track)"):
            toggle_repeat()
    
    # Progress bar and seeking
    position = audio_manager.get_position()
    duration_ms = audio_manager.get_duration()

    if duration_ms > 0:
        # Display timestamps
        current_time_str = format_duration(position * duration_ms)
        total_time_str = format_duration(duration_ms)
        
        # Use a slider for seeking
        new_position = st.slider(
            "Track Progress", 0.0, 1.0, position,
            label_visibility="collapsed", key="seek_slider",
            on_change=lambda: audio_manager.set_position(st.session_state.seek_slider)
        )
        
        st.markdown(f"<div style='display: flex; justify-content: space-between; font-size: 0.9em; color: grey;'><p>{current_time_str}</p><p>{total_time_str}</p></div>", unsafe_allow_html=True)

        if abs(new_position - position) > 0.01 and not st.session_state.is_playing:
            audio_manager.set_position(new_position)
            st.rerun()
    else:
        st.progress(0)

    # To make the progress bar and seeking feel "live", force a rerun if playing.
    if st.session_state.is_playing:
        time.sleep(0.5) # Update roughly twice a second
        st.rerun()
    
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
 
def format_duration(ms: int) -> str:
    """Formats duration in milliseconds to MM:SS"""
    if ms is None or ms < 0:
        return "00:00"
    seconds = int((ms / 1000) % 60)
    minutes = int((ms / (1000 * 60)) % 60)
    return f"{minutes:02d}:{seconds:02d}"

def play_track(resume=False):
    """Play the current track, or resume if paused."""
    if st.session_state.current_track:
        track = st.session_state.current_track
        audio_manager = st.session_state.audio_manager

        if resume and not audio_manager.player.is_playing():
            audio_manager.resume()
        else:
            audio_manager.play_track(track)
        st.success(f"Playing: {track.get('title', 'Unknown')}")
        
        # Optimistically update the UI and rerun
        st.session_state.is_playing = True
        st.rerun()

def pause_track():
    """Pause the current track"""
    st.session_state.audio_manager.pause()
    st.session_state.is_playing = False
    st.info("Playback paused")
    st.rerun()

def next_track(autoplay=False):
    """Skip to next track in playlist"""
    if st.session_state.current_playlist:
        current_index = st.session_state.current_track_index
        playlist_len = len(st.session_state.current_playlist)
        repeat_mode = st.session_state.get('repeat_mode', 'off')

        next_index = current_index + 1

        if repeat_mode == 'track' and autoplay:
            # Replay the same track
            play_track()
            return

        if next_index < playlist_len:
            st.session_state.current_track_index = next_index
            st.session_state.current_track = st.session_state.current_playlist[next_index]
            play_track()
        elif repeat_mode == 'playlist':
            # Loop back to the start
            st.session_state.current_track_index = 0
            st.session_state.current_track = st.session_state.current_playlist[0]
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
    modes = ['off', 'playlist', 'track']
    current_mode = st.session_state.get('repeat_mode', 'off')
    try:
        current_index = modes.index(current_mode)
        next_index = (current_index + 1) % len(modes)
        st.session_state.repeat_mode = modes[next_index]
    except ValueError:
        st.session_state.repeat_mode = 'off'
    
    mode_text = st.session_state.repeat_mode.replace('_', ' ').title()
    st.toast(f"Repeat mode: {mode_text}")
    st.rerun()
