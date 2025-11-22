import spacy
from typing import List, Dict, Tuple
from collections import Counter, defaultdict
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import re
import sys
import os

class NLPAnalyzer:
    """NLP-based email analysis and clustering"""
    
    def __init__(self):
        # Try to find venv site-packages if not in sys.path
        venv_site_packages = self._find_venv_site_packages()
        if venv_site_packages and venv_site_packages not in sys.path:
            sys.path.insert(0, venv_site_packages)
        
        # Try importing model directly first (more reliable)
        try:
            import en_core_web_sm
            self.nlp = en_core_web_sm.load()
        except ImportError:
            # Fallback to spacy.load()
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                raise Exception(
                    "spaCy English model not found. Install with: "
                    "pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl"
                )
        self.vectorizer = TfidfVectorizer(max_features=100, stop_words='english', ngram_range=(1, 2))
    
    def _find_venv_site_packages(self):
        """Find venv site-packages directory relative to this file"""
        current_file = os.path.abspath(__file__)
        # Navigate from app/nlp_analyzer.py to backend/venv/lib/python*/site-packages
        # __file__ is backend/app/nlp_analyzer.py, so:
        # dirname once: backend/app
        # dirname twice: backend
        backend_dir = os.path.dirname(os.path.dirname(current_file))
        venv_dir = os.path.join(backend_dir, 'venv', 'lib')
        if os.path.exists(venv_dir):
            # Find python version directory
            for item in os.listdir(venv_dir):
                if item.startswith('python'):
                    site_packages = os.path.join(venv_dir, item, 'site-packages')
                    if os.path.exists(site_packages):
                        return os.path.abspath(site_packages)
        return None
    
    def analyze_batch(self, emails: List[Dict]) -> Dict:
        """
        Analyze a batch of emails and return insights
        """
        if not emails:
            return {
                'sender_patterns': {},
                'subject_clusters': [],
                'frequency_analysis': {},
                'categories': {}
            }
        
        # Extract data
        subjects = [e.get('subject', '') for e in emails]
        senders = [e.get('sender_email', '') for e in emails]
        dates = [e.get('date_received') for e in emails]
        
        # Analyze senders
        sender_patterns = self._analyze_sender_patterns(emails)
        
        # Cluster subjects
        subject_clusters = self._cluster_subjects(subjects)
        
        # Frequency analysis
        frequency_analysis = self._analyze_frequency(emails, dates)
        
        # Categorize emails
        categories = self._categorize_emails(emails)
        
        return {
            'sender_patterns': sender_patterns,
            'subject_clusters': subject_clusters,
            'frequency_analysis': frequency_analysis,
            'categories': categories,
            'total_emails': len(emails),
            'unique_senders': len(set(senders)),
            'date_range': {
                'start': min(dates).isoformat() if dates else None,
                'end': max(dates).isoformat() if dates else None
            }
        }
    
    def _analyze_sender_patterns(self, emails: List[Dict]) -> Dict:
        """Analyze sender patterns and frequency"""
        sender_counts = Counter(e.get('sender_email', '') for e in emails)
        sender_names = {e.get('sender_email', ''): e.get('sender_name') for e in emails}
        
        # Group by domain
        domain_counts = Counter()
        for sender in sender_counts.keys():
            if '@' in sender:
                domain = sender.split('@')[1]
                domain_counts[domain] += sender_counts[sender]
        
        # Top senders
        top_senders = [
            {
                'email': email,
                'name': sender_names.get(email),
                'count': count,
                'percentage': round(count / len(emails) * 100, 2)
            }
            for email, count in sender_counts.most_common(20)
        ]
        
        return {
            'top_senders': top_senders,
            'top_domains': [
                {'domain': domain, 'count': count}
                for domain, count in domain_counts.most_common(10)
            ],
            'total_unique_senders': len(sender_counts)
        }
    
    def _cluster_subjects(self, subjects: List[str]) -> List[Dict]:
        """Cluster similar subjects using NLP"""
        if not subjects:
            return []
        
        # Clean and preprocess
        cleaned_subjects = [self._clean_subject(s) for s in subjects if s]
        
        if len(cleaned_subjects) < 2:
            return [{'cluster_id': 0, 'subjects': subjects, 'count': len(subjects)}]
        
        try:
            # Vectorize
            vectors = self.vectorizer.fit_transform(cleaned_subjects)
            
            # Cluster
            clustering = DBSCAN(eps=0.3, min_samples=2, metric='cosine')
            cluster_labels = clustering.fit_predict(vectors.toarray())
            
            # Group by cluster
            clusters = defaultdict(list)
            for idx, label in enumerate(cluster_labels):
                if label != -1:  # -1 is noise in DBSCAN
                    clusters[label].append(subjects[idx])
            
            # Format results
            result = []
            for cluster_id, cluster_subjects in clusters.items():
                result.append({
                    'cluster_id': int(cluster_id),
                    'subjects': cluster_subjects[:10],  # Limit examples
                    'count': len(cluster_subjects),
                    'representative': self._get_representative_subject(cluster_subjects)
                })
            
            # Add unclustered
            noise_count = sum(1 for label in cluster_labels if label == -1)
            if noise_count > 0:
                result.append({
                    'cluster_id': -1,
                    'subjects': [],
                    'count': noise_count,
                    'representative': 'Unclustered emails'
                })
            
            return sorted(result, key=lambda x: x['count'], reverse=True)
            
        except Exception as e:
            print(f"Clustering error: {e}")
            return [{'cluster_id': 0, 'subjects': subjects[:10], 'count': len(subjects)}]
    
    def _clean_subject(self, subject: str) -> str:
        """Clean and normalize subject line"""
        # Remove common prefixes
        subject = re.sub(r'^(Re:|Fwd?:|FW:)', '', subject, flags=re.IGNORECASE)
        subject = re.sub(r'\[.*?\]', '', subject)  # Remove brackets
        subject = re.sub(r'\(.*?\)', '', subject)  # Remove parentheses
        subject = subject.strip().lower()
        return subject
    
    def _get_representative_subject(self, subjects: List[str]) -> str:
        """Get most representative subject from cluster"""
        if not subjects:
            return ""
        # Return shortest non-empty subject (often most generic)
        non_empty = [s for s in subjects if s.strip()]
        if non_empty:
            return min(non_empty, key=len)
        return subjects[0]
    
    def _analyze_frequency(self, emails: List[Dict], dates: List[datetime]) -> Dict:
        """Analyze email frequency patterns"""
        if not dates:
            return {}
        
        # Daily frequency
        daily_counts = Counter(d.date() for d in dates if d)
        
        # Hourly frequency
        hourly_counts = Counter(d.hour for d in dates if d)
        
        # Day of week frequency
        weekday_counts = Counter(d.weekday() for d in dates if d)
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        return {
            'daily_average': round(len(emails) / max(len(daily_counts), 1), 2),
            'peak_hour': max(hourly_counts.items(), key=lambda x: x[1])[0] if hourly_counts else None,
            'peak_day': weekday_names[max(weekday_counts.items(), key=lambda x: x[1])[0]] if weekday_counts else None,
            'hourly_distribution': dict(hourly_counts),
            'weekday_distribution': {weekday_names[k]: v for k, v in weekday_counts.items()}
        }
    
    def _categorize_emails(self, emails: List[Dict]) -> Dict:
        """Categorize emails based on subject and sender patterns"""
        categories = {
            'notifications': 0,
            'newsletters': 0,
            'social': 0,
            'shopping': 0,
            'work': 0,
            'personal': 0,
            'other': 0
        }
        
        notification_keywords = ['notification', 'alert', 'reminder', 'confirm', 'receipt']
        newsletter_keywords = ['newsletter', 'digest', 'weekly', 'monthly', 'unsubscribe']
        social_keywords = ['facebook', 'twitter', 'linkedin', 'instagram', 'social']
        shopping_keywords = ['order', 'purchase', 'shipping', 'delivery', 'amazon', 'ebay']
        work_keywords = ['meeting', 'calendar', 'team', 'project', 'deadline']
        
        for email in emails:
            subject = (email.get('subject', '') or '').lower()
            sender = (email.get('sender_email', '') or '').lower()
            
            categorized = False
            
            if any(kw in subject for kw in notification_keywords):
                categories['notifications'] += 1
                categorized = True
            elif any(kw in subject or kw in sender for kw in newsletter_keywords):
                categories['newsletters'] += 1
                categorized = True
            elif any(kw in sender for kw in social_keywords):
                categories['social'] += 1
                categorized = True
            elif any(kw in subject or kw in sender for kw in shopping_keywords):
                categories['shopping'] += 1
                categorized = True
            elif any(kw in subject for kw in work_keywords):
                categories['work'] += 1
                categorized = True
            elif '@' in sender and not any(kw in sender for kw in ['noreply', 'no-reply', 'donotreply']):
                categories['personal'] += 1
                categorized = True
            
            if not categorized:
                categories['other'] += 1
        
        return categories

