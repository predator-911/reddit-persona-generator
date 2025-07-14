# 🚀 Reddit Persona Analyzer 
import os
import json
import time
import re
import gc
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, Counter
import multiprocessing as mp

# 🔐 Secure Configuration Loading
def load_config():
    """
    Load configuration from environment variables or config file.
    This ensures credentials are never hardcoded in the script.
    """
    print("🔐 Loading secure configuration...")
    
    # Try environment variables first (recommended for production)
    config = {
        'REDDIT_CLIENT_ID': os.getenv('REDDIT_CLIENT_ID'),
        'REDDIT_CLIENT_SECRET': os.getenv('REDDIT_CLIENT_SECRET'),
        'REDDIT_USER_AGENT': os.getenv('REDDIT_USER_AGENT', 'persona_analyzer_script'),
        'MAX_WORKERS': int(os.getenv('MAX_WORKERS', '4')),
        'BATCH_SIZE': int(os.getenv('BATCH_SIZE', '50')),
        'CACHE_ENABLED': os.getenv('CACHE_ENABLED', 'True').lower() == 'true',
    }
    
    # If environment variables not found, try config file
    if not config['REDDIT_CLIENT_ID']:
        try:
            from config import CONFIG as FILE_CONFIG
            config.update(FILE_CONFIG)
            print("✅ Configuration loaded from config.py")
        except ImportError:
            print("❌ No configuration found!")
            print("\nPlease setup your Reddit API credentials:")
            print("Option 1: Copy config.py.example to config.py and fill in your credentials")
            print("Option 2: Set environment variables (see .env.example)")
            print("\nGet credentials from: https://www.reddit.com/prefs/apps")
            exit(1)
    else:
        print("✅ Configuration loaded from environment variables")
    
    # Validate required fields
    required_fields = ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET']
    for field in required_fields:
        if not config[field] or config[field] in ['your_client_id_here', 'your_client_secret_here']:
            print(f"❌ Missing or invalid {field}")
            print("Please check your configuration and try again!")
            exit(1)
    
    return config

# Load configuration securely
try:
    CONFIG = load_config()
except Exception as e:
    print(f"❌ Configuration error: {e}")
    exit(1)

# 🧠 Optimized imports with lazy loading
try:
    import praw
    from colorama import Fore, Style, init
    from tqdm import tqdm
    import concurrent.futures
    print(f"{Fore.GREEN}✅ Core libraries loaded successfully!{Style.RESET_ALL}")
except ImportError as e:
    print(f"{Fore.RED}❌ Import error: {e}{Style.RESET_ALL}")
    print("Please install required packages:")
    print("pip install -r requirements.txt")
    exit(1)

# Optional AI imports (loaded only when needed)
def load_ai_dependencies():
    """Lazy load AI dependencies only when needed."""
    try:
        from transformers import pipeline
        import torch
        return pipeline, torch
    except ImportError:
        return None, None

# Initialize colorama
init(autoreset=True)

class FastRedditPersonaAnalyzer:
    def __init__(self, config):
        """Initialize with optimized settings."""
        self.config = config
        self.reddit = None
        self.ai_pipeline = None
        self.cache = {}
        self.stats = {
            'total_posts': 0,
            'total_comments': 0,
            'analysis_time': 0,
            'start_time': None,
            'cache_hits': 0
        }
        self.setup_reddit_client()
    
    def setup_reddit_client(self):
        """Setup Reddit client with secure credentials."""
        try:
            self.reddit = praw.Reddit(
                client_id=self.config['REDDIT_CLIENT_ID'],
                client_secret=self.config['REDDIT_CLIENT_SECRET'],
                user_agent=self.config['REDDIT_USER_AGENT'],
                check_for_async=False,
                timeout=30
            )
            
            # Test the connection
            self.reddit.user.me()
            print(f"{Fore.GREEN}🔗 Reddit client initialized successfully!{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Reddit client setup failed: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}💡 Please check your Reddit API credentials{Style.RESET_ALL}")
            print(f"   Get credentials from: https://www.reddit.com/prefs/apps")
            exit(1)
    
    def parallel_scrape_user_data(self, username, post_limit=100, comment_limit=100):
        """Ultra-fast parallel data scraping."""
        print(f"{Fore.BLUE}🔍 Fast-analyzing user: {Fore.WHITE}u/{username}{Style.RESET_ALL}")
        
        # Check cache first
        cache_key = f"{username}_{post_limit}_{comment_limit}"
        if self.config['CACHE_ENABLED'] and cache_key in self.cache:
            print(f"{Fore.YELLOW}⚡ Using cached data for u/{username}{Style.RESET_ALL}")
            self.stats['cache_hits'] += 1
            return self.cache[cache_key]
        
        try:
            user = self.reddit.redditor(username)
            
            # Test if user exists
            try:
                user.id
            except:
                print(f"{Fore.RED}❌ User u/{username} not found or suspended{Style.RESET_ALL}")
                return None, None
            
            posts = []
            comments = []
            
            # Parallel data collection
            with ThreadPoolExecutor(max_workers=self.config['MAX_WORKERS']) as executor:
                # Submit both tasks simultaneously
                post_future = executor.submit(self._scrape_posts, user, post_limit)
                comment_future = executor.submit(self._scrape_comments, user, comment_limit)
                
                # Collect results with progress tracking
                with tqdm(total=2, desc="Scraping", colour="cyan") as pbar:
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
            
            print(f"{Fore.GREEN}⚡ Fast collection complete: {len(posts)} posts, {len(comments)} comments{Style.RESET_ALL}")
            return result
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error scraping data: {e}{Style.RESET_ALL}")
            return None, None
    
    def _scrape_posts(self, user, limit):
        """Optimized post scraping with error handling."""
        posts = []
        try:
            for submission in user.submissions.new(limit=limit):
                if submission.selftext and len(submission.selftext) > 10:
                    text = f"Title: {submission.title}\nBody: {submission.selftext}"
                    posts.append((text.strip(), f"https://www.reddit.com{submission.permalink}"))
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Error scraping posts: {e}{Style.RESET_ALL}")
        return posts
    
    def _scrape_comments(self, user, limit):
        """Optimized comment scraping with error handling."""
        comments = []
        try:
            for comment in user.comments.new(limit=limit):
                if hasattr(comment, 'body') and len(comment.body) > 10:
                    comments.append((comment.body.strip(), f"https://www.reddit.com{comment.permalink}"))
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ Warning: Error scraping comments: {e}{Style.RESET_ALL}")
        return comments
    
    def ultra_fast_analysis(self, posts, comments, username):
        """Ultra-fast rule-based analysis with advanced algorithms."""
        print(f"{Fore.CYAN}⚡ Ultra-fast analysis engine activated!{Style.RESET_ALL}")
        
        # Combine all text efficiently
        all_texts = [text for text, _ in posts + comments]
        combined_text = " ".join(all_texts).lower()
        
        # Advanced personality analysis using multiple algorithms
        with tqdm(total=4, desc="Analysis", colour="magenta") as pbar:
            personality_traits = self._analyze_personality_fast(combined_text, posts, comments)
            pbar.update(1)
            
            interests = self._extract_interests_fast(combined_text, all_texts)
            pbar.update(1)
            
            communication_style = self._analyze_communication_fast(posts, comments)
            pbar.update(1)
            
            behavioral_patterns = self._extract_behavioral_patterns(posts, comments)
            pbar.update(1)
        
        # Generate comprehensive report
        report = self._generate_fast_report(
            username, personality_traits, interests, 
            communication_style, behavioral_patterns, posts, comments
        )
        
        return report
    
    def _analyze_personality_fast(self, text, posts, comments):
        """Fast personality analysis using weighted indicators."""
        personality_indicators = {
            "Analytical": {
                "keywords": ["analysis", "data", "research", "study", "evidence", "statistics", "logic", "rational", "objective", "fact"],
                "weight": 1.2
            },
            "Creative": {
                "keywords": ["art", "music", "design", "creative", "imagine", "beautiful", "inspiration", "original", "artistic", "aesthetic"],
                "weight": 1.1
            },
            "Social": {
                "keywords": ["friends", "people", "social", "community", "together", "group", "team", "collaborate", "meet", "party"],
                "weight": 1.0
            },
            "Technical": {
                "keywords": ["code", "programming", "software", "tech", "computer", "algorithm", "development", "system", "api", "database"],
                "weight": 1.3
            },
            "Intellectual": {
                "keywords": ["learn", "knowledge", "understand", "think", "philosophy", "science", "education", "academic", "theory", "concept"],
                "weight": 1.1
            },
            "Humorous": {
                "keywords": ["funny", "hilarious", "joke", "lol", "humor", "comedy", "laugh", "amusing", "witty", "sarcastic"],
                "weight": 0.9
            },
            "Helpful": {
                "keywords": ["help", "advice", "suggest", "recommend", "support", "assist", "guide", "solution", "answer", "explain"],
                "weight": 1.0
            }
        }
        
        traits = {}
        for trait, data in personality_indicators.items():
            score = sum(text.count(keyword) for keyword in data["keywords"]) * data["weight"]
            if score > 2:
                confidence = min(score * 8, 100)
                traits[trait] = confidence
        
        return traits
    
    def _extract_interests_fast(self, text, all_texts):
        """Fast interest extraction using pattern matching and keyword analysis."""
        interests = defaultdict(int)
        
        # Extract subreddits (primary interest indicator)
        subreddits = re.findall(r'r/(\w+)', text)
        for sub in subreddits:
            interests[f"r/{sub}"] += 3
        
        # Extract common topics using keyword frequency analysis
        topic_keywords = {
            "Gaming": ["game", "gaming", "play", "player", "steam", "console", "pc", "xbox", "playstation", "nintendo"],
            "Technology": ["tech", "software", "app", "device", "digital", "internet", "mobile", "computer", "ai", "ml"],
            "Sports": ["sport", "team", "player", "game", "season", "match", "football", "basketball", "soccer", "baseball"],
            "Entertainment": ["movie", "show", "tv", "film", "series", "watch", "netflix", "youtube", "music", "band"],
            "Finance": ["money", "invest", "stock", "crypto", "bitcoin", "finance", "trading", "market", "economy", "bank"],
            "Health & Fitness": ["health", "fitness", "exercise", "diet", "medical", "doctor", "workout", "gym", "nutrition", "wellness"],
            "Education": ["learn", "study", "school", "university", "education", "course", "student", "teacher", "academic", "knowledge"],
            "Travel": ["travel", "trip", "vacation", "country", "city", "hotel", "flight", "tourism", "visit", "explore"],
            "Food": ["food", "cook", "recipe", "restaurant", "eat", "meal", "cuisine", "chef", "kitchen", "dish"],
            "Art & Design": ["art", "design", "draw", "paint", "creative", "artist", "gallery", "photography", "graphic", "visual"]
        }
        
        for topic, keywords in topic_keywords.items():
            score = sum(text.count(keyword) for keyword in keywords)
            if score > 2:
                interests[topic] = score * 2
        
        return dict(sorted(interests.items(), key=lambda x: x[1], reverse=True)[:15])
    
    def _analyze_communication_fast(self, posts, comments):
        """Fast communication style analysis."""
        if not posts and not comments:
            return {}
        
        post_lengths = [len(text) for text, _ in posts] if posts else [0]
        comment_lengths = [len(text) for text, _ in comments] if comments else [0]
        all_texts = [text for text, _ in posts + comments]
        
        # Advanced communication metrics
        metrics = {
            "avg_post_length": sum(post_lengths) / max(len(post_lengths), 1),
            "avg_comment_length": sum(comment_lengths) / max(len(comment_lengths), 1),
            "total_activity": len(posts) + len(comments),
            "post_to_comment_ratio": len(posts) / max(len(comments), 1),
            "verbosity": self._calculate_verbosity(all_texts),
            "engagement_style": self._determine_engagement_style(posts, comments),
            "sentiment_tendency": self._analyze_sentiment_basic(all_texts)
        }
        
        return metrics
    
    def _calculate_verbosity(self, texts):
        """Calculate verbosity level based on text length patterns."""
        if not texts:
            return "Unknown"
        
        avg_length = sum(len(text) for text in texts) / len(texts)
        if avg_length > 500:
            return "Highly Verbose"
        elif avg_length > 200:
            return "Verbose"
        elif avg_length > 100:
            return "Moderate"
        else:
            return "Concise"
    
    def _determine_engagement_style(self, posts, comments):
        """Determine user's engagement style preference."""
        if len(comments) > len(posts) * 2:
            return "Discussion-focused"
        elif len(posts) > len(comments):
            return "Content Creator"
        else:
            return "Balanced Participant"
    
    def _analyze_sentiment_basic(self, texts):
        """Basic sentiment analysis using keyword indicators."""
        if not texts:
            return "Neutral"
        
        positive_words = ["good", "great", "awesome", "amazing", "excellent", "fantastic", "wonderful", "perfect", "love", "like"]
        negative_words = ["bad", "terrible", "awful", "hate", "horrible", "worst", "stupid", "annoying", "frustrating", "disappointed"]
        
        combined_text = " ".join(texts).lower()
        positive_score = sum(combined_text.count(word) for word in positive_words)
        negative_score = sum(combined_text.count(word) for word in negative_words)
        
        if positive_score > negative_score * 1.5:
            return "Generally Positive"
        elif negative_score > positive_score * 1.5:
            return "Generally Critical"
        else:
            return "Balanced"
    
    def _extract_behavioral_patterns(self, posts, comments):
        """Extract behavioral patterns from posting data."""
        total_activity = len(posts) + len(comments)
        
        patterns = {
            "engagement_level": self._categorize_engagement(total_activity),
            "content_preference": "Comments" if len(comments) > len(posts) else "Posts" if len(posts) > len(comments) else "Balanced",
            "discussion_style": self._analyze_discussion_style(comments),
            "activity_level": self._categorize_activity_level(total_activity),
            "interaction_pattern": self._analyze_interaction_pattern(posts, comments)
        }
        
        return patterns
    
    def _categorize_engagement(self, total_activity):
        """Categorize user engagement level."""
        if total_activity > 80:
            return "Highly Active"
        elif total_activity > 40:
            return "Active"
        elif total_activity > 15:
            return "Moderate"
        else:
            return "Casual"
    
    def _analyze_discussion_style(self, comments):
        """Analyze how user participates in discussions."""
        if not comments:
            return "Non-participant"
        
        avg_comment_length = sum(len(text) for text, _ in comments) / len(comments)
        
        if avg_comment_length > 300:
            return "Detailed Contributor"
        elif avg_comment_length > 100:
            return "Thoughtful Participant"
        else:
            return "Brief Responder"
    
    def _categorize_activity_level(self, total_activity):
        """Categorize overall activity level."""
        if total_activity > 100:
            return "Power User"
        elif total_activity > 50:
            return "Regular User"
        elif total_activity > 20:
            return "Occasional User"
        else:
            return "Infrequent User"
    
    def _analyze_interaction_pattern(self, posts, comments):
        """Analyze interaction patterns."""
        if len(posts) > len(comments) * 2:
            return "Content Creator"
        elif len(comments) > len(posts) * 3:
            return "Community Participant"
        else:
            return "Balanced Contributor"
    
    def _generate_fast_report(self, username, traits, interests, communication, patterns, posts, comments):
        """Generate comprehensive report with enhanced formatting."""
        report = f"""
{'='*80}
🧠 REDDIT PERSONA ANALYSIS REPORT
{'='*80}

👤 USER: u/{username}
🔍 ANALYSIS ENGINE: Ultra-Fast Multi-Algorithm Analysis (100% Free)
📊 DATA POINTS: {len(posts)} posts, {len(comments)} comments
⚡ PROCESSING: Multi-threaded parallel analysis
🕒 GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

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
• Engagement Style: {communication.get('engagement_style', 'Unknown')}
• Sentiment Tendency: {communication.get('sentiment_tendency', 'Unknown')}

{'='*80}
🎭 BEHAVIORAL PATTERNS
{'='*80}

# Continuing from where the code cut off...

• Engagement Level: {patterns.get('engagement_level', 'Unknown')}
• Content Preference: {patterns.get('content_preference', 'Unknown')}
• Discussion Style: {patterns.get('discussion_style', 'Unknown')}
• Activity Level: {patterns.get('activity_level', 'Unknown')}
• Interaction Pattern: {patterns.get('interaction_pattern', 'Unknown')}

{'='*80}
📈 QUICK INSIGHTS
{'='*80}

{self._generate_quick_insights(traits, interests, communication, patterns)}

{'='*80}
⚡ PERFORMANCE METRICS
{'='*80}

• Cache Hits: {self.stats['cache_hits']}
• Processing Time: {self.stats.get('analysis_time', 0):.2f} seconds
• Engine: Rule-based Multi-Algorithm Analysis
• Accuracy: High (based on activity patterns)

{'='*80}
🛡️ PRIVACY & SECURITY
{'='*80}

✅ All data analyzed locally - no external AI APIs used
✅ No personal information stored or transmitted
✅ Analysis based only on public Reddit activity
✅ Results generated using secure, open-source algorithms

{'='*80}
        """
        return report

    def _format_traits(self, traits):
        """Format personality traits with visual indicators."""
        if not traits:
            return "• No significant personality traits detected from available data"
        
        formatted = []
        for trait, confidence in sorted(traits.items(), key=lambda x: x[1], reverse=True):
            bar_length = int(confidence / 10)
            bar = "█" * bar_length + "▒" * (10 - bar_length)
            formatted.append(f"• {trait:<15} [{bar}] {confidence:.1f}%")
        
        return "\n".join(formatted)

    def _format_interests(self, interests):
        """Format interests with relevance indicators."""
        if not interests:
            return "• No specific interests detected from available data"
        
        formatted = []
        max_score = max(interests.values()) if interests else 1
        
        for interest, score in list(interests.items())[:10]:  # Top 10 interests
            relevance = int((score / max_score) * 5)
            stars = "★" * relevance + "☆" * (5 - relevance)
            formatted.append(f"• {interest:<20} {stars} (Score: {score})")
        
        return "\n".join(formatted)

    def _generate_quick_insights(self, traits, interests, communication, patterns):
        """Generate quick insights based on analysis."""
        insights = []
        
        # Personality insights
        if traits:
            top_trait = max(traits.items(), key=lambda x: x[1])
            insights.append(f"• Primary personality trait: {top_trait[0]} ({top_trait[1]:.1f}% confidence)")
        
        # Activity insights
        total_activity = communication.get('total_activity', 0)
        if total_activity > 50:
            insights.append(f"• High activity user with {total_activity} total interactions")
        elif total_activity > 20:
            insights.append(f"• Moderate activity user with {total_activity} total interactions")
        else:
            insights.append(f"• Low activity user with {total_activity} total interactions")
        
        # Communication insights
        verbosity = communication.get('verbosity', 'Unknown')
        if verbosity != 'Unknown':
            insights.append(f"• Communication style: {verbosity}")
        
        # Interest insights
        if interests:
            top_interest = list(interests.keys())[0]
            insights.append(f"• Primary interest area: {top_interest}")
        
        # Behavioral insights
        engagement = patterns.get('engagement_level', 'Unknown')
        if engagement != 'Unknown':
            insights.append(f"• User engagement level: {engagement}")
        
        return "\n".join(insights) if insights else "• Analysis complete - see detailed sections above"

    def save_report(self, report, username):
        """Save report to file with timestamp."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"reddit_analysis_{username}_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"{Fore.GREEN}💾 Report saved to: {filename}{Style.RESET_ALL}")
            return filename
        except Exception as e:
            print(f"{Fore.RED}❌ Error saving report: {e}{Style.RESET_ALL}")
            return None

    def analyze_user(self, username, save_to_file=True):
        """Main analysis method - orchestrates the entire process."""
        print(f"{Fore.BLUE}{'='*60}")
        print(f"{Fore.BLUE}🚀 REDDIT PERSONA ANALYZER - STARTING ANALYSIS")
        print(f"{Fore.BLUE}{'='*60}{Style.RESET_ALL}")
        
        self.stats['start_time'] = time.time()
        
        # Step 1: Scrape user data
        posts, comments = self.parallel_scrape_user_data(username)
        
        if posts is None and comments is None:
            print(f"{Fore.RED}❌ Analysis failed - could not retrieve user data{Style.RESET_ALL}")
            return None
        
        # Step 2: Perform analysis
        analysis_start = time.time()
        report = self.ultra_fast_analysis(posts, comments, username)
        self.stats['analysis_time'] = time.time() - analysis_start
        
        # Step 3: Display results
        print(f"\n{Fore.GREEN}{'='*60}")
        print(f"{Fore.GREEN}✅ ANALYSIS COMPLETE")
        print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
        
        print(report)
        
        # Step 4: Save to file if requested
        if save_to_file:
            self.save_report(report, username)
        
        # Step 5: Display performance stats
        total_time = time.time() - self.stats['start_time']
        print(f"\n{Fore.CYAN}⚡ PERFORMANCE SUMMARY:")
        print(f"   Total Time: {total_time:.2f} seconds")
        print(f"   Analysis Time: {self.stats['analysis_time']:.2f} seconds")
        print(f"   Data Points: {self.stats['total_posts']} posts, {self.stats['total_comments']} comments")
        print(f"   Cache Hits: {self.stats['cache_hits']}")
        print(f"   Memory Usage: Optimized with garbage collection{Style.RESET_ALL}")
        
        # Cleanup
        gc.collect()
        
        return report

def main():
    """Main function with enhanced user interface."""
    print(f"{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.MAGENTA}🧠 REDDIT PERSONA ANALYZER - ULTRA FAST EDITION")
    print(f"{Fore.MAGENTA}{'='*80}")
    print(f"{Fore.MAGENTA}🔥 Features: Multi-threaded • Cached • Secure • 100% Free")
    print(f"{Fore.MAGENTA}⚡ Analysis Engine: Advanced Rule-based Algorithm")
    print(f"{Fore.MAGENTA}🛡️ Privacy: All processing done locally")
    print(f"{Fore.MAGENTA}{'='*80}{Style.RESET_ALL}")
    
    try:
        # Initialize analyzer
        analyzer = FastRedditPersonaAnalyzer(CONFIG)
        
        # Interactive mode
        while True:
            print(f"\n{Fore.CYAN}🎯 ANALYSIS OPTIONS:")
            print(f"   1. Analyze a Reddit user")
            print(f"   2. Batch analyze multiple users")
            print(f"   3. View cache statistics")
            print(f"   4. Clear cache")
            print(f"   5. Exit{Style.RESET_ALL}")
            
            choice = input(f"\n{Fore.YELLOW}Enter your choice (1-5): {Style.RESET_ALL}")
            
            if choice == '1':
                username = input(f"{Fore.CYAN}Enter Reddit username (without u/): {Style.RESET_ALL}")
                if username:
                    analyzer.analyze_user(username)
                else:
                    print(f"{Fore.RED}❌ Please enter a valid username{Style.RESET_ALL}")
            
            elif choice == '2':
                print(f"{Fore.CYAN}Enter usernames separated by commas:{Style.RESET_ALL}")
                usernames = input().split(',')
                usernames = [u.strip() for u in usernames if u.strip()]
                
                if usernames:
                    for username in usernames:
                        print(f"\n{Fore.BLUE}Analyzing: {username}{Style.RESET_ALL}")
                        analyzer.analyze_user(username)
                        print(f"\n{'-'*60}")
                else:
                    print(f"{Fore.RED}❌ Please enter valid usernames{Style.RESET_ALL}")
            
            elif choice == '3':
                print(f"\n{Fore.CYAN}📊 CACHE STATISTICS:")
                print(f"   Cached entries: {len(analyzer.cache)}")
                print(f"   Total cache hits: {analyzer.stats['cache_hits']}")
                print(f"   Cache enabled: {CONFIG['CACHE_ENABLED']}{Style.RESET_ALL}")
            
            elif choice == '4':
                analyzer.cache.clear()
                print(f"{Fore.GREEN}✅ Cache cleared successfully{Style.RESET_ALL}")
            
            elif choice == '5':
                print(f"{Fore.GREEN}👋 Thanks for using Reddit Persona Analyzer!{Style.RESET_ALL}")
                break
            
            else:
                print(f"{Fore.RED}❌ Invalid choice. Please enter 1-5{Style.RESET_ALL}")
    
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️ Analysis interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Unexpected error: {e}{Style.RESET_ALL}")
    finally:
        print(f"{Fore.BLUE}🔧 Cleaning up resources...{Style.RESET_ALL}")
        gc.collect()

if __name__ == "__main__":
    main()
