#!/usr/bin/env python3
"""
Load seed words into the server via the seedwords.set RPC API.
Words are assigned to game days starting at day 1.

Usage:
    python3 load_seedwords.py [--base-url URL] [--start-day N] [--batch-size N] [--dry-run]

Environment:
    BASE_URL  Server base URL (default: http://localhost:8000)
"""

import json
import os
import sys
import urllib.request
import urllib.error
import argparse

WORDS = [
    "gipsy", "piles", "posed", "flows", "scrap", "pleas", "knead", "tired",
    "sped", "scared", "party", "desk", "take", "strike", "only", "fish",
    "broad", "partly", "heat", "his", "dish", "low", "beach", "fast",
    "explain", "loan", "works", "judgment", "major", "float", "bank", "who",
    "save", "justice", "field", "few", "doubt", "bag", "creation", "jury",
    "club", "turn", "earn", "company", "gold", "nature", "often", "rope",
    "water", "payment", "sight", "around", "double", "tribe", "one", "chart",
    "bunch", "winter", "myself", "mainly", "quick", "husband", "faith", "huge",
    "for", "bake", "lead", "phase", "go", "detail", "above", "king", "rock",
    "rid", "flower", "urge", "profit", "shirt", "lock", "race", "host",
    "cloud", "ready", "promise", "cut", "nuclear", "ie", "invest", "fashion",
    "author", "in", "advice", "news", "prime", "method", "editor", "nice",
    "jump", "friend", "sing", "new", "drop", "park", "confirm", "smile",
    "grain", "with", "music", "improve", "ethics", "wrong", "island", "index",
    "aid", "quit", "cabinet", "spend", "next", "growth", "fabric", "row",
    "scope", "father", "wine", "marketing", "powder", "bowl", "shore", "poet",
    "platform", "media", "sin", "truck", "period", "fault", "famous", "victory",
    "to", "permit", "house", "counter", "talk", "funeral", "iron", "basket",
    "hurt", "end", "market", "ban", "job", "favorite", "day", "least",
    "album", "nose", "bus", "each", "twice", "once", "just", "spot",
    "kitchen", "hot", "shelf", "ugly", "grant", "weapon", "dear", "son",
    "holy", "silver", "deny", "front", "cable", "lab", "cold", "pure",
    "lawn", "include", "busy", "glad", "picture", "maybe", "chase", "could",
    "simply", "item", "push", "slight", "camp", "side", "any", "solid",
    "topic", "legacy", "forget", "jacket", "spring", "campus", "quietly", "pride",
    "square", "army", "star", "central", "question", "grade", "lots", "via",
    "unlike", "run", "would", "journey", "second", "courage", "frame", "discovery",
    "awful", "dance", "typical", "left", "handful", "swim", "spread", "plan",
    "bridge", "reduction", "early", "prison", "farm", "storage", "as", "region",
    "favor", "violent", "labor", "urban", "mostly", "her", "snap", "diet",
    "belong", "bike", "fuel", "cop", "hi", "tube", "saving", "brick",
    "ring", "true", "neighbor", "personal", "two", "gap", "film", "journalist",
    "bother", "sake", "modern", "slow", "drug", "hunter", "policy", "faculty",
    "bad", "gate", "deck", "project", "large", "tear", "hate", "priest",
    "city", "gather", "rail", "sky", "bite", "qualify", "sport", "mine",
    "the", "dream", "pound", "software", "youth", "cast", "voice", "sauce",
    "size", "admit", "up", "organic", "stream", "lady", "track", "shine",
    "mode", "working", "social", "golf", "split", "nurse", "aspect", "lover",
    "ski", "thanks", "brown", "hit", "smart", "consumer", "born", "grab",
    "play", "enjoy", "pay", "land", "pile", "no", "belt", "avoid",
    "solar", "anxiety", "complaint", "tour", "lower", "vote", "sir", "war",
    "pair", "grow", "truly", "garlic", "than", "smoke", "various", "young",
    "birth", "whisper", "rich", "founder", "fine", "block", "found", "anger",
    "nearly", "armed", "quite", "notice", "cluster", "impact", "educator", "road",
    "bed", "switch", "video", "holiday", "scale", "native", "cap", "both",
    "trip", "sector", "yield", "meat", "like", "unit", "plane", "journal",
    "volume", "alive", "hold", "hand", "your", "tea", "personality", "poverty",
    "fly", "handle", "use", "lie", "fit", "how", "we", "clothing",
    "agent", "below", "publish", "user", "red", "hat", "fan", "build",
    "body", "pot", "pack", "fix", "trouble", "story", "simple", "code",
    "player", "previous", "visual", "shower", "housing", "white", "shortly", "adopt",
    "shit", "trace", "relation", "ad", "core", "introduce", "quality", "eight",
    "more", "clear", "react", "painter", "single", "begin", "hearing", "along",
    "miracle", "complain", "argument", "joint", "given", "power", "link", "retain",
    "destroy", "fire", "other", "town", "problem", "act", "lawyer", "hero",
    "deal", "buck", "towards", "mouse", "client", "male", "warm", "phrase",
    "buyer", "study", "back", "cash", "penalty", "joy", "careful", "etc",
    "flame", "bean", "phone", "metal", "garden", "convert", "fortune", "scholar",
    "script", "math", "sacred", "oil", "hospital", "join", "stand", "boat",
    "woman", "tie", "waste", "home", "sugar", "tax", "trend", "wish",
    "weight", "basic", "might", "machine", "right", "five", "chest", "very",
    "cream", "tank", "nut", "fresh", "great", "meal", "ask", "network",
    "sharp", "flag", "sick", "bone", "walk", "down", "tale", "at",
    "directly", "round", "somewhat", "rose", "product", "touch", "world", "loud",
    "wing", "focus", "budget", "lose", "cake", "jet", "wet", "per",
    "carbon", "flavor", "silent", "horse", "wisdom", "crash", "neck", "boy",
    "stick", "ignore", "reach", "suit", "map", "black", "muscle", "ah",
    "from", "voter", "naked", "wander", "listen", "many", "clean", "history",
    "fat", "knife", "singer", "cousin", "tap", "imply", "open", "uniform",
    "flow", "soup", "car", "yeah", "hey", "score", "exactly", "ship",
    "third", "hungry", "distance", "guide", "proud", "acid", "divorce", "sex",
    "purchase", "scream", "strongly", "widely", "senator", "relax", "instead", "rain",
    "vary", "security", "role", "may", "steal", "shoe", "raw", "man",
    "them", "so", "sea", "slide", "sort", "what", "produce", "north",
    "place", "long", "gift", "pray", "giant", "comedy", "adviser", "mayor",
    "surface", "lucky", "rapidly", "can", "pocket", "string", "gently", "income",
    "until", "nor", "song", "pine", "normal", "be", "whole", "strip",
    "symbol", "but", "habit", "board", "hope", "organize", "ratio", "education",
    "display", "about", "shade", "work", "paint", "draft", "brain", "friendly",
    "beyond", "dare", "result", "depict", "crop", "panel", "honey", "read",
    "private", "poetry", "team", "hire", "outside", "its", "senior", "flat",
    "love", "four", "way", "menu", "clothes", "hang", "travel", "master",
    "cause", "final", "rank", "make", "rifle", "such", "regional", "soul",
    "drink", "soft", "value", "beauty", "lunch", "capture", "submit", "out",
    "during", "almost", "terms", "lake", "variety", "ice", "juice", "entry",
    "if", "rest", "chair", "into", "later", "term", "file", "grave",
    "or", "delay", "mad", "tape", "gaze", "chapter", "bench", "shift",
    "climate", "discover", "fate", "sand", "rise", "hole", "short", "then",
    "send", "reply", "charity", "chef", "bend", "bread", "guy", "case",
    "modest", "chief", "article", "fear", "advise", "blanket", "first", "ear",
    "mail", "remain", "tough", "hip", "this", "used", "lemon", "inform",
    "virtue", "stock", "own", "brief", "most", "task", "bright", "wear",
    "win", "combine", "plenty", "soldier", "expand", "bear", "orange", "not",
    "month", "sit", "virus", "privacy", "trial", "wave", "girl", "mistake",
    "drag", "century", "part", "maker", "course", "watch", "shop", "store",
    "universal", "birthday", "page", "key", "glance", "plot", "noise", "dry",
    "warn", "snow", "gun", "guilty", "pour", "blame", "why", "worth",
    "buy", "let", "theory", "steady", "section", "pace", "custom", "blind",
    "drawing", "rush", "and", "undergo", "sad", "air", "know", "computer",
    "near", "previously", "hard", "stair", "shadow", "search", "she", "publisher",
    "milk", "porch", "fact", "some", "lack", "soil", "false", "length",
    "count", "minute", "amount", "tip", "okay", "my", "danger", "print",
    "exact", "site", "step", "being", "lean", "vs", "foreign", "aim",
    "peak", "newly", "strange", "court", "stake", "county", "reading", "post",
    "form", "under", "old", "formal", "rely", "gear", "wrap", "yes",
    "wild", "minor", "therapy", "chip", "big", "mother", "guard", "moral",
    "wise", "stage", "dust", "compare", "ethnic", "trail", "real", "top",
    "those", "badly", "ground", "document", "risk", "ten", "cow", "factory",
    "studio", "south", "admire", "while", "painful", "uncle", "parking", "actor",
    "storm", "port", "respond", "hide", "source", "brand", "climb", "tone",
    "clue", "heavy", "mean", "get", "upon", "cabin", "help", "cat",
    "shut", "drive", "consider", "guest", "pan", "stir", "society", "year",
    "ride", "try", "due", "yet", "grand", "profile", "mix", "heart",
    "injury", "toe", "reality", "scenario", "yours", "bring", "lost", "lawsuit",
    "super", "tend", "mouth", "physical", "point", "move", "subject", "romantic",
    "lift", "gray", "give", "path", "draw", "able", "dominate", "show",
    "easy", "cope", "arise", "wonder", "earth", "share", "auto", "want",
    "die", "boundary", "have", "corn", "humor", "note", "plastic", "shock",
    "breath", "image", "yourself", "owner", "think", "mental", "leg", "safe",
    "they", "object", "gifted", "finger", "bird", "today", "musical", "something",
    "failure", "hotel", "last", "blue", "daily", "eat", "find", "roughly",
    "dark", "glove", "crew", "alter", "survey", "pie", "me", "shot",
    "adult", "east", "sure", "style", "human", "background", "cover", "us",
    "easily", "another", "leading", "wake", "charge", "champion", "shoulder", "special",
    "exist", "cite", "jail", "couple", "gay", "wind", "pause", "slip",
    "come", "employ", "raise", "by", "wire", "investor", "west", "cry",
    "acquire", "agency", "blow", "argue", "equal", "lip", "sun", "lap",
    "pale", "yard", "he", "age", "should", "fruit", "nearby", "six",
    "night", "dozen", "train", "game", "on", "bet", "duty", "police",
    "behavior", "say", "stone", "empty", "do", "wealth", "pick", "thank",
    "route", "sale", "flight", "shake", "thin", "tired", "angle", "base",
    "shrug", "money", "fairly", "hear", "whom", "oh", "it", "close",
    "nervous", "tail", "planet", "pole", "solve", "group", "late", "dialogue",
    "boyfriend", "child", "locate", "view", "version", "flesh", "shape", "deputy",
    "forest", "novel", "customer", "cost", "hardly", "wound", "answer", "rapid",
    "prove", "fund", "care", "you", "seat", "list", "teach", "importance",
    "era", "art", "firm", "itself", "powerful", "fourth", "fiber", "bind",
    "province", "abuse", "mask", "speak", "category", "put", "stop", "brush",
    "hair", "safety", "also", "wide", "plate", "stomach", "family", "broken",
    "palm", "tragedy", "half", "word", "depth", "factor", "routine", "strong",
    "of", "fade", "myth", "hour", "slave", "lay", "swear", "movie",
    "sample", "crazy", "action", "wait", "dirt", "chain", "margin", "fun",
    "mount", "set", "past", "pitch", "ghost", "rough", "absolute", "forth",
    "predict", "certain", "idea", "adjust", "net", "craft", "signal", "column",
    "unable", "their", "box", "pink", "direct", "golden", "break", "domestic",
    "quickly", "toward", "justify", "skin", "number", "coal", "wage", "space",
    "arm", "stupid", "when", "mind", "self", "tongue", "cheap", "thing",
    "public", "range", "figure", "extra", "dig", "beat", "owe", "name",
    "design", "luck", "live", "industry", "provide", "gain", "regulation", "coast",
    "bit", "debt", "after", "claim", "enough", "mixture", "sound", "twin",
    "date", "credit", "dispute", "protein", "match", "whose", "alone", "ocean",
    "dog", "law", "wife", "thousand", "operating", "now", "ought", "quiet",
    "teaching", "folk", "rub", "vital", "write", "fair", "plant", "fighter",
    "nod", "slice", "head", "coat", "tire", "southern", "barely", "band",
    "death", "burn", "price", "trick", "table", "learn", "obtain", "impose",
    "leaf", "aide", "since", "angry", "junior", "lung", "same", "crime",
    "makeup", "sexual", "thick", "vast", "layer", "light", "anymore", "over",
    "toy", "remind", "spin", "time", "far", "rating", "poem", "dangerous",
    "stable", "pose", "tower", "pain", "wash", "complex", "dirty", "country",
    "swing", "joke", "force", "him", "sign", "pet", "shout", "our",
    "consume", "goal", "behind", "blade", "formula", "chamber", "kind", "rate",
    "crowd", "lot", "wealthy", "salt", "sue", "thus", "much", "mark",
    "plus", "violate", "trade", "among", "pilot", "piano", "branch", "stroke",
    "bury", "bar", "others", "oven", "burden", "launch", "medical", "gas",
    "stay", "rice", "must", "wonderful", "fail", "fight", "copy", "heavily",
    "ok", "reaction", "weigh", "load", "majority", "certainly", "bond", "briefly",
    "patch", "active", "honest", "surely", "change", "parent", "radio", "kid",
    "weak", "cup", "life", "pant", "ago", "breast", "zone", "reason",
    "person", "closer", "line", "stare", "laugh", "rule", "judge", "aside",
    "main", "wipe", "tiny", "sigh", "daughter", "ideal", "face", "himself",
    "card", "type", "sink", "best", "quote", "throw", "model",
]


def rpc_call(base_url: str, method: str, params: dict) -> dict:
    payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode()
    req = urllib.request.Request(
        f"{base_url}/rpc",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def main():
    parser = argparse.ArgumentParser(description="Load seed words into the server")
    parser.add_argument("--base-url", default=os.getenv("BASE_URL", "http://localhost:8000"))
    parser.add_argument("--start-day", type=int, default=1, help="Game day for the first word (default: 1)")
    parser.add_argument("--batch-size", type=int, default=50, help="Words per request (default: 50)")
    parser.add_argument("--dry-run", action="store_true", help="Print entries without sending")
    args = parser.parse_args()

    entries = [{"day": args.start_day + i, "word": w} for i, w in enumerate(WORDS)]
    total = len(entries)
    batches = [entries[i:i + args.batch_size] for i in range(0, total, args.batch_size)]

    print(f"Base URL : {args.base_url}")
    print(f"Words    : {total} (days {entries[0]['day']}–{entries[-1]['day']})")
    print(f"Batches  : {len(batches)} × up to {args.batch_size}")
    if args.dry_run:
        print("\n-- dry run, first batch --")
        print(json.dumps(batches[0], indent=2))
        return

    print()
    for i, batch in enumerate(batches, 1):
        day_range = f"{batch[0]['day']}–{batch[-1]['day']}"
        try:
            result = rpc_call(args.base_url, "seedwords.set", {"entries": batch})
            if "error" in result:
                print(f"  batch {i}/{len(batches)} (days {day_range})  ERROR: {result['error']['message']}")
                sys.exit(1)
            print(f"  batch {i}/{len(batches)} (days {day_range})  OK  ({len(batch)} words)")
        except Exception as e:
            print(f"  batch {i}/{len(batches)} (days {day_range})  FAILED: {e}")
            sys.exit(1)

    print(f"\nDone. {total} seed words loaded.")


if __name__ == "__main__":
    main()
