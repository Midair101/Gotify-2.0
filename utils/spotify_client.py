import os
import requests
import base64
from typing import List, Dict, Optional

class SpotifyClient:
    """Client for interacting with Spotify Web API"""
    
    def __init__(self):
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID', '')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET', '')
        self.base_url = 'https://api.spotify.com/v1'
        self.access_token = None
        
        if self.client_id and self.client_secret:
            self._get_access_token()
    
    def _get_access_token(self):
        """Get access token using client credentials flow"""
        try:
            # Encode credentials
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            # Request token
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {'grant_type': 'client_credentials'}
            
            response = requests.post(
                'https://accounts.spotify.com/api/token',
                headers=headers,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                return True
            else:
                print(f"Failed to get Spotify token: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error getting Spotify access token: {e}")
            return False
    
    def search(self, query: str, search_type: str = 'track', limit: int = 20) -> List[Dict]:
        """Search for tracks, artists, or albums on Spotify"""
        if not self.access_token:
            print("No Spotify access token available")
            return []
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            params = {
                'q': query,
                'type': search_type,
                'limit': limit,
                'market': 'US'
            }
            
            response = requests.get(
                f'{self.base_url}/search',
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_search_results(data, search_type)
            elif response.status_code == 401:
                # Token might be expired, try to refresh
                if self._get_access_token():
                    return self.search(query, search_type, limit)
                else:
                    print("Failed to refresh Spotify token")
                    return []
            else:
                print(f"Spotify search failed: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error searching Spotify: {e}")
            return []
    
    def _parse_search_results(self, data: Dict, search_type: str) -> List[Dict]:
        """Parse Spotify search results into standardized format"""
        results = []
        
        if search_type == 'track' and 'tracks' in data:
            for track in data['tracks']['items']:
                result = {
                    'id': track['id'],
                    'title': track['name'],
                    'artist': ', '.join([artist['name'] for artist in track['artists']]),
                    'album': track['album']['name'],
                    'duration': track['duration_ms'],
                    'popularity': track['popularity'],
                    'url': track['external_urls']['spotify'],
                    'preview_url': track.get('preview_url'),
                    'source': 'spotify'
                }
                
                # Add album art if available
                if track['album']['images']:
                    result['album_art'] = track['album']['images'][0]['url']
                
                results.append(result)
        
        elif search_type == 'artist' and 'artists' in data:
            for artist in data['artists']['items']:
                result = {
                    'id': artist['id'],
                    'name': artist['name'],
                    'popularity': artist['popularity'],
                    'url': artist['external_urls']['spotify'],
                    'followers': artist['followers']['total'],
                    'genres': artist['genres'],
                    'source': 'spotify'
                }
                
                if artist['images']:
                    result['image'] = artist['images'][0]['url']
                
                results.append(result)
        
        elif search_type == 'album' and 'albums' in data:
            for album in data['albums']['items']:
                result = {
                    'id': album['id'],
                    'name': album['name'],
                    'artist': ', '.join([artist['name'] for artist in album['artists']]),
                    'release_date': album['release_date'],
                    'total_tracks': album['total_tracks'],
                    'url': album['external_urls']['spotify'],
                    'source': 'spotify'
                }
                
                if album['images']:
                    result['album_art'] = album['images'][0]['url']
                
                results.append(result)
        
        return results
    
    def get_track_details(self, track_id: str) -> Optional[Dict]:
        """Get detailed information about a specific track"""
        if not self.access_token:
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(
                f'{self.base_url}/tracks/{track_id}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                track = response.json()
                return self._parse_track_details(track)
            else:
                print(f"Failed to get track details: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error getting track details: {e}")
            return None
    
    def _parse_track_details(self, track: Dict) -> Dict:
        """Parse detailed track information"""
        result = {
            'id': track['id'],
            'title': track['name'],
            'artist': ', '.join([artist['name'] for artist in track['artists']]),
            'album': track['album']['name'],
            'duration': track['duration_ms'],
            'popularity': track['popularity'],
            'url': track['external_urls']['spotify'],
            'preview_url': track.get('preview_url'),
            'explicit': track['explicit'],
            'track_number': track['track_number'],
            'disc_number': track['disc_number'],
            'source': 'spotify'
        }
        
        # Add album information
        album = track['album']
        result['album_details'] = {
            'id': album['id'],
            'name': album['name'],
            'release_date': album['release_date'],
            'total_tracks': album['total_tracks']
        }
        
        # Add album art
        if album['images']:
            result['album_art'] = album['images'][0]['url']
        
        # Add artist details
        result['artist_details'] = []
        for artist in track['artists']:
            result['artist_details'].append({
                'id': artist['id'],
                'name': artist['name'],
                'url': artist['external_urls']['spotify']
            })
        
        return result
    
    def get_recommendations(self, seed_tracks: List[str] = None, seed_artists: List[str] = None, 
                           seed_genres: List[str] = None, limit: int = 20) -> List[Dict]:
        """Get track recommendations based on seeds"""
        if not self.access_token:
            return []
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            params = {
                'limit': limit
            }
            
            if seed_tracks:
                params['seed_tracks'] = ','.join(seed_tracks[:5])  # Max 5 seeds
            if seed_artists:
                params['seed_artists'] = ','.join(seed_artists[:5])
            if seed_genres:
                params['seed_genres'] = ','.join(seed_genres[:5])
            
            response = requests.get(
                f'{self.base_url}/recommendations',
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_search_results({'tracks': data}, 'track')
            else:
                print(f"Failed to get recommendations: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return []
