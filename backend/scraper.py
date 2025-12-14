import time
import logging
import re
import random
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class LinkedInScraper:
    """
    LinkedIn Company Page Scraper using Selenium + BeautifulSoup
    """
    
    def __init__(self, headless=True, timeout=15):
        self.timeout = timeout
        self.headless = headless
        self.driver = None
        
    def _init_driver(self):
        """Initialize Selenium WebDriver"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless=new")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout * 3)
            logger.info("  Selenium WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f" Failed to initialize WebDriver: {e}")
            raise
    
    def _close_driver(self):
        """Close Selenium WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def _random_delay(self, min_sec=1, max_sec=3):
        """Add random delay"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
    
    def scrape_page(self, page_id):
        """Main scraping method"""
        self._init_driver()
        
        try:
            url = f"https://www.linkedin.com/company/{page_id}/"
            logger.info(f"🔗 Scraping: {url}")
            
            self.driver.get(url)
            self._random_delay(3, 5)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            page_data = self._extract_basic_info(soup, page_id, url)
            
            self._scroll_page()
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            page_data['posts'] = self._extract_posts(soup, page_id)
            page_data['employees'] = self._extract_employees(soup, page_id)
            
            logger.info(f"  Successfully scraped {page_id}")
            logger.info(f"     Final stats: {len(page_data['posts'])} posts, {len(page_data['employees'])} employees")
            
            return page_data
            
        except Exception as e:
            logger.error(f" Error scraping {page_id}: {e}")
            return None
        
        finally:
            self._close_driver()
    
    def _extract_basic_info(self, soup, page_id, url):
        """Extract basic page information"""
        try:
            page_data = {
                'id': page_id,
                'url': url,
                'name': '',
                'profile_pic_url': '',
                'description': '',
                'website': '',
                'industry': '',
                'followers_count': 0,
                'employees_count': 0,
                'employees_text': '',
                'specialities': '',
                'posts': [],
                'employees': [],
            }
            
            # Extract company name
            name_selectors = [
                ('h1', {}),
                ('meta', {'property': 'og:title'}),
                ('title', {}),
            ]
            
            for tag, attrs in name_selectors:
                elem = soup.find(tag, attrs)
                if elem:
                    if hasattr(elem, 'get_text'):
                        page_data['name'] = elem.get_text(strip=True).split('|')[0].strip()
                    else:
                        page_data['name'] = elem.get('content', page_id).split('|')[0].strip()
                    if page_data['name']:
                        break
            
            if not page_data['name']:
                page_data['name'] = page_id.replace('-', ' ').title()
            
            # Extract profile picture
            img_selectors = [
                ('img', {'class': re.compile(r'logo', re.IGNORECASE)}),
                ('img', {'alt': re.compile(page_data['name'], re.IGNORECASE)}),
                ('meta', {'property': 'og:image'}),
            ]
            
            for tag, attrs in img_selectors:
                elem = soup.find(tag, attrs)
                if elem:
                    if tag == 'img':
                        src = elem.get('src', '')
                        if src and 'http' in src:
                            page_data['profile_pic_url'] = src
                            logger.info(f"🖼️ Found profile image: {src[:50]}...")
                            break
                    else:
                        content = elem.get('content', '')
                        if content and 'http' in content:
                            page_data['profile_pic_url'] = content
                            logger.info(f"🖼️ Found profile image: {content[:50]}...")
                            break
            
            # Extract description
            desc_selectors = [
                ('p', {'class': re.compile(r'description|about', re.IGNORECASE)}),
                ('meta', {'name': 'description'}),
                ('meta', {'property': 'og:description'}),
            ]
            
            for tag, attrs in desc_selectors:
                elem = soup.find(tag, attrs)
                if elem:
                    if hasattr(elem, 'get_text'):
                        desc = elem.get_text(strip=True)
                    else:
                        desc = elem.get('content', '')
                    if desc and len(desc) > 20:
                        page_data['description'] = desc[:1000]
                        logger.info(f"📄 Found description: {len(desc)} chars")
                        break
            
            page_text = soup.get_text()
            
            # Extract followers
            follower_patterns = [
                (r'([\d,]+)\s*followers?', 1),
                (r'([\d,]+)K\s*followers?', 1000),
                (r'([\d,]+)M\s*followers?', 1000000),
                (r'([\d.]+)K\s*followers?', 1000),
                (r'([\d.]+)M\s*followers?', 1000000),
            ]
            
            for pattern, multiplier in follower_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    try:
                        num_str = match.group(1).replace(',', '')
                        num = float(num_str)
                        page_data['followers_count'] = int(num * multiplier)
                        logger.info(f"     Followers: {page_data['followers_count']:,}")
                        break
                    except:
                        continue
            
            # Extract employees
            employee_patterns = [
                r'(\d+)-(\d+)\s+employees?',
                r'(\d+)\+\s+employees?',
                r'(\d+)\s+employees?',
            ]
            
            for pattern in employee_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    try:
                        if len(match.groups()) == 2:
                            min_emp = int(match.group(1))
                            max_emp = int(match.group(2))
                            page_data['employees_text'] = f"{min_emp}-{max_emp}"
                            page_data['employees_count'] = max_emp
                            logger.info(f"👔 Employees: {page_data['employees_text']}")
                        else:
                            num = int(match.group(1))
                            if '+' in match.group(0):
                                page_data['employees_text'] = f"{num}+"
                            else:
                                page_data['employees_text'] = str(num)
                            page_data['employees_count'] = num
                            logger.info(f"👔 Employees: {page_data['employees_text']}")
                        break
                    except:
                        continue
            
            # Extract industry
            industry_keywords = ['industry', 'sector']
            for keyword in industry_keywords:
                pattern = rf'{keyword}[:\s]+([^\n\r]+)'
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    page_data['industry'] = match.group(1).strip()[:100]
                    break
            
            if not page_data['industry']:
                industry_elem = soup.find('meta', {'name': 'keywords'})
                if industry_elem:
                    page_data['industry'] = industry_elem.get('content', 'Not Specified')[:100]
            
            # Extract website
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'http' in href and 'linkedin.com' not in href and len(href) < 200:
                    page_data['website'] = href
                    break
            
            logger.info(f" Extracted basic info: {page_data['name']}")
            return page_data
            
        except Exception as e:
            logger.error(f"Error extracting basic info: {e}")
            return {
                'id': page_id,
                'url': url,
                'name': page_id.replace('-', ' ').title(),
                'profile_pic_url': '',
                'description': '',
                'website': '',
                'industry': '',
                'followers_count': 0,
                'employees_count': 0,
                'employees_text': '',
                'specialities': '',
                'posts': [],
                'employees': [],
            }
    
    def _scroll_page(self):
        """Scroll to load content"""
        try:
            for i in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/5 * {});".format(i+1))
                self._random_delay(1, 2)
            logger.info("📜 Scrolled page")
        except Exception as e:
            logger.debug(f"Error scrolling: {e}")
    
    def _extract_posts(self, soup, page_id):
        """Extract posts"""
        posts = []
        try:
            post_containers = soup.find_all(['article', 'div'], class_=re.compile(r'feed|post|update|share', re.IGNORECASE))
            
            logger.info(f"🔍 Found {len(post_containers)} potential post containers")
            
            for idx, container in enumerate(post_containers[:25]):
                try:
                    content = container.get_text(strip=True)
                    
                    if len(content) > 50:
                        likes = 0
                        comments = 0
                        shares = 0
                        
                        text = content.lower()
                        
                        likes_match = re.search(r'(\d+)\s*(?:like|reaction)', text)
                        if likes_match:
                            likes = int(likes_match.group(1))
                        
                        comments_match = re.search(r'(\d+)\s*comment', text)
                        if comments_match:
                            comments = int(comments_match.group(1))
                        
                        shares_match = re.search(r'(\d+)\s*share', text)
                        if shares_match:
                            shares = int(shares_match.group(1))
                        
                        post_data = {
                            'id': f"post_{idx}_{int(time.time())}",
                            'content': content[:500],
                            'likes_count': likes,
                            'comments_count': comments,
                            'shares_count': shares,
                        }
                        
                        posts.append(post_data)
                
                except Exception as e:
                    logger.debug(f"Error parsing post {idx}: {e}")
                    continue
            
            logger.info(f"📰 Extracted {len(posts)} posts")
            return posts
            
        except Exception as e:
            logger.error(f"Error extracting posts: {e}")
            return []
    
    def _extract_employees(self, soup, page_id):
        """Extract employees"""
        employees = []
        try:
            employee_containers = soup.find_all(['li', 'div', 'article'], class_=re.compile(r'employee|people|member|profile', re.IGNORECASE))
            
            logger.info(f"🔍 Found {len(employee_containers)} potential employee containers")
            
            for idx, container in enumerate(employee_containers[:50]):
                try:
                    name_elem = container.find(['span', 'h3', 'h4', 'a'], class_=re.compile(r'name|title', re.IGNORECASE))
                    
                    if not name_elem:
                        link = container.find('a', href=re.compile(r'/in/'))
                        if link:
                            name_elem = link
                    
                    if name_elem:
                        name = name_elem.get_text(strip=True)
                        
                        if 2 < len(name) < 100 and re.search(r'[a-zA-Z]', name):
                            headline_elem = container.find(['p', 'div', 'span'], class_=re.compile(r'headline|title|occupation', re.IGNORECASE))
                            headline = headline_elem.get_text(strip=True) if headline_elem else ''
                            
                            profile_url = ''
                            link = container.find('a', href=re.compile(r'/in/'))
                            if link:
                                href = link.get('href', '')
                                if href.startswith('http'):
                                    profile_url = href
                                elif href.startswith('/'):
                                    profile_url = f"https://www.linkedin.com{href}"
                            
                            emp_data = {
                                'id': f"emp_{idx}_{int(time.time())}",
                                'name': name,
                                'headline': headline[:200] if headline else 'Employee',
                                'profile_url': profile_url,
                            }
                            
                            employees.append(emp_data)
                
                except Exception as e:
                    logger.debug(f"Error parsing employee {idx}: {e}")
                    continue
            
            logger.info(f"👥 Extracted {len(employees)} employees")
            return employees
            
        except Exception as e:
            logger.error(f"Error extracting employees: {e}")
            return []


def scrape_linkedin_page(page_id):
    """Convenience function"""
    scraper = LinkedInScraper(headless=True)
    return scraper.scrape_page(page_id)
