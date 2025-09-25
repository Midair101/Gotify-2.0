import requests
import socket

def check_internet_connection(timeout: int = 5) -> bool:
    """
    Check if internet connection is available
    
    Args:
        timeout: Connection timeout in seconds
        
    Returns:
        bool: True if connected to internet, False otherwise
    """
    try:
        # Try to connect to a reliable host
        response = requests.get(
            'https://www.google.com',
            timeout=timeout,
            headers={'User-Agent': 'Gotify Music Player'}
        )
        return response.status_code == 200
    except (requests.RequestException, socket.timeout):
        try:
            # Fallback: try DNS resolution
            socket.create_connection(("8.8.8.8", 53), timeout=timeout)
            return True
        except (socket.timeout, socket.error):
            return False

def test_spotify_api_connection() -> bool:
    """
    Test if Spotify API is accessible
    
    Returns:
        bool: True if Spotify API is accessible, False otherwise
    """
    try:
        response = requests.get(
            'https://api.spotify.com/v1/',
            timeout=5,
            headers={'User-Agent': 'Gotify Music Player'}
        )
        # Spotify API returns 401 for unauthenticated requests, which is expected
        return response.status_code in [200, 401]
    except requests.RequestException:
        return False

def test_youtube_api_connection() -> bool:
    """
    Test if YouTube API is accessible
    
    Returns:
        bool: True if YouTube API is accessible, False otherwise
    """
    try:
        response = requests.get(
            'https://www.googleapis.com/youtube/v3/',
            timeout=5,
            headers={'User-Agent': 'Gotify Music Player'}
        )
        # YouTube API returns 400 for requests without parameters, which is expected
        return response.status_code in [200, 400]
    except requests.RequestException:
        return False

def get_network_status() -> dict:
    """
    Get comprehensive network status information
    
    Returns:
        dict: Network status information
    """
    status = {
        'internet': False,
        'spotify_api': False,
        'youtube_api': False,
        'overall': False
    }
    
    try:
        # Check general internet connectivity
        status['internet'] = check_internet_connection()
        
        if status['internet']:
            # Check specific API endpoints
            status['spotify_api'] = test_spotify_api_connection()
            status['youtube_api'] = test_youtube_api_connection()
        
        # Overall status is true if internet is available
        status['overall'] = status['internet']
        
    except Exception as e:
        print(f"Error checking network status: {e}")
        # All status values remain False
    
    return status

def get_public_ip() -> str:
    """
    Get the public IP address
    
    Returns:
        str: Public IP address or 'Unknown' if failed
    """
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        return response.text.strip()
    except requests.RequestException:
        return 'Unknown'

def ping_host(host: str, port: int = 80, timeout: int = 3) -> bool:
    """
    Ping a specific host and port
    
    Args:
        host: Hostname or IP address
        port: Port number
        timeout: Connection timeout in seconds
        
    Returns:
        bool: True if host is reachable, False otherwise
    """
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except (socket.timeout, socket.error):
        return False

def get_connection_speed() -> dict:
    """
    Estimate connection speed by downloading a small file
    
    Returns:
        dict: Connection speed information
    """
    import time
    
    try:
        # Use a small file for speed test
        test_url = 'https://www.google.com/favicon.ico'
        start_time = time.time()
        
        response = requests.get(test_url, timeout=10)
        end_time = time.time()
        
        if response.status_code == 200:
            duration = end_time - start_time
            size_bytes = len(response.content)
            speed_bps = size_bytes / duration if duration > 0 else 0
            speed_kbps = speed_bps / 1024
            
            return {
                'success': True,
                'duration_seconds': round(duration, 2),
                'size_bytes': size_bytes,
                'speed_bps': round(speed_bps, 2),
                'speed_kbps': round(speed_kbps, 2),
                'quality': get_connection_quality(speed_kbps)
            }
        else:
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_connection_quality(speed_kbps: float) -> str:
    """
    Determine connection quality based on speed
    
    Args:
        speed_kbps: Connection speed in KB/s
        
    Returns:
        str: Connection quality description
    """
    if speed_kbps >= 1000:  # 1 MB/s or higher
        return 'Excellent'
    elif speed_kbps >= 500:  # 500 KB/s or higher
        return 'Good'
    elif speed_kbps >= 100:  # 100 KB/s or higher
        return 'Fair'
    elif speed_kbps >= 50:   # 50 KB/s or higher
        return 'Poor'
    else:
        return 'Very Poor'

def check_streaming_capability() -> dict:
    """
    Check if connection is suitable for music streaming
    
    Returns:
        dict: Streaming capability information
    """
    network_status = get_network_status()
    
    if not network_status['internet']:
        return {
            'capable': False,
            'reason': 'No internet connection',
            'recommendations': ['Connect to internet', 'Use offline mode']
        }
    
    speed_test = get_connection_speed()
    
    if not speed_test['success']:
        return {
            'capable': True,  # Assume capable if we can't test
            'reason': 'Could not test connection speed',
            'recommendations': ['Connection appears stable']
        }
    
    speed_kbps = speed_test.get('speed_kbps', 0)
    
    # Music streaming typically needs 128-320 kbps
    # We'll be conservative and recommend at least 64 KB/s (512 kbps)
    if speed_kbps >= 64:
        return {
            'capable': True,
            'quality': speed_test.get('quality', 'Unknown'),
            'speed_kbps': speed_kbps,
            'recommendations': ['Good for high-quality streaming']
        }
    elif speed_kbps >= 32:
        return {
            'capable': True,
            'quality': 'Limited',
            'speed_kbps': speed_kbps,
            'recommendations': ['Use lower quality settings', 'Consider downloading for offline playback']
        }
    else:
        return {
            'capable': False,
            'reason': 'Connection too slow for streaming',
            'speed_kbps': speed_kbps,
            'recommendations': ['Use offline mode only', 'Improve internet connection']
        }
