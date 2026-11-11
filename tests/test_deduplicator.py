from src.deduplicator import (
    normalize_text,
    tokenize,
    calculate_jaccard_similarity,
    are_articles_similar,
    deduplicate_articles
)

def test_normalize_and_tokenize():
    title = "The U.S. and E.U. Announce New Sanctions Over Naval Blockade!"
    norm = normalize_text(title)
    assert "sanctions" in norm
    tokens = tokenize(title)
    # Stopwords like the, and, over should be removed
    assert "the" not in tokens
    assert "and" not in tokens
    assert "sanctions" in tokens
    assert "blockade" in tokens

def test_jaccard_similarity():
    tokens1 = {"naval", "blockade", "strait", "tensions"}
    tokens2 = {"naval", "blockade", "strait", "crisis"}
    sim = calculate_jaccard_similarity(tokens1, tokens2)
    # 3 in common / 5 total unique = 0.6
    assert round(sim, 2) == 0.60
    assert calculate_jaccard_similarity(tokens1, tokens1) == 1.0
    assert calculate_jaccard_similarity(set(), tokens1) == 0.0

def test_are_articles_similar():
    t1 = "UN passes resolution calling for immediate ceasefire"
    t2 = "UN adopts resolution demanding immediate ceasefire"
    similar, score = are_articles_similar(t1, t2, threshold=0.6)
    assert similar is True
    assert score >= 0.6

    t3 = "Oil prices fluctuate following OPEC production quota report"
    different, diff_score = are_articles_similar(t1, t3, threshold=0.5)
    assert different is False

def test_deduplicate_articles():
    incoming = [
        {
            "title": "Envoys Meet for Red Sea Maritime Talks",
            "link": "https://example.com/red-sea-talks",
            "source": "Source A"
        },
        {
            "title": "Envoys Meet for Red Sea Maritime Talks", # Exact URL duplicate
            "link": "https://example.com/red-sea-talks",
            "source": "Source A"
        },
        {
            "title": "Diplomats Gather for Red Sea Maritime Talks", # Semantic title duplicate
            "link": "https://reuters.com/world/red-sea-maritime-talks",
            "source": "Source B"
        },
        {
            "title": "New Aerospace Defense Pact Signed in Pacific", # Distinct article
            "link": "https://dw.com/pacific-defense-pact",
            "source": "Source C"
        }
    ]

    deduped = deduplicate_articles(incoming, threshold=0.6)
    assert len(deduped) == 2
    
    # Check that Source B was attached as a related source to the first event
    first_event = deduped[0]
    assert first_event["link"] == "https://example.com/red-sea-talks"
    assert len(first_event.get("related_sources", [])) == 1
    assert first_event["related_sources"][0]["source"] == "Source B"

    # Second event is distinct
    second_event = deduped[1]
    assert "Aerospace Defense Pact" in second_event["title"]
