from youtube_transcript_api import YouTubeTranscriptApi
import re

def extract_text_from_youtube(url):
    """
    Extract transcript text from a YouTube video URL.
    Returns cleaned text string for AI processing.
    """
    try:
        # Extract video ID from URL
        video_id = None
        if 'v=' in url:
            video_id = url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]
        
        if not video_id:
            return "Could not extract YouTube video ID from URL."
        
        # Fetch transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US'])
        
        # Combine transcript segments
        text = ' '.join([entry['text'] for entry in transcript])
        
        # Clean up
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text if text else "No transcript available for this video."
        
    except Exception as e:
        print(f"YouTube transcript error: {e}")
        return f"Error fetching transcript: {str(e)}"