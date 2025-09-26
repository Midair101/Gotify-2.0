import streamlit as st
import time

def set_volume():
    """Callback to set volume from the slider.
    This ensures the volume state is updated before any potential reruns.
    """
    st.session_state.volume = st.session_state.volume_slider # Sync the main volume state
    st.session_state.audio_manager.set_volume(st.session_state.volume)

def render_player():
    """Render the music player component"""

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
    
    # --- Vertical Layout for Sidebar ---

    # Album Art and Track Info
    album_art_url = track.get('album_art') or track.get('thumbnail')
    if album_art_url:
        st.image(album_art_url)
    st.markdown(f"**{track.get('title', 'Unknown Title')}**")
    st.caption(f"*{track.get('artist', 'Unknown Artist')}*")

    # Main Player Controls (above progress bar)
    _, c1, c2, c3, _ = st.columns([1.5, 1, 1, 1, 1.5])
    with c1:
        if st.button("⏮️", help="Previous track"):
            previous_track()
    with c2:
        if st.session_state.is_playing:
            if st.button("⏸️", help="Pause"):
                pause_track()
        else:
            if st.button("▶️", help="Play"):
                play_track(resume=True)
    with c3:
        if st.button("⏭️", help="Next track"):
            next_track()

    # Progress bar and seeking
    position = audio_manager.get_position()
    duration_ms = audio_manager.get_duration()

    if duration_ms > 0:
        # Use a slider for seeking
        new_position = st.slider(
            "Track Progress", 0.0, 1.0, position,
            label_visibility="collapsed", key="seek_slider",
            on_change=lambda: audio_manager.set_position(st.session_state.seek_slider)
        )
        if abs(new_position - position) > 0.01 and not st.session_state.is_playing:
            audio_manager.set_position(new_position)
            st.rerun()
        
        # Timestamps
        current_time_str = format_duration(position * duration_ms)
        total_time_str = format_duration(duration_ms)
        st.caption(f"{current_time_str} / {total_time_str}")

    else:
        st.progress(0)

    # Secondary Controls (Shuffle/Repeat) and Volume
    c1, c2, c3 = st.columns([1, 1, 3])
    with c1:
        if st.button("🔀", help="Shuffle"):
            shuffle_playlist()
    with c2:
        repeat_mode = st.session_state.get('repeat_mode', 'off')
        repeat_icons = {'off': '🔁', 'playlist': '🔁', 'track': '🔂'}
        if st.button(repeat_icons[repeat_mode], help="Toggle Repeat (Off -> Playlist -> Track)"):
            toggle_repeat()
    
    with c3:
        # Wrap slider in a div with a custom class to target with CSS
        st.markdown('<div class="volume-slider-container">', unsafe_allow_html=True)
        st.slider(
            "Volume", 0.0, 1.0, st.session_state.volume, 0.05,
            on_change=set_volume,
            key="volume_slider",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # To make the progress bar and seeking feel "live", force a rerun if playing.
    if st.session_state.is_playing:
        st.rerun() # Reruns to update the progress bar
    
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
