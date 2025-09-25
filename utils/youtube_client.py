import os
import requests
import re
from typing import List, Dict, Optional
import yt_dlp

class YouTubeClient:
    """Client for searching and streaming YouTube videos"""
    
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY', '')
        self.base_url = 'https://www.googleapis.com/youtube/v3'
        
        # Configure yt-dlp
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }
    
    def search(self, query: str, max_results: int = 20) -> List[Dict]:
        """Search for music videos on YouTube"""
        if self.api_key:
            return self._search_with_api(query, max_results)
        else:
            return self._search_with_yt_dlp(query, max_results)
    
    def _search_with_api(self, query: str, max_results: int) -> List[Dict]:
        """Search using YouTube Data API"""
        try:
            params = {
                'part': 'snippet',
                'q': f"{query} music",
                'type': 'video',
                'maxResults': max_results,
                'order': 'relevance',
                'videoCategoryId': '10',  # Music category
                'key': self.api_key
            }
            
            response = requests.get(
                f'{self.base_url}/search',
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_api_results(data)
            else:
                print(f"YouTube API search failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error searching YouTube API: {e}")
            return []
    
    def _search_with_yt_dlp(self, query: str, max_results: int) -> List[Dict]:
        """Search using yt-dlp (fallback when no API key)"""
        try:
            search_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlistend': max_results,
            }
            
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                search_results = ydl.extract_info(
                    f"ytsearch{max_results}:{query} music",
                    download=False
                )
                
                if search_results and 'entries' in search_results:
                    return self._parse_yt_dlp_results(search_results['entries'])
                else:
                    return []
                    
        except Exception as e:
            print(f"Error searching with yt-dlp: {e}")
            return []
    
    def _parse_api_results(self, data: Dict) -> List[Dict]:
        """Parse YouTube API search results"""
        results = []
        
        for item in data.get('items', []):
            video_id = item['id']['videoId']
            snippet = item['snippet']
            
            # Try to extract artist and title from video title
            title_parts = self._parse_video_title(snippet['title'])
            
            result = {
                'id': video_id,
                'title': title_parts.get('title', snippet['title']),
                'artist': title_parts.get('artist', snippet['channelTitle']),
                'album': 'YouTube',
                'url': f"https://www.youtube.com/watch?v={video_id}",
                'thumbnail': snippet['thumbnails']['default']['url'],
                'channel': snippet['channelTitle'],
                'description': snippet['description'],
                'published_at': snippet['publishedAt'],
                'source': 'youtube'
            }
            
            results.append(result)
        
        return results
    
    def _parse_yt_dlp_results(self, entries: List[Dict]) -> List[Dict]:
        """Parse yt-dlp search results"""
        results = []
        
        for entry in entries:
            if not entry:
                continue
            
            # Try to extract artist and title from video title
            title_parts = self._parse_video_title(entry.get('title', ''))
            
            result = {
                'id': entry.get('id', ''),
                'title': title_parts.get('title', entry.get('title', 'Unknown')),
                'artist': title_parts.get('artist', entry.get('uploader', 'Unknown')),
                'album': 'YouTube',
                'url': entry.get('webpage_url', f"https://www.youtube.com/watch?v={entry.get('id', '')}"),
                'thumbnail': entry.get('thumbnail', ''),
                'channel': entry.get('uploader', 'Unknown'),
                'duration': entry.get('duration', 0),
                'view_count': entry.get('view_count', 0),
                'source': 'youtube'
            }
            
            results.append(result)
        
        return results
    
    def _parse_video_title(self, title: str) -> Dict[str, str]:
        """Try to extract artist and song title from video title"""
        # Common patterns for music videos
        patterns = [
            r'^(.+?)\s*[-–—]\s*(.+?)(?:\s*\(.*\)|\s*\[.*\])?$',  # Artist - Title
            r'^(.+?)\s*[:\|]\s*(.+?)(?:\s*\(.*\)|\s*\[.*\])?$',   # Artist : Title or Artist | Title
            r'^(.+?)\s*"(.+?)"',  # Artist "Title"
            r'^(.+?)\s*–\s*(.+?)(?:\s*\(.*\)|\s*\[.*\])?$',      # Artist – Title (em dash)
        ]
        
        for pattern in patterns:
            match = re.match(pattern, title.strip())
            if match:
                return {
                    'artist': match.group(1).strip(),
                    'title': match.group(2).strip()
                }
        
        # If no pattern matches, return the whole title as both
        return {
            'artist': 'Unknown Artist',
            'title': title.strip()
        }
    
    def get_stream_url(self, video_url: str) -> Optional[str]:
        """Get direct stream URL for a YouTube video"""
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                # Get the best audio format
                formats = info.get('formats', [])
                audio_formats = [f for f in formats if f.get('acodec') != 'none']
                
                if audio_formats:
                    # Sort by quality and get the best one
                    best_audio = max(audio_formats, key=lambda x: x.get('abr', 0))
                    return best_audio.get('url')
                
                return None
                
        except Exception as e:
            print(f"Error getting stream URL: {e}")
            return None
    
    def get_video_info(self, video_url: str) -> Optional[Dict]:
        """Get detailed information about a YouTube video"""
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(video_url, download=False)
                
                title_parts = self._parse_video_title(info.get('title', ''))
                
                return {
                    'id': info.get('id'),
                    'title': title_parts.get('title', info.get('title')),
                    'artist': title_parts.get('artist', info.get('uploader')),
                    'album': 'YouTube',
                    'duration': info.get('duration', 0),
                    'view_count': info.get('view_count', 0),
                    'like_count': info.get('like_count', 0),
                    'upload_date': info.get('upload_date'),
                    'description': info.get('description', ''),
                    'thumbnail': info.get('thumbnail'),
                    'url': video_url,
                    'source': 'youtube'
                }
                
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def download_audio(self, video_url: str, output_path: str = None) -> Optional[str]:
        """Download audio from YouTube video"""
        try:
            download_opts = self.ydl_opts.copy()
            if output_path:
                download_opts['outtmpl'] = output_path
            
            with yt_dlp.YoutubeDL(download_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                return ydl.prepare_filename(info)
                
        except Exception as e:
            print(f"Error downloading audio: {e}")
            return None
