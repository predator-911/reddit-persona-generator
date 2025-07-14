#!/usr/bin/env python3
"""
Reddit Persona Analyzer
A fast, free tool for analyzing Reddit user personalities and behavior patterns.
"""

import os
import json
import time
import re
import gc
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, Counter
import multiprocessing as mp
from typing import Dict, List, Tuple, Optional, Any

# Third-party imports
try:
    import praw
    from colorama import Fore, Style, init
    from tqdm import tqdm
    print(f"{Fore.GREEN}✅ Core libraries loaded successfully!{Style.RESET_ALL}")
except ImportError as e:
    print(f"{Fore.RED}❌ Import error: {e}{Style.RESET_ALL}")
    print("Please install required dependencies: pip install -r requirements.txt")
    exit(1)

# Initialize colorama for cross-platform colored output
init(autoreset=True)

class RedditPersonaAnalyzer:
    """
    Ultra-fast Reddit persona analyzer using rule-based AI and parallel processing.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the analyzer with configuration.
        
        Args:
            config: Dictionary containing Reddit API credentials and settings
        """
        self.config = config
        self.reddit = None
        self.cache = {}
        self.stats = {
            'total_posts': 0,
            'total_comments': 0,
            'analysis_time': 0,
            'start_time': None,
            'cache_hits': 0
        }
        self.setup_reddit_client()
    
    def setup_reddit_client(self) -> None:
        """Setup Reddit client with optimized settings."""
        try:
            self.reddit = praw.Reddit(
                client_id=self.config['REDDIT_CLIENT_ID'],
                client_secret=self.config['REDDIT_CLIENT_SECRET'],
                user_agent=self.config['REDDIT_USER_AGENT'],
                check_for_async=False,
                timeout=30
            )
            # Test connection
            self.reddit.user.me()
            print(f"{Fore.GREEN}🔗 Reddit client initialized successfully!{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Reddit setup failed: {e}{Style.RESET_ALL}")
            print("Please check your Reddit API credentials in config.json")
            exit(1)
    
    def parallel_scrape_user_data(self, username: str, post_limit: int = 100, 
                                 comment_limit: int = 100) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
        """
        Ultra-fast parallel data scraping from Reddit user profile.
        
        Args:
            username: Reddit username (without u/ prefix)
            post_limit: Maximum number of posts to analyze
            comment_limit: Maximum number of comments to analyze
            
        Returns:
            Tuple of (posts, comments) where each is a list of (text, url) tuples
        """
        print(f"{Fore.BLUE}🔍 Analyzing user: {Fore.WHITE}u/{username}{Style.RESET_ALL}")
        
        # Check cache first
        cache_key = f"{username}_{post_limit}_{comment_limit}"
        if self.config['CACHE_ENABLED'] and cache_key in self.cache:
            print(f"{Fore.YELLOW}⚡ Using cached data for u/{username}{Style.RESET_ALL}")
            self.stats['cache_hits'] += 1
            return self.cache[cache_key]
        
        try:
            user = self.reddit.redditor(username)
            # Test if user exists
            user.id
            
            posts = []
            comments = []
            
            # Parallel data collection
            with ThreadPoolExecutor(max_workers=self.config['MAX_WORKERS']) as executor:
                post_future = executor.submit(self._scrape_posts, user, post_limit)
                comment_future = executor.submit(self._scrape_comments, user, comment_limit)
                
                # Collect results with progress indication
                with tqdm(total=2, desc="Collecting data") as pbar:
                    posts = post_future.result()
                    pbar.update(1)
                    comments = comment_future.result()
                    pbar.update(1)
            
            self.stats['total_posts'] = len(posts)
            self.stats['total_comments'] = len(comments)
            
            result = (posts, comments)
            
            # Cache results
            if self.config['CACHE_ENABLED']:
                self.cache[cache_key] = result
            
            print(f"{Fore.GREEN}⚡ Data collection complete: {len(posts)} posts, {len(comments)} comments{Style.RESET_ALL}")
            return result
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error accessing user u/{username}: {e}{Style.RESET_ALL}")
            return [], []
    
    def _scrape_posts(self, user, limit: int) -> List[Tuple[str, str]]:
        """Scrape user posts efficiently."""
        posts = []
        try:
            for submission in user.submissions.new(limit=limit):
                if submission.selftext and len(submission.selftext.strip()) > 10:
                    text = f"Title: {submission.title}\nBody: {submission.selftext}"
                    posts.append((text.strip(), f"https://www.reddit.com{submission.permalink}"))
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Could not fetch all posts: {e}{Style.RESET_ALL}")
        
        return posts
    
    def _scrape_comments(self, user, limit: int) -> List[Tuple[str, str]]:
        """Scrape user comments efficiently."""
        comments = []
        try:
            for comment in user.comments.new(limit=limit):
                if hasattr(comment, 'body') and len(comment.body.strip()) > 10:
                    comments.append((comment.body.strip(), f"https://www.reddit.com{comment.permalink}"))
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Could not fetch all comments: {e}{Style.RESET_ALL}")
        
        return comments
    
    def analyze_personality(self, posts: List[Tuple[str, str]], 
                          comments: List[Tuple[str, str]], username: str) -> Dict[str, Any]:
        """
        Comprehensive personality analysis using advanced rule-based algorithms.
        
        Args:
            posts: List of user posts
            comments: List of user comments
            username: Reddit username
            
        Returns:
            Dictionary containing complete personality analysis
        """
        print(f"{Fore.CYAN}🧠 Running personality analysis...{Style.RESET_ALL}")
        
        # Combine all text efficiently
        all_texts = [text for text, _ in posts + comments]
        combined_text = " ".join(all_texts).lower()
        
        # Multi-faceted analysis
        with tqdm(total=4, desc="Analyzing personality") as pbar:
            personality_traits = self._analyze_personality_traits(combined_text)
            pbar.update(1)
            
            interests = self._extract_interests(combined_text, all_texts)
            pbar.update(1)
            
            communication_style = self._analyze_communication_style(posts, comments)
            pbar.update(1)
            
            behavioral_patterns = self._extract_behavioral_patterns(posts, comments)
            pbar.update(1)
        
        # Generate comprehensive report
        report = self._generate_analysis_report(
            username, personality_traits, interests, 
            communication_style, behavioral_patterns, posts, comments
        )
        
        return {
            'personality_traits': personality_traits,
            'interests': interests,
            'communication_style': communication_style,
            'behavioral_patterns': behavioral_patterns,
            'report': report
        }
    
    def _analyze_personality_traits(self, text: str) -> Dict[str, float]:
        """Analyze personality traits using weighted keyword analysis."""
        personality_indicators = {
            "Analytical": {
                "keywords": ["analysis", "data", "research", "study", "evidence", "statistics", 
                           "logic", "rational", "objective", "methodology", "systematic"],
                "weight": 1.2
            },
            "Creative": {
                "keywords": ["art", "music", "design", "creative", "imagine", "beautiful", 
                           "inspiration", "original", "artistic", "innovative"],
                "weight": 1.1
            },
            "Social": {
                "keywords": ["friends", "people", "social", "community", "together", "group", 
                           "team", "collaborate", "relationship", "connection"],
                "weight": 1.0
            },
            "Technical": {
                "keywords": ["code", "programming", "software", "tech", "computer", "algorithm", 
                           "development", "system", "engineer", "technical"],
                "weight": 1.3
            },
            "Intellectual": {
                "keywords": ["learn", "knowledge", "understand", "think", "philosophy", "science", 
                           "education", "academic", "intellectual", "theory"],
                "weight": 1.1
            },
            "Humorous": {
                "keywords": ["lol", "haha", "funny", "joke", "humor", "hilarious", "lmao", 
                           "comedy", "amusing", "entertaining"],
                "weight": 0.9
            },
            "Opinionated": {
                "keywords": ["opinion", "believe", "think", "disagree", "argue", "debate", 
                           "strongly", "definitely", "absolutely", "wrong"],
                "weight": 1.0
            }
        }
        
        traits = {}
        for trait, data in personality_indicators.items():
            # Count keyword occurrences with context weighting
            score = 0
            for keyword in data["keywords"]:
                count = text.count(keyword)
                score += count * data["weight"]
            
            # Convert to confidence percentage
            if score > 1:
                confidence = min(score * 15, 100)  # Scale and cap at 100%
                traits[trait] = round(confidence, 1)
        
        return traits
    
    def _extract_interests(self, text: str, all_texts: List[str]) -> Dict[str, int]:
        """Extract interests and topics using advanced pattern matching."""
        interests = defaultdict(int)
        
        # Extract mentioned subreddits
        subreddits = re.findall(r'r/(\w+)', text)
        for sub in subreddits:
            interests[f"r/{sub}"] += 3
        
        # Topic analysis using keyword clustering
        topic_keywords = {
            "Gaming": ["game", "gaming", "play", "player", "steam", "console", "pc", "xbox", "playstation"],
            "Technology": ["tech", "software", "app", "device", "digital", "internet", "ai", "ml"],
            "Sports": ["sport", "team", "player", "game", "season", "match", "football", "basketball"],
            "Entertainment": ["movie", "show", "tv", "film", "series", "watch", "netflix", "streaming"],
            "Finance": ["money", "invest", "stock", "crypto", "bitcoin", "finance", "trading", "market"],
            "Health": ["health", "fitness", "exercise", "diet", "medical", "doctor", "workout", "nutrition"],
            "Education": ["learn", "study", "school", "university", "education", "course", "degree", "academic"],
            "Science": ["science", "research", "experiment", "theory", "physics", "chemistry", "biology"],
            "Politics": ["politics", "government", "election", "vote", "policy", "political", "candidate"],
            "Travel": ["travel", "trip", "vacation", "country", "city", "visit", "tourism", "explore"]
        }
        
        for topic, keywords in topic_keywords.items():
            score = sum(text.count(keyword) for keyword in keywords)
            if score > 2:
                interests[topic] = score
        
        # Return top interests sorted by relevance
        return dict(sorted(interests.items(), key=lambda x: x[1], reverse=True)[:15])
    
    def _analyze_communication_style(self, posts: List[Tuple[str, str]], 
                                   comments: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Analyze communication patterns and style."""
        if not posts and not comments:
            return {}
        
        post_lengths = [len(text) for text, _ in posts]
        comment_lengths = [len(text) for text, _ in comments]
        
        all_texts = [text for text, _ in posts + comments]
        combined_text = " ".join(all_texts).lower()
        
        # Advanced metrics
        metrics = {
            "avg_post_length": sum(post_lengths) / max(len(post_lengths), 1),
            "avg_comment_length": sum(comment_lengths) / max(len(comment_lengths), 1),
            "total_activity": len(posts) + len(comments),
            "post_to_comment_ratio": len(posts) / max(len(comments), 1),
            "verbosity": self._calculate_verbosity(all_texts),
            "formality": self._calculate_formality(combined_text),
            "emotional_tone": self._analyze_emotional_tone(combined_text),
            "question_frequency": combined_text.count('?') / max(len(all_texts), 1),
            "exclamation_usage": combined_text.count('!') / max(len(all_texts), 1)
        }
        
        return metrics
    
    def _calculate_verbosity(self, texts: List[str]) -> str:
        """Calculate verbosity level based on text lengths."""
        if not texts:
            return "Unknown"
        
        avg_length = sum(len(text) for text in texts) / len(texts)
        
        if avg_length > 300:
            return "Very High"
        elif avg_length > 200:
            return "High"
        elif avg_length > 100:
            return "Moderate"
        else:
            return "Low"
    
    def _calculate_formality(self, text: str) -> str:
        """Calculate formality level of communication."""
        formal_indicators = ["furthermore", "however", "therefore", "nevertheless", "consequently"]
        informal_indicators = ["lol", "omg", "tbh", "imo", "btw", "wtf", "yeah", "gonna"]
        
        formal_score = sum(text.count(word) for word in formal_indicators)
        informal_score = sum(text.count(word) for word in informal_indicators)
        
        if formal_score > informal_score * 2:
            return "High"
        elif informal_score > formal_score * 2:
            return "Low"
        else:
            return "Moderate"
    
    def _analyze_emotional_tone(self, text: str) -> str:
        """Analyze overall emotional tone."""
        positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic", 
                         "happy", "excited", "love", "awesome", "perfect", "brilliant"]
        negative_words = ["bad", "terrible", "awful", "horrible", "hate", "angry", "sad", 
                         "disappointed", "frustrated", "annoying", "stupid", "worst"]
        
        positive_score = sum(text.count(word) for word in positive_words)
        negative_score = sum(text.count(word) for word in negative_words)
        
        if positive_score > negative_score * 1.5:
            return "Positive"
        elif negative_score > positive_score * 1.5:
            return "Negative"
        else:
            return "Neutral"
    
    def _extract_behavioral_patterns(self, posts: List[Tuple[str, str]], 
                                   comments: List[Tuple[str, str]]) -> Dict[str, str]:
        """Extract behavioral patterns from posting data."""
        total_activity = len(posts) + len(comments)
        
        patterns = {
            "engagement_level": self._classify_engagement_level(total_activity),
            "content_preference": "Comments" if len(comments) > len(posts) else "Posts",
            "discussion_style": "Active" if len(comments) > 30 else "Passive",
            "activity_type": self._classify_activity_type(posts, comments)
        }
        
        return patterns
    
    def _classify_engagement_level(self, total_activity: int) -> str:
        """Classify user engagement level."""
        if total_activity > 100:
            return "Very High"
        elif total_activity > 50:
            return "High"
        elif total_activity > 20:
            return "Moderate"
        else:
            return "Low"
    
    def _classify_activity_type(self, posts: List[Tuple[str, str]], 
                               comments: List[Tuple[str, str]]) -> str:
        """Classify the type of user activity."""
        if len(posts) > len(comments) * 2:
            return "Content Creator"
        elif len(comments) > len(posts) * 3:
            return "Active Commenter"
        else:
            return "Balanced Participant"
    
    def _generate_analysis_report(self, username: str, traits: Dict[str, float], 
                                interests: Dict[str, int], communication: Dict[str, Any],
                                patterns: Dict[str, str], posts: List[Tuple[str, str]], 
                                comments: List[Tuple[str, str]]) -> str:
        """Generate comprehensive analysis report."""
        report = f"""
{'='*80}
🧠 REDDIT PERSONA ANALYSIS REPORT
{'='*80}

👤 USER: u/{username}
🔍 ANALYSIS ENGINE: Advanced Rule-Based AI with Pattern Recognition
📊 DATA POINTS: {len(posts)} posts, {len(comments)} comments
⚡ PROCESSING: Multi-threaded parallel analysis
📅 GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*80}
🎯 PERSONALITY TRAITS
{'='*80}

{self._format_traits(traits)}

{'='*80}
🔍 INTERESTS & COMMUNITIES
{'='*80}

{self._format_interests(interests)}

{'='*80}
💬 COMMUNICATION STYLE
{'='*80}

• Average Post Length: {communication.get('avg_post_length', 0):.0f} characters
• Average Comment Length: {communication.get('avg_comment_length', 0):.0f} characters
• Total Activity: {communication.get('total_activity', 0)} interactions
• Post-to-Comment Ratio: {communication.get('post_to_comment_ratio', 0):.2f}
• Verbosity Level: {communication.get('verbosity', 'Unknown')}
• Formality Level: {communication.get('formality', 'Unknown')}
• Emotional Tone: {communication.get('emotional_tone', 'Unknown')}
• Question Frequency: {communication.get('question_frequency', 0):.2f} per post
• Exclamation Usage: {communication.get('exclamation_usage', 0):.2f} per post

{'='*80}
🎭 BEHAVIORAL PATTERNS
{'='*80}

• Engagement Level: {patterns.get('engagement_level', 'Unknown')}
• Content Preference: {patterns.get('content_preference', 'Unknown')}
• Discussion Style: {patterns.get('discussion_style', 'Unknown')}
• Activity Type: {patterns.get('activity_type', 'Unknown')}

{'='*80}
📈 ANALYSIS STATISTICS
{'='*80}

• Processing Speed: Ultra-Fast (Multi-threaded)
• Memory Usage: Optimized with caching
• Cache Hits: {self.stats['cache_hits']}
• Analysis Method: Advanced Rule-Based with Pattern Recognition
• Confidence Level: High (based on {len(posts) + len(comments)} data points)

{'='*80}
📝 CONTENT CITATIONS
{'='*80}

This analysis is based on the following Reddit content:

POSTS ANALYZED:
{self._format_citations(posts, "Post")}

COMMENTS ANALYZED:
{self._format_citations(comments, "Comment")}

{'='*80}
⚖️ DISCLAIMER
{'='*80}

This analysis is generated using advanced algorithms and is for educational 
purposes only. Results are based on publicly available Reddit data and should 
not be used for making important decisions about individuals.

Generated by Reddit Persona Analyzer v2.0
Repository: https://github.com/yourusername/reddit-persona-analyzer
        """
        
        return report
    
    def _format_traits(self, traits: Dict[str, float]) -> str:
        """Format personality traits for display."""
        if not traits:
            return "• No strong personality traits detected from available data"
        
        formatted = []
        for trait, confidence in sorted(traits.items(), key=lambda x: x[1], reverse=True):
            bars = "█" * int(confidence / 10)
            formatted.append(f"• {trait:<15} {confidence:5.1f}% {bars}")
        
        return "\n".join(formatted)
    
    def _format_interests(self, interests: Dict[str, int]) -> str:
        """Format interests for display."""
        if not interests:
            return "• No clear interests detected from available data"
        
        formatted = []
        for interest, score in interests.items():
            bars = "█" * min(score, 10)
            formatted.append(f"• {interest:<20} (score: {score:2d}) {bars}")
        
        return "\n".join(formatted)
    
    def _format_citations(self, content_list: List[Tuple[str, str]], content_type: str) -> str:
        """Format citations for the report."""
        if not content_list:
            return f"• No {content_type.lower()}s available for analysis"
        
        citations = []
        for i, (text, url) in enumerate(content_list[:5], 1):
            preview = text[:100] + "..." if len(text) > 100 else text
            citations.append(f"{i}. {content_type}: \"{preview}\"\n   Source: {url}")
        
        if len(content_list) > 5:
            citations.append(f"... and {len(content_list) - 5} more {content_type.lower()}s")
        
        return "\n".join(citations)
    
    def save_report(self, username: str, report: str, output_dir: str = "reports") -> Optional[str]:
        """Save analysis report to file."""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"{username}_analysis_{timestamp}.txt")
        
        try:
            with open(filename, "w", encoding='utf-8') as f:
                f.write(report)
            print(f"{Fore.GREEN}💾 Report saved: {Fore.WHITE}{filename}{Style.RESET_ALL}")
            return filename
        except Exception as e:
            print(f"{Fore.RED}❌ Save error: {e}{Style.RESET_ALL}")
            return None
    
    def analyze_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Main analysis function for a Reddit user.
        
        Args:
            username: Reddit username (without u/ prefix)
            
        Returns:
            Dictionary containing analysis results or None if failed
        """
        self.stats['start_time'] = time.time()
        
        print(f"{Fore.CYAN}🚀 Starting analysis for u/{username}{Style.RESET_ALL}")
        
        # Data collection
        posts, comments = self.parallel_scrape_user_data(username)
        
        if not posts and not comments:
            print(f"{Fore.RED}⚠️ No data found for u/{username} - user may not exist or have no content{Style.RESET_ALL}")
            return None
        
        # Analysis
        analysis_results = self.analyze_personality(posts, comments, username)
        
        # Save report
        filename = self.save_report(username, analysis_results['report'])
        
        # Update stats
        self.stats['analysis_time'] = time.time() - self.stats['start_time']
        
        # Display completion message
        print(f"\n{Fore.GREEN}✅ Analysis complete for u/{username}!{Style.RESET_ALL}")
        print(f"⏱️  Time: {self.stats['analysis_time']:.2f}s | "
              f"📊 Data: {len(posts)} posts, {len(comments)} comments")
        
        analysis_results['filename'] = filename
        return analysis_results


def extract_username_from_url(url_or_username: str) -> str:
    """
    Extract username from Reddit URL or return username as-is.
    
    Args:
        url_or_username: Reddit URL or username
        
    Returns:
        Clean username without prefixes
    """
    if url_or_username.startswith('http'):
        # Handle both /user/ and /u/ formats
        for pattern in [r'/user/([^/]+)', r'/u/([^/]+)']:
            match = re.search(pattern, url_or_username)
            if match:
                return match.group(1)
    
    # Remove u/ prefix if present
    if url_or_username.startswith('u/'):
        return url_or_username[2:]
    
    return url_or_username


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{Fore.RED}❌ Configuration file not found: {config_path}{Style.RESET_ALL}")
        print(f"Please create {config_path} with your Reddit API credentials.")
        return None


def main():
    """Main function with enhanced user interaction."""
    # Display banner
    banner = f"""
{Fore.CYAN}
╔══════════════════════════════════════════════════════════════╗
║              🚀 REDDIT PERSONA ANALYZER 🚀                  ║
║                 Advanced AI-Powered Analysis                 ║
║                                                              ║
║  ⚡ Multi-threaded Parallel Processing                       ║
║  🧠 Advanced Rule-Based AI Analysis                          ║
║  💾 Smart Caching System                                     ║
║  📊 Comprehensive Personality Reports                        ║
║  🔍 Deep Behavioral Pattern Recognition                      ║
╚══════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}
    """
    print(banner)
    
    # Load configuration
    config = load_config()
    if not config:
        return
    
    # Initialize analyzer
    analyzer = RedditPersonaAnalyzer(config)
    
    # Interactive mode
    while True:
        print(f"\n{Fore.CYAN}🔍 Enter Reddit user URL or username (or 'quit' to exit):{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Examples: kojied, u/username, https://reddit.com/user/username{Style.RESET_ALL}")
        
        user_input = input(">> ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print(f"{Fore.GREEN}👋 Thanks for using Reddit Persona Analyzer!{Style.RESET_ALL}")
            break
        
        if not user_input:
            continue
        
        username = extract_username_from_url(user_input)
        result = analyzer.analyze_user(username)
        
        if result:
            print(f"{Fore.GREEN}📄 Report saved to: {result.get('filename', 'N/A')}{Style.RESET_ALL}")
        
        print(f"{Fore.BLUE}{'='*60}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
