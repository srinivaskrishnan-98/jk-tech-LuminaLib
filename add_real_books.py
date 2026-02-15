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
    # Science Fiction (5 books)
    {
        "title": "Frankenstein",
        "author": "Mary Shelley",
        "genre": "Science Fiction",
        "isbn": "9780141439471",
        "description": "Mary Shelley's seminal novel of the scientist whose creation becomes a monster. A novel of science fiction that examines the moral implications of scientific advancement.",
        "url": "https://www.gutenberg.org/cache/epub/84/pg84.txt"
    },
    {
        "title": "The Time Machine",
        "author": "H.G. Wells",
        "genre": "Science Fiction",
        "isbn": "9780141439976",
        "description": "A Victorian scientist invents a machine that transports him into the future. Wells' pioneering work of science fiction explores the fate of humanity in the distant future.",
        "url": "https://www.gutenberg.org/cache/epub/35/pg35.txt"
    },
    {
        "title": "A Journey to the Centre of the Earth",
        "author": "Jules Verne",
        "genre": "Science Fiction",
        "isbn": "9780486440880",
        "description": "An adventurous geology professor leads an expedition deep within the earth, where they encounter strange phenomena and prehistoric creatures.",
        "url": "https://www.gutenberg.org/cache/epub/18857/pg18857.txt"
    },
    {
        "title": "The War of the Worlds",
        "author": "H.G. Wells",
        "genre": "Science Fiction",
        "isbn": "9780141441030",
        "description": "A terrifying account of Martian invasion of Earth, one of the most influential science fiction novels ever written.",
        "url": "https://www.gutenberg.org/cache/epub/36/pg36.txt"
    },
    {
        "title": "Twenty Thousand Leagues Under the Sea",
        "author": "Jules Verne",
        "genre": "Science Fiction",
        "isbn": "9780553213119",
        "description": "The adventure of a French professor and his companions aboard the submarine Nautilus with the mysterious Captain Nemo.",
        "url": "https://www.gutenberg.org/cache/epub/164/pg164.txt"
    },

    # Fantasy (5 books)
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
    {
        "title": "The Jungle Book",
        "author": "Rudyard Kipling",
        "genre": "Fantasy",
        "isbn": "9780141325293",
        "description": "A collection of stories featuring Mowgli, a boy raised by wolves in the Indian jungle, and his animal friends.",
        "url": "https://www.gutenberg.org/cache/epub/236/pg236.txt"
    },
    {
        "title": "A Princess of Mars",
        "author": "Edgar Rice Burroughs",
        "genre": "Fantasy",
        "isbn": "9780345324375",
        "description": "John Carter mysteriously finds himself transported to Mars, where he becomes embroiled in a conflict between the planet's various civilizations.",
        "url": "https://www.gutenberg.org/cache/epub/62/pg62.txt"
    },

    # Mystery (5 books)
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
    {
        "title": "The Mysterious Affair at Styles",
        "author": "Agatha Christie",
        "genre": "Mystery",
        "isbn": "9780062073570",
        "description": "Hercule Poirot's first case: investigating the poisoning of a wealthy heiress at her country estate during World War I.",
        "url": "https://www.gutenberg.org/cache/epub/863/pg863.txt"
    },
    {
        "title": "The Moonstone",
        "author": "Wilkie Collins",
        "genre": "Mystery",
        "isbn": "9780140434088",
        "description": "A magnificent diamond is stolen, and the ensuing investigation uncovers dark secrets. Often considered the first modern English detective novel.",
        "url": "https://www.gutenberg.org/cache/epub/155/pg155.txt"
    },
    {
        "title": "The Woman in White",
        "author": "Wilkie Collins",
        "genre": "Mystery",
        "isbn": "9780140434149",
        "description": "A gripping tale of mystery and suspense involving mistaken identity, a secret marriage, and a mysterious woman dressed in white.",
        "url": "https://www.gutenberg.org/cache/epub/583/pg583.txt"
    },

    # Historical Fiction (5 books)
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
    },
    {
        "title": "War and Peace",
        "author": "Leo Tolstoy",
        "genre": "Historical Fiction",
        "isbn": "9780307266934",
        "description": "An epic novel chronicling the French invasion of Russia and its impact on Tsarist society through the stories of five aristocratic families.",
        "url": "https://www.gutenberg.org/cache/epub/2600/pg2600.txt"
    },
    {
        "title": "Ivanhoe",
        "author": "Walter Scott",
        "genre": "Historical Fiction",
        "isbn": "9780140436587",
        "description": "A historical romance set in 12th-century England during the reign of King Richard I, featuring knights, tournaments, and the legend of Robin Hood.",
        "url": "https://www.gutenberg.org/cache/epub/82/pg82.txt"
    }
]

print("Downloading and adding 20 real public domain books...")
print(f"Using token: {token[:20]}...\n")

downloads_dir = Path("/tmp/lumina_books")
downloads_dir.mkdir(exist_ok=True)

for i, book in enumerate(books, 1):
    try:
        # Download the book
        print(f"[{i}/20] Downloading: {book['title']}...", end=" ", flush=True)
        book_response = requests.get(book["url"], timeout=30)
        if book_response.status_code != 200:
            print(f"✗ Failed to download (HTTP {book_response.status_code})")
            continue

        # Save to temporary file
        book_file = downloads_dir / f"{i}_{book['title'].replace(' ', '_')}.txt"
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
print("This may take 30-60 minutes for all 20 books to complete.")
print("\nMonitor progress with: docker compose logs -f api | grep -E '(ollama_|consensus_|summarization)' ")
