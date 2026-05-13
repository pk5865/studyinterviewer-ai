import requests
from bs4 import BeautifulSoup

def extract_text_from_web(url):
    """Extract readable text from a webpage URL (memory-safe)."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove non-content elements
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
            
        # Extract text & limit size for 8GB RAM safety
        text = soup.get_text(separator=' ', strip=True)
        return text[:4000] if text else "No readable content found."
        
    except Exception as e:
        print(f"🌐 Web parse error: {e}")
        return f"Error fetching webpage: {str(e)}"