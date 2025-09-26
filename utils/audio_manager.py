from pathlib import Path
import vlc
import yt_dlp
import streamlit as st

class AudioManager:
    """Manages audio playback using python-vlc."""

    def __init__(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.track_info = None
        
        # Event handling
        self.event_manager = self.player.event_manager()
        self.event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self.song_finished_callback)
        self.event_manager.event_attach(vlc.EventType.MediaPlayerPlaying, lambda e: self.update_playing_state(True))
        self.event_manager.event_attach(vlc.EventType.MediaPlayerPaused, lambda e: self.update_playing_state(False))

    def _get_youtube_stream_url(self, video_id):
        """Get the best audio stream URL from a YouTube video ID."""
        if not video_id:
            return None

        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'force_generic_extractor': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                return info['url']
        except Exception as e:
            st.error(f"Error getting audio stream: {e}")
            return None

    def play_track(self, track):
        """Play a track, fetching stream URL if it's from YouTube."""
        self.stop()
        if not track:
            st.warning("No track provided to play.")
            return

        self.track_info = track
        source_type = track.get('source', 'local')
        media = None

        if source_type == 'youtube' and track.get('id'):
            stream_url = self._get_youtube_stream_url(track.get('id'))
            if stream_url:
                media = self.instance.media_new(stream_url)
        elif source_type == 'local' and track.get('file_path'):
            file_path = Path(track['file_path'])
            if file_path.exists():
                media = self.instance.media_new(str(file_path))
            else:
                st.error(f"Local file not found: {file_path}")
        else:
            st.warning(f"Playback for source type '{source_type}' is not implemented.")

        if media:
            self.player.set_media(media)
            self.player.play()
            st.session_state.is_playing = True
        else:
            st.session_state.is_playing = False

    def pause(self):
        if self.player.is_playing():
            self.player.pause()
            st.session_state.is_playing = False

    def resume(self):
        if not self.player.is_playing():
            self.player.play()
            st.session_state.is_playing = True

    def stop(self):
        self.player.stop()
        st.session_state.is_playing = False

    def set_volume(self, volume):
        """Set volume from 0.0 to 1.0"""
        self.player.audio_set_volume(int(volume * 100))

    def get_position(self):
        """Get current playback position (0.0 to 1.0)."""
        return self.player.get_position()

    def get_duration(self):
        """Get total duration of the track in milliseconds."""
        return self.player.get_length()

    def set_position(self, position):
        """Set playback position (0.0 to 1.0)."""
        self.player.set_position(position)

    def update_playing_state(self, is_playing):
        """Callback to update session state based on player events."""
        st.session_state.is_playing = is_playing

    def song_finished_callback(self, event):
        """
        Callback triggered when a song finishes.
        This will be used to trigger the 'next_track' logic in the UI.
        We set a flag in the session state that the UI can check on the next rerun.
        """
        st.session_state.is_playing = False
        # Using a flag is a safe way to communicate from a callback thread to Streamlit
        st.session_state.song_finished = True
