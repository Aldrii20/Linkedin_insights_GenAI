import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def extract_page_id_from_url(url):
    """
    Extract LinkedIn page ID from URL.
    Supports both company pages AND personal profiles.
    
    Examples:
    - https://www.linkedin.com/company/deepsolv -> deepsolv
    - linkedin.com/company/deepsolv -> deepsolv
    - https://www.linkedin.com/in/aldrin-thomas/ -> aldrin-thomas
    - deepsolv -> deepsolv
    """
    if not url:
        return None
    
    # If it's already just an ID (no slashes)
    if '/' not in url and 'linkedin.com' not in url:
        return url.lower().strip()
    
    # Extract from URL - try both /company/ and /in/ patterns
    patterns = [
        r'/company/([a-zA-Z0-9\-]+)',  # Company pages: /company/deepsolv
        r'/in/([a-zA-Z0-9\-]+)',        # Personal profiles: /in/aldrin-thomas
        r'linkedin\.com/company/([a-zA-Z0-9\-]+)',
        r'linkedin\.com/in/([a-zA-Z0-9\-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1).lower().strip()
    
    return None


def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    return text.strip()


def format_number(num):
    """Format large numbers (e.g., 1000 -> 1K)"""
    if not num:
        return "0"
    
    try:
        num = int(num)
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        return str(num)
    except:
        return "0"


def parse_follower_count(text):
    """
    Parse follower count from text.
    Examples:
    - "1,234,567 followers" -> 1234567
    - "1.2M followers" -> 1200000
    - "1K followers" -> 1000
    """
    if not text:
        return 0
    
    text = text.lower().strip()
    
    # Remove common words
    text = text.replace('followers', '').replace('follower', '').replace('people', '').strip()
    
    # Handle M (millions)
    if 'm' in text:
        match = re.search(r'([\d.]+)\s*m', text)
        if match:
            try:
                return int(float(match.group(1)) * 1000000)
            except:
                return 0
    
    # Handle K (thousands)
    if 'k' in text:
        match = re.search(r'([\d.]+)\s*k', text)
        if match:
            try:
                return int(float(match.group(1)) * 1000)
            except:
                return 0
    
    # Handle plain numbers
    text = text.replace(',', '').replace('.', '')
    match = re.search(r'([\d]+)', text)
    if match:
        try:
            return int(match.group(1))
        except:
            return 0
    
    return 0


def validate_url(url):
    """
    Validate if URL is a valid LinkedIn company page OR personal profile URL
    """
    if not url:
        return False
    
    # Check if it's a LinkedIn URL (company or personal profile) or has page ID format
    patterns = [
        r'linkedin\.com/company/[a-zA-Z0-9\-]+',
        r'linkedin\.com/in/[a-zA-Z0-9\-]+',
        r'^[a-zA-Z0-9\-]+$',  # Just the ID
    ]
    
    for pattern in patterns:
        if re.search(pattern, url):
            return True
    
    return False


def paginate_list(items, page=1, per_page=10):
    """
    Paginate a list of items.
    
    Args:
        items: List of items to paginate
        page: Page number (1-indexed)
        per_page: Items per page
    
    Returns:
        Dict with paginated data and metadata
    """
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 10
    
    total = len(items)
    total_pages = max(1, (total + per_page - 1) // per_page)
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    paginated_items = items[start_idx:end_idx]
    
    return {
        'items': paginated_items,
        'pagination': {
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
        }
    }


def format_response(success, data=None, message=None, status_code=200):
    """Format API response"""
    response = {
        'success': success,
        'status_code': status_code,
    }
    
    if data is not None:
        response['data'] = data
    
    if message:
        response['message'] = message
    
    return response, status_code


def log_error(error_msg, exception=None):
    """Log error with optional exception details"""
    logger.error(f"{error_msg}")
    if exception:
        logger.exception(exception)
