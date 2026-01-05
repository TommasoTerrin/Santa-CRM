"""
Test script to verify extraction flow from file to SQLite database.
Processes a few good letters and saves them to db_test.db.
"""
import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session, select
from src.extractors import LetterExtractor
from src.models import Child, Letter

# 1. Setup SQLite Test DB
DB_FILE = "db_test.db"
DATABASE_URL = f"sqlite:///{DB_FILE}"
engine = create_engine(DATABASE_URL, echo=False)

def init_test_db():
    """Create tables in the test database."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    print(f"🔧 Initializing test database: {DB_FILE}")
    SQLModel.metadata.create_all(engine)

def run_test():
    init_test_db()
    
    extractor = LetterExtractor()
    
    # Selected test letters (assuming they are good)
    test_files = [
        Path("data/test_letters/child_italy_000.txt"),
        Path("data/test_letters/child_usa_012.txt")
    ]
    
    with Session(engine) as session:
        for file_path in test_files:
            if not file_path.exists():
                print(f"⚠ Skipping {file_path.name} (not found)")
                continue
            
            print(f"\n📬 Processing {file_path.name}...")
            try:
                # Extract objects
                child_new, letter_new = extractor.extract_from_file(file_path)
                
                # Check if child already exists by name/country (simple deduplication for test)
                statement = select(Child).where(Child.name == child_new.name, Child.country == child_new.country)
                existing_child = session.exec(statement).first()
                
                if existing_child:
                    print(f"👤 Found existing child: {existing_child.name}")
                    letter_new.child = existing_child
                else:
                    print(f"👶 Created new child: {child_new.name}")
                    session.add(child_new)
                    letter_new.child = child_new
                
                session.add(letter_new)
                session.commit()
                print(f"✅ Saved {child_new.name}'s letter to DB")
                
            except Exception as e:
                print(f"❌ Error processing {file_path.name}: {e}")
                session.rollback()

    # 2. Verify Data
    print("\n🔍 Verifying Data in DB:")
    with Session(engine) as session:
        children = session.exec(select(Child)).all()
        print(f"\n--- Children ({len(children)}) ---")
        for c in children:
            print(f"ID: {c.id} | Name: {c.name} ({c.gender}) | Country: {c.country}")
            
        letters = session.exec(select(Letter)).all()
        print(f"\n--- Letters ({len(letters)}) ---")
        for l in letters:
            status = "SPAM" if l.is_spam else "VALID"
            child_name = l.child.name if l.child else "Unknown"
            print(f"ID: {l.id} | Child: {child_name} | Score: {l.goodness_score} | Coal: {l.coal_qty_kg}kg | Type: {status}")
            print(f"   Gifts: {l.gift_request}")

if __name__ == "__main__":
    run_test()
