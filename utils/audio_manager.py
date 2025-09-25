import os
import pygame
from pathlib import Path

class AudioManager:
    """Manages audio playback using pygame"""
    
    def __init__(self):
        self.is_initialized = False
        self.current_file = None
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.7
        self.position = 0
        
        self._initialize_pygame()
    
    def _initialize_pygame(self):
        """Initialize pygame mixer for audio playback"""
        try:
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            self.is_initialized = True
        except Exception as e:
            print(f"Failed to initialize audio: {e}")
            self.is_initialized = False
    
    def play(self, track):
        """Play a track"""
        if not self.is_initialized:
            print("Audio system not initialized")
            return False
        
        try:
            # Handle different track sources
            if track.get('source') == 'local':
                file_path = track.get('file_path')
                if file_path and Path(file_path).exists():
                    return self._play_local_file(file_path)
                else:
                    print(f"Local file not found: {file_path}")
                    return False
            
            elif track.get('source') in ['youtube', 'spotify']:
                # For online tracks, we would need to get the stream URL
                stream_url = track.get('stream_url')
                if stream_url:
                    return self._play_stream(stream_url)
                else:
                    print("No stream URL available")
                    return False
            
            return False
            
        except Exception as e:
            print(f"Error playing track: {e}")
            return False
    
    def _play_local_file(self, file_path):
        """Play a local audio file"""
        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()
            
            self.current_file = file_path
            self.is_playing = True
            self.is_paused = False
            
            return True
            
        except Exception as e:
            print(f"Error playing local file: {e}")
            return False
    
    def _play_stream(self, stream_url):
        """Play an online stream (placeholder implementation)"""
        # In a real implementation, this would handle streaming audio
        # For now, we'll just indicate that streaming is not fully implemented
        print(f"Streaming not implemented for: {stream_url}")
        return False
    
    def pause(self):
        """Pause playback"""
        if self.is_initialized and self.is_playing:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False
    
    def resume(self):
        """Resume playback"""
        if self.is_initialized and self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.is_playing = True
    
    def stop(self):
        """Stop playback"""
        if self.is_initialized:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.is_paused = False
            self.current_file = None
    
    def set_volume(self, volume):
        """Set playback volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        if self.is_initialized:
            pygame.mixer.music.set_volume(self.volume)
    
    def get_volume(self):
        """Get current volume"""
        return self.volume
    
    def is_busy(self):
        """Check if audio is currently playing"""
        if self.is_initialized:
            return pygame.mixer.music.get_busy()
        return False
    
    def get_position(self):
        """Get current playback position (placeholder)"""
        # pygame doesn't provide easy position tracking
        # In a real implementation, you might use a different library
        return self.position
    
    def set_position(self, position):
        """Set playback position (placeholder)"""
        # pygame doesn't support seeking easily
        # In a real implementation, you might use a different library
        self.position = position
    
    def cleanup(self):
        """Clean up audio resources"""
        if self.is_initialized:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            self.is_initialized = False
