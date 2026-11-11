import re
import hashlib
from typing import List, Dict, Any, Set, Tuple, Optional
from config import SIMILARITY_THRESHOLD

STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "for", "to", "of", "and", "or", "by",
    "with", "is", "are", "was", "were", "be", "been", "as", "from", "after",
    "says", "said", "over", "into", "amid", "new", "us", "uk", "eu", "un"
}

def normalize_text(text: str) -> str:
    """Normalize text by lowercasing and stripping non-alphanumeric characters."""
    if not text:
        return ""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return re.sub(r"\s+", " ", cleaned).strip()

def tokenize(text: str) -> Set[str]:
    """Tokenize normalized text into meaningful keywords, discarding common stopwords."""
    norm = normalize_text(text)
    tokens = {word for word in norm.split() if len(word) > 2 and word not in STOPWORDS}
    return tokens

def calculate_jaccard_similarity(tokens1: Set[str], tokens2: Set[str]) -> float:
    """Compute Jaccard similarity coefficient between two sets of tokens."""
    if not tokens1 or not tokens2:
        return 0.0
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    return intersection / union if union > 0 else 0.0

def calculate_overlap_coefficient(tokens1: Set[str], tokens2: Set[str]) -> float:
    """
    Compute Overlap (Szymkiewicz-Simpson) coefficient.
    Crucial for news headlines where one outlet writes a short title and another adds sub-clauses.
    """
    if not tokens1 or not tokens2:
        return 0.0
    intersection = len(tokens1.intersection(tokens2))
    min_size = min(len(tokens1), len(tokens2))
    return intersection / min_size if min_size > 0 else 0.0

def generate_article_fingerprint(url: str, title: str) -> str:
    """Generate a deterministic SHA-256 fingerprint from canonical URL and normalized title."""
    norm_title = normalize_text(title)
    seed = f"{url.strip()}|{norm_title}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()

def are_tokens_similar(
    tokens_a: Set[str],
    tokens_b: Set[str],
    threshold: float = SIMILARITY_THRESHOLD
) -> Tuple[bool, float]:
    """Check if token sets represent the same news event."""
    if not tokens_a or not tokens_b:
        return (False, 0.0)

    jaccard = calculate_jaccard_similarity(tokens_a, tokens_b)
    overlap = calculate_overlap_coefficient(tokens_a, tokens_b)
    
    common_count = len(tokens_a.intersection(tokens_b))
    if common_count >= 3:
        score = max(jaccard, overlap)
    elif common_count == 2 and (len(tokens_a) <= 3 or len(tokens_b) <= 3):
        score = max(jaccard, overlap * 0.85)
    else:
        score = jaccard

    return (score >= threshold, score)

def are_articles_similar(
    title_a: str,
    title_b: str,
    threshold: float = SIMILARITY_THRESHOLD
) -> Tuple[bool, float]:
    """
    Check if two article headlines cover the same event using token overlap.
    Uses composite metric balancing Jaccard similarity and Overlap coefficient.
    Returns (is_similar, similarity_score).
    """
    tokens_a = tokenize(title_a)
    tokens_b = tokenize(title_b)
    return are_tokens_similar(tokens_a, tokens_b, threshold=threshold)

def deduplicate_articles(
    articles: List[Dict[str, Any]],
    existing_urls: Optional[Set[str]] = None,
    existing_titles: Optional[List[str]] = None,
    threshold: float = SIMILARITY_THRESHOLD
) -> List[Dict[str, Any]]:
    """
    Deduplicate a list of incoming articles against:
    1. Existing database URLs and titles.
    2. Intra-batch duplicates across multiple RSS feeds.
    
    Merges duplicate coverage info (e.g. tracking multiple sources reporting the same event).
    """
    seen_urls: Set[str] = set(existing_urls) if existing_urls else set()
    accepted_articles: List[Dict[str, Any]] = []
    
    # Pre-populate token cache for existing titles
    existing_title_tokens: List[Tuple[str, Set[str]]] = []
    if existing_titles:
        for t in existing_titles:
            existing_title_tokens.append((t, tokenize(t)))

    for article in articles:
        url = article.get("link", "").strip()
        title = article.get("title", "").strip()

        if not url or not title:
            continue

        # Check 1: Exact URL match
        if url in seen_urls:
            continue

        tokens = tokenize(title)
        
        # Check 2: Similarity against existing DB titles
        matched_existing = False
        for _, ex_tokens in existing_title_tokens:
            is_sim, _ = are_tokens_similar(tokens, ex_tokens, threshold=threshold)
            if is_sim:
                matched_existing = True
                break
        if matched_existing:
            continue

        # Check 3: Similarity against already accepted articles in current batch
        is_intra_duplicate = False
        for accepted in accepted_articles:
            acc_tokens = accepted["_tokens"]
            is_sim, _ = are_tokens_similar(tokens, acc_tokens, threshold=threshold)
            if is_sim:
                # Same story reported by multiple outlets in current batch
                is_intra_duplicate = True
                # Record related source
                if "related_sources" not in accepted:
                    accepted["related_sources"] = []
                accepted["related_sources"].append({
                    "source": article.get("source"),
                    "link": url,
                    "title": title
                })
                break

        if not is_intra_duplicate:
            # Store temporary token set for fast matching
            article_copy = dict(article)
            article_copy["_tokens"] = tokens
            article_copy["related_sources"] = []
            article_copy["fingerprint"] = generate_article_fingerprint(url, title)
            accepted_articles.append(article_copy)
            seen_urls.add(url)

    # Clean up temporary matching tokens before returning
    for item in accepted_articles:
        item.pop("_tokens", None)

    return accepted_articles
