"""
=============================================================
  DATA VALIDATION SYSTEM - Redundancy & False Positive Detector
  Internship Project | Python Implementation
=============================================================

WHAT THIS SYSTEM DOES (Plain English):
  1. Stores data entries in a simulated "cloud database" (JSON file)
  2. When new data comes in, it checks:
       a. Is this an EXACT duplicate? (same record already exists)
       b. Is this a NEAR duplicate? (same person, slightly different spelling)
       c. Is this data VALID? (no missing fields, correct formats)
  3. Only UNIQUE + VALID data gets saved
  4. Everything else is flagged as REDUNDANT or FALSE POSITIVE
"""

import json          # To read/write our database file
import os            # To check if files exist
import hashlib       # To create unique "fingerprints" of data
import re            # Regular expressions - for validating emails, phones, etc.
from datetime import datetime  # To timestamp each record


# ─────────────────────────────────────────────
#  SECTION 1: THE DATABASE
#  Think of this as our "cloud storage" stored
#  locally as a JSON file.
# ─────────────────────────────────────────────

DATABASE_FILE = "cloud_database.json"  # Our simulated cloud database

def load_database():
    """
    Load existing records from the database file.
    If the file doesn't exist yet, start with an empty database.
    """
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "r") as f:
            return json.load(f)
    # First time running? Create a fresh empty database structure
    return {
        "records": [],          # List of all saved entries
        "hashes": [],           # Fingerprints of each entry (for fast duplicate check)
        "total_added": 0,       # Counter: how many records were successfully added
        "total_rejected": 0,    # Counter: how many were blocked
        "last_updated": None    # Timestamp of last write
    }

def save_database(db):
    """
    Save the current database back to the JSON file.
    This is like "syncing to the cloud".
    """
    db["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DATABASE_FILE, "w") as f:
        json.dump(db, f, indent=2)  # indent=2 makes the file human-readable


# ─────────────────────────────────────────────
#  SECTION 2: HASHING
#  A "hash" is a unique fingerprint for data.
#  If two records have the same hash = they are
#  IDENTICAL (exact duplicate).
# ─────────────────────────────────────────────

def generate_hash(record):
    """
    Create a unique fingerprint (hash) for a record.
    
    HOW IT WORKS:
      - We sort the fields alphabetically so {"b":2,"a":1} and {"a":1,"b":2} 
        produce the same hash (same data, different order = same record)
      - We lowercase everything so "JOHN" and "john" are treated the same
      - We run it through SHA-256 (a standard hashing algorithm)
    
    EXAMPLE:
      {"name": "Alice", "email": "alice@gmail.com"}
      → becomes the string: 'email:alice@gmail.com|name:alice'
      → SHA-256 hash: 'a3f9c2...' (a long unique code)
    """
    # Build a normalized string from the record (sorted, lowercased)
    normalized = "|".join(
        f"{k}:{str(v).lower().strip()}"
        for k, v in sorted(record.items())
        if k != "timestamp"  # Don't include timestamp in hash (it changes every run)
    )
    return hashlib.sha256(normalized.encode()).hexdigest()


# ─────────────────────────────────────────────
#  SECTION 3: VALIDATION
#  Before saving, we check if the data is REAL
#  and COMPLETE. Garbage in = garbage out!
# ─────────────────────────────────────────────

def validate_record(record):
    """
    Check if a record is valid (well-formed, complete, not fake).
    
    Returns a tuple: (is_valid: bool, reason: str)
    
    VALIDATION RULES:
      ✓ Required fields must exist and not be empty
      ✓ Email must follow the pattern: something@something.something
      ✓ Age must be a number between 0 and 120
      ✓ Phone (if provided) must contain only digits/spaces/dashes
    """
    errors = []

    # --- Rule 1: Required fields must be present ---
    required_fields = ["name", "email"]
    for field in required_fields:
        if field not in record:
            errors.append(f"Missing required field: '{field}'")
        elif not str(record[field]).strip():
            errors.append(f"Field '{field}' cannot be empty")

    # --- Rule 2: Email format check ---
    if "email" in record and record["email"]:
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
        if not re.match(email_pattern, record["email"]):
            errors.append(f"Invalid email format: '{record['email']}'")

    # --- Rule 3: Age must be a realistic number (if provided) ---
    if "age" in record and record["age"] != "":
        try:
            age = int(record["age"])
            if age < 0 or age > 120:
                errors.append(f"Age '{age}' is unrealistic (must be 0-120)")
        except ValueError:
            errors.append(f"Age '{record['age']}' is not a valid number")

    # --- Rule 4: Phone number format (if provided) ---
    if "phone" in record and record["phone"]:
        phone_digits = re.sub(r'[\s\-\(\)]', '', str(record["phone"]))
        if not phone_digits.isdigit():
            errors.append(f"Phone '{record['phone']}' contains invalid characters")
        elif len(phone_digits) < 7 or len(phone_digits) > 15:
            errors.append(f"Phone '{record['phone']}' has wrong length")

    if errors:
        return False, "VALIDATION FAILED: " + "; ".join(errors)
    return True, "Valid"


# ─────────────────────────────────────────────
#  SECTION 4: NEAR-DUPLICATE DETECTION
#  Even if records aren't identical, they might
#  be the SAME PERSON with a typo or variation.
#  This catches "false positives" = data that
#  LOOKS new but is actually already in the DB.
# ─────────────────────────────────────────────

def similarity_score(str1, str2):
    """
    Calculate how similar two strings are (0.0 = totally different, 1.0 = identical).
    Uses a simple character-overlap method called the Dice Coefficient.
    
    EXAMPLE:
      "johnsmith" vs "john_smith" → 0.89 (very similar)
      "alice"     vs "bob"        → 0.0  (nothing in common)
    """
    if not str1 or not str2:
        return 0.0
    s1, s2 = str1.lower(), str2.lower()
    if s1 == s2:
        return 1.0
    
    # Create sets of 2-character "bigrams" (pairs of consecutive letters)
    # "john" → {"jo", "oh", "hn"}
    bigrams1 = set(s1[i:i+2] for i in range(len(s1) - 1))
    bigrams2 = set(s2[i:i+2] for i in range(len(s2) - 1))
    
    if not bigrams1 or not bigrams2:
        return 0.0
    
    intersection = bigrams1 & bigrams2  # Letters in common
    return (2.0 * len(intersection)) / (len(bigrams1) + len(bigrams2))


def check_near_duplicate(new_record, db, threshold=0.85):
    """
    Check if a new record is suspiciously similar to an existing one.
    
    THRESHOLD = 0.85 means:
      - 85% or more similar = treat as duplicate
      - Below 85% = probably a different person
    
    We compare by: name + email (the most identifying fields)
    
    Returns: (is_near_duplicate: bool, matching_record or None)
    """
    new_name = new_record.get("name", "").lower().strip()
    new_email = new_record.get("email", "").lower().strip()

    for existing in db["records"]:
        existing_name = existing.get("name", "").lower().strip()
        existing_email = existing.get("email", "").lower().strip()

        name_score = similarity_score(new_name, existing_name)
        email_score = similarity_score(new_email, existing_email)

        # If EITHER name or email is very similar, flag it
        if name_score >= threshold or email_score >= threshold:
            return True, existing, max(name_score, email_score)

    return False, None, 0.0


# ─────────────────────────────────────────────
#  SECTION 5: THE MAIN ENTRY POINT
#  This is where a new record comes in and gets
#  processed through all our checks.
# ─────────────────────────────────────────────

class DataValidationResult:
    """
    A simple container to hold the result of processing a record.
    Like a report card for each submission.
    """
    ADDED = "✅ ADDED"
    EXACT_DUPLICATE = "🔁 EXACT DUPLICATE (Blocked)"
    NEAR_DUPLICATE = "⚠️  NEAR DUPLICATE (Flagged)"
    INVALID = "❌ INVALID DATA (Rejected)"

def add_record(new_data, db, force=False):
    """
    The main function. Takes a new record and decides what to do with it.
    
    PROCESS FLOW:
      Step 1 → Validate the data (is it well-formed?)
      Step 2 → Check for exact duplicate (same hash?)
      Step 3 → Check for near duplicate (very similar?)
      Step 4 → If all clear: save it!
    
    Parameters:
      new_data (dict): The incoming record, e.g. {"name": "Alice", "email": "..."}
      db (dict): The current database loaded into memory
      force (bool): If True, override near-duplicate warning and save anyway
    
    Returns:
      (status, message, record_or_None)
    """

    print("\n" + "="*55)
    print(f"  Processing: {new_data}")
    print("="*55)

    # ── STEP 1: VALIDATE ──────────────────────────────────
    is_valid, validation_msg = validate_record(new_data)
    if not is_valid:
        db["total_rejected"] += 1
        save_database(db)
        print(f"  {DataValidationResult.INVALID}")
        print(f"  Reason: {validation_msg}")
        return DataValidationResult.INVALID, validation_msg, None

    print("  ✓ Validation passed")

    # ── STEP 2: EXACT DUPLICATE CHECK ────────────────────
    record_hash = generate_hash(new_data)
    if record_hash in db["hashes"]:
        db["total_rejected"] += 1
        save_database(db)
        msg = "This exact record already exists in the database."
        print(f"  {DataValidationResult.EXACT_DUPLICATE}")
        print(f"  Reason: {msg}")
        return DataValidationResult.EXACT_DUPLICATE, msg, None

    print("  ✓ No exact duplicate found")

    # ── STEP 3: NEAR DUPLICATE CHECK ─────────────────────
    is_near_dup, matched_record, score = check_near_duplicate(new_data, db)
    if is_near_dup and not force:
        db["total_rejected"] += 1
        save_database(db)
        msg = (
            f"Record is {score*100:.1f}% similar to existing record: "
            f"{matched_record.get('name')} / {matched_record.get('email')}"
        )
        print(f"  {DataValidationResult.NEAR_DUPLICATE}")
        print(f"  Reason: {msg}")
        return DataValidationResult.NEAR_DUPLICATE, msg, matched_record

    print("  ✓ No near-duplicate detected")

    # ── STEP 4: ALL CLEAR — SAVE TO DATABASE ─────────────
    new_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_data["record_id"] = f"REC-{db['total_added'] + 1:04d}"  # e.g. REC-0001

    db["records"].append(new_data)
    db["hashes"].append(record_hash)
    db["total_added"] += 1
    save_database(db)

    print(f"  {DataValidationResult.ADDED}")
    print(f"  Assigned ID: {new_data['record_id']}")
    return DataValidationResult.ADDED, "Record saved successfully.", new_data


# ─────────────────────────────────────────────
#  SECTION 6: REPORTING
# ─────────────────────────────────────────────

def print_database_report(db):
    """
    Print a summary of everything in the database.
    """
    print("\n" + "="*55)
    print("        📊 DATABASE REPORT")
    print("="*55)
    print(f"  Total records saved    : {db['total_added']}")
    print(f"  Total records rejected : {db['total_rejected']}")
    print(f"  Last updated           : {db['last_updated']}")
    print("\n  --- Saved Records ---")
    if not db["records"]:
        print("  (No records in database yet)")
    for rec in db["records"]:
        print(f"\n  [{rec.get('record_id')}] {rec.get('name')} | {rec.get('email')}", end="")
        if rec.get("age"):
            print(f" | Age: {rec.get('age')}", end="")
        if rec.get("phone"):
            print(f" | Phone: {rec.get('phone')}", end="")
        print(f"\n           Added: {rec.get('timestamp')}")
    print("="*55)


# ─────────────────────────────────────────────
#  SECTION 7: DEMO — Run this to see it in action
# ─────────────────────────────────────────────

if __name__ == "__main__":

    print("\n" + "🔷"*27)
    print("  DATA VALIDATION SYSTEM - DEMO RUN")
    print("🔷"*27)

    # Load (or create) our database
    db = load_database()

    # ── TEST BATCH 1: Valid, unique records ───────────────
    print("\n\n📌 BATCH 1: Adding valid, unique records")
    add_record({"name": "Alice Johnson",  "email": "alice@example.com", "age": "29", "phone": "555-1234"}, db)
    add_record({"name": "Bob Smith",      "email": "bob@example.com",   "age": "35", "phone": "555-5678"}, db)
    add_record({"name": "Carol White",    "email": "carol@example.com", "age": "42"                      }, db)

    # ── TEST BATCH 2: Exact duplicates (should be BLOCKED) ──
    print("\n\n📌 BATCH 2: Trying to add exact duplicates")
    add_record({"name": "Alice Johnson",  "email": "alice@example.com", "age": "29", "phone": "555-1234"}, db)
    add_record({"name": "Bob Smith",      "email": "bob@example.com",   "age": "35", "phone": "555-5678"}, db)

    # ── TEST BATCH 3: Near duplicates (should be FLAGGED) ───
    print("\n\n📌 BATCH 3: Near duplicates (slight variations)")
    add_record({"name": "Alicia Johnson", "email": "alice@example.com", "age": "29"}, db)  # Same email
    add_record({"name": "Bob Smyth",      "email": "bob@example.com",   "age": "35"}, db)  # Typo in name

    # ── TEST BATCH 4: Invalid data (should be REJECTED) ─────
    print("\n\n📌 BATCH 4: Invalid / malformed data")
    add_record({"name": "",               "email": "noname@example.com"             }, db)  # Empty name
    add_record({"name": "Dave",           "email": "not-an-email"                   }, db)  # Bad email
    add_record({"name": "Eve",            "email": "eve@example.com", "age": "999"  }, db)  # Impossible age
    add_record({"name": "Frank",          "email": "frank@example.com","phone": "abc"}, db) # Bad phone

    # ── BATCH 5: New unique valid entry ─────────────────────
    print("\n\n📌 BATCH 5: New unique valid entry")
    add_record({"name": "Diana Prince", "email": "diana@example.com", "age": "31", "phone": "555-9999"}, db)

    # ── FINAL REPORT ────────────────────────────────────────
    print_database_report(db)
