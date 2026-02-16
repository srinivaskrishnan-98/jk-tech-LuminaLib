#!/usr/bin/env python3
"""Script to download and add real public domain books from Project Gutenberg."""
import requests
import time
from pathlib import Path

API_BASE = "http://localhost:8000"

# Login to get token
login_response = requests.post(
    f"{API_BASE}/auth/login",
    data={
        "username": "srinivaskrishnan@gmail.com",
        "password": "SecurePass123"
    }
)
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Public domain books from Project Gutenberg (TXT format for faster processing)
books = [
    # Science Fiction (2 books)
    {
        "title": "Frankenstein",
        "author": "Mary Shelley",
        "genre": "Science Fiction",
        "isbn": "9780141439471",
        "description": "Mary Shelley's seminal novel of the scientist whose creation becomes a monster. A novel of science fiction that examines the moral implications of scientific advancement.",
        "url": "https://www.gutenberg.org/cache/epub/84/pg84.txt"
    },
    {
        "title": "Twenty Thousand Leagues Under the Sea",
        "author": "Jules Verne",
        "genre": "Science Fiction",
        "isbn": "9780553213119",
        "description": "The adventure of a French professor and his companions aboard the submarine Nautilus with the mysterious Captain Nemo.",
        "url": "https://www.gutenberg.org/cache/epub/164/pg164.txt"
    },

    # Fantasy (3 books)
    {
        "title": "Alice's Adventures in Wonderland",
        "author": "Lewis Carroll",
        "genre": "Fantasy",
        "isbn": "9780141439761",
        "description": "Alice falls down a rabbit hole and finds herself in a bizarre world inhabited by peculiar creatures. A masterpiece of fantasy literature.",
        "url": "https://www.gutenberg.org/cache/epub/11/pg11.txt"
    },
    {
        "title": "The Wonderful Wizard of Oz",
        "author": "L. Frank Baum",
        "genre": "Fantasy",
        "isbn": "9780486248189",
        "description": "Dorothy is swept away from Kansas to the magical Land of Oz, where she embarks on a quest to find the Wizard who can help her return home.",
        "url": "https://www.gutenberg.org/cache/epub/55/pg55.txt"
    },
    {
        "title": "Peter Pan",
        "author": "J.M. Barrie",
        "genre": "Fantasy",
        "isbn": "9780141321127",
        "description": "The classic tale of the boy who wouldn't grow up, his fairy companion Tinker Bell, and the Darling children's adventures in Neverland.",
        "url": "https://www.gutenberg.org/cache/epub/16/pg16.txt"
    },

    # Mystery (2 books)
    {
        "title": "The Adventures of Sherlock Holmes",
        "author": "Arthur Conan Doyle",
        "genre": "Mystery",
        "isbn": "9780141034355",
        "description": "A collection of twelve short stories featuring the famous detective Sherlock Holmes and his companion Dr. Watson.",
        "url": "https://www.gutenberg.org/cache/epub/1661/pg1661.txt"
    },
    {
        "title": "The Hound of the Baskervilles",
        "author": "Arthur Conan Doyle",
        "genre": "Mystery",
        "isbn": "9780141439785",
        "description": "Holmes and Watson investigate the legend of a supernatural hound haunting the Baskerville family on the moors of Devonshire.",
        "url": "https://www.gutenberg.org/cache/epub/2852/pg2852.txt"
    },

    # Historical Fiction (3 books)
    {
        "title": "A Tale of Two Cities",
        "author": "Charles Dickens",
        "genre": "Historical Fiction",
        "isbn": "9780141439600",
        "description": "Set against the backdrop of the French Revolution, this novel follows the lives of Charles Darnay and Sydney Carton in London and Paris.",
        "url": "https://www.gutenberg.org/cache/epub/98/pg98.txt"
    },
    {
        "title": "The Three Musketeers",
        "author": "Alexandre Dumas",
        "genre": "Historical Fiction",
        "isbn": "9780140449242",
        "description": "Young d'Artagnan travels to Paris to join the Musketeers of the Guard and becomes embroiled in court intrigue and romance.",
        "url": "https://www.gutenberg.org/cache/epub/1257/pg1257.txt"
    },
    {
        "title": "The Count of Monte Cristo",
        "author": "Alexandre Dumas",
        "genre": "Historical Fiction",
        "isbn": "9780140449266",
        "description": "Edmond Dantès is wrongfully imprisoned, escapes, finds treasure, and exacts elaborate revenge on those who betrayed him.",
        "url": "https://www.gutenberg.org/cache/epub/1184/pg1184.txt"
    }
]

print("Downloading and adding 10 real public domain books...")
print(f"Using token: {token[:10]}...\n")

downloads_dir = Path("/tmp/lumina_books")
downloads_dir.mkdir(exist_ok=True)

for i, book in enumerate(books, 1):
    try:
        # Download the book
        print(f"[{i}/10] Downloading: {book['title']}...", end=" ", flush=True)
        book_response = requests.get(book["url"], timeout=30)
        if book_response.status_code != 200:
            print(f"✗ Failed to download (HTTP {book_response.status_code})")
            continue

        # Save to temporary file
        book_file = downloads_dir / \
            f"{i}_{book['title'].replace(' ', '_')}.txt"
        book_file.write_bytes(book_response.content)
        print(f"✓ ({len(book_response.content)} bytes)", flush=True)

        # Upload to LuminaLib
        print(f"    Uploading to LuminaLib...", end=" ", flush=True)
        with open(book_file, "rb") as f:
            response = requests.post(
                f"{API_BASE}/books",
                headers=headers,
                data={
                    "title": book["title"],
                    "author": book["author"],
                    "genre": book["genre"],
                    "isbn": book["isbn"],
                    "description": book["description"]
                },
                files={"file": (book_file.name, f, "text/plain")},
                timeout=30
            )

        if response.status_code == 201:
            print(f"✓ Added ({book['genre']})")
        else:
            print(f"✗ Failed: {response.status_code}: {response.text[:100]}")

    except Exception as e:
        print(f"✗ Error: {str(e)[:100]}")

    # Small delay between uploads
    time.sleep(1)

print(f"\n✓ Book addition complete!")
print(f"\nBooks downloaded to: {downloads_dir}")
print("\nNote: AI summarization is running in the background with 10-minute timeout per book.")
print("This may take 30-60 minutes for all 10 books to complete.")
print("\nMonitor progress with: docker compose logs -f api | grep -E '(ollama_|consensus_|summarization)' ")
