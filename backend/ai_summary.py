import logging

logger = logging.getLogger(__name__)


class AISummaryGenerator:
    """
    Generate AI-powered summaries using Groq API (Free tier available)
    Requires GROQ_API_KEY environment variable
    """
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None
        
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
                logger.info("    Groq client initialized")
            except Exception as e:
                logger.error(f" Failed to initialize Groq client: {e}")
                self.client = None
    
    def generate_summary(self, page_data):
        """
        Generate AI summary for a LinkedIn page
        
        Args:
            page_data: Dictionary with page information
        
        Returns:
            AI-generated summary string
        """
        if not self.client:
            logger.warning("⚠️  Groq API key not configured, returning mock summary")
            return self._generate_mock_summary(page_data)
        
        try:
            prompt = self._build_prompt(page_data)
            
            logger.info("     Generating AI summary with Groq...")
            
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama-3.3-70b-versatile",  # UPDATED MODEL
                max_tokens=500,
                temperature=0.7,
            )
            
            summary = chat_completion.choices[0].message.content
            logger.info("    AI summary generated successfully with Groq")
            
            return summary
            
        except Exception as e:
            logger.error(f" Error generating summary with Groq: {e}")
            logger.info("⚠️  Falling back to mock summary")
            return self._generate_mock_summary(page_data)
    
    def _build_prompt(self, page_data):
        """Build the prompt for AI summary"""
        
        posts_summary = ""
        if page_data.get('posts'):
            posts_text = "\n".join([p.get('content', '')[:100] for p in page_data['posts'][:5] if p.get('content')])
            if posts_text:
                posts_summary = f"\n\nRecent Posts:\n{posts_text}"
        
        employees_count = len(page_data.get('employees', []))
        
        prompt = f"""Analyze this LinkedIn company profile and provide a professional, concise 2-3 paragraph summary:

Company Name: {page_data.get('name', 'Unknown')}
Description: {page_data.get('description', 'No description available')}
Industry: {page_data.get('industry', 'Not specified')}
Followers: {page_data.get('followers_count', 0):,}
Employees Found: {employees_count}
Website: {page_data.get('website', 'Not specified')}
Specialties: {page_data.get('specialities', 'Not specified')}
{posts_summary}

Please provide:
1. A brief overview of what this company does
2. Their market position and size (based on followers/employees)
3. Key insights about their industry and focus areas

Keep it professional and suitable for business analysis.
"""
        
        return prompt
    
    def _generate_mock_summary(self, page_data):
        """
        Generate a mock summary when API is not available.
        """
        
        name = page_data.get('name', 'This Company')
        description = page_data.get('description', '')
        followers = page_data.get('followers_count', 0)
        employees = len(page_data.get('employees', []))
        industry = page_data.get('industry', 'Professional Services')
        
        followers_text = self._format_followers(followers)
        
        summary = f"{name} is a professional organization in the {industry} sector with {followers_text} followers on LinkedIn"
        
        if employees > 0:
            summary += f" and approximately {employees} team members featured on the platform"
        
        summary += ". "
        
        if description:
            desc_snippet = description[:200]
            if len(description) > 200:
                desc_snippet += "..."
            summary += f"\n\nThe company describes itself as: {desc_snippet}\n\n"
        else:
            summary += "\n\n"
        
        summary += f"Based on their LinkedIn presence, {name} maintains an active professional community with regular engagement through posts and updates. "
        
        if followers > 100000:
            summary += f"With {followers_text} followers, the company demonstrates a significant industry presence and extensive professional network. "
        elif followers > 10000:
            summary += f"With {followers_text} followers, the company shows a solid market presence and growing professional community. "
        else:
            summary += f"With {followers_text} followers, the company is building its professional network and market presence. "
        
        if employees > 50:
            summary += f"The team of {employees}+ professionals suggests an established organization with significant operational capacity."
        elif employees > 10:
            summary += f"The team of {employees} professionals indicates a growing organization with focused expertise."
        else:
            summary += f"The company showcases a lean, focused team dedicated to their mission."
        
        return summary
    
    def _format_followers(self, count):
        """Format follower count for readability"""
        if count >= 1000000:
            return f"{count/1000000:.1f}M"
        elif count >= 1000:
            return f"{count/1000:.1f}K"
        return str(count)


def generate_summary(page_data, api_key=None):
    """
    Convenience function to generate summary
    
    Args:
        page_data: Dictionary with page information
        api_key: Optional Groq API key
    
    Returns:
        AI-generated summary string
    """
    generator = AISummaryGenerator(api_key=api_key)
    return generator.generate_summary(page_data)
