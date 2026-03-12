# Data Redundancy Removal System

A Python-based system designed to identify, classify, and prevent redundant or false positive data from being stored in a cloud database. Built as part of my Cloud Computing Internship.

## What It Does

- Detects **exact duplicates** using SHA-256 hashing
- Flags **near-duplicates** using similarity detection (Dice Coefficient algorithm)
- **Validates** every entry before saving (email format, required fields, age range, phone number)
- **Blocks** redundant or invalid data from entering the database
- **Appends only clean, unique, verified data** to the cloud database

## How It Works

Every new record goes through 4 steps:

1. **Validation** — Is the data real and complete?
2. **Exact Duplicate Check** — Does this record already exist? (via SHA-256 hash)
3. **Near Duplicate Check** — Is it 85%+ similar to an existing record?
4. **Save** — Only if all 3 checks pass, the record gets saved with an auto-assigned ID and timestamp

## Project Structure
```
data-redundancy-removal-system/
├── main.py               # Main Python script
└── cloud_database.json   # Auto-generated database file
```

## How To Run
```bash
python main.py
```

No additional libraries needed — only built-in Python modules are used.

## Sample Output
```
✅ ADDED        → Unique and valid record saved
🔁 EXACT DUPLICATE  → Blocked, already exists
⚠️ NEAR DUPLICATE   → Flagged, too similar to existing record
❌ INVALID DATA     → Rejected, failed validation
```

## Tech Stack

- **Language:** Python 3.x
- **Database:** JSON (simulated cloud database)
- **Libraries:** hashlib, json, re, datetime (all built-in)

## 🖼️ Screenshots

<img width="1917" height="975" alt="image" src="https://github.com/user-attachments/assets/d137c36d-ed2d-4a82-9c37-00b3fa881114" />
<img width="1918" height="977" alt="image" src="https://github.com/user-attachments/assets/adb66973-b2e2-4f9e-836d-4f93f1726016" />



## 👤 Author

**Asna Haris** — Cloud Computing Intern

- GitHub: https://github.com/asnaharis06-bot
- LinkedIn: https://www.linkedin.com/in/asna-haris-684058319

## 🔗 Project Links

- 📂 GitHub: [data-redundancy-removal-system](https://github.com/asnah/data-redundancy-removal-system)

## 📄 License

This project is built as part of my Cloud Computing Internship Program.

Website: https://www.codealpha.tech
