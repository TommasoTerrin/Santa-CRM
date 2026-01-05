"""
Fake ETL - Direct Database Population Script
Bypasses LLM extraction by loading pre-made JSON data.
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the Elf-ETL module to path for model access
sys.path.insert(0, str(Path(__file__).parent.parent / "Elf-ETL module" / "src"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from sqlmodel import SQLModel, create_engine, Session
from core.models import Child, Letter, CountryEnum, GenderEnum


def get_engine():
    """Create database engine from environment."""
    db_url = os.getenv("SANTA_DB_URL")
    if not db_url:
        raise ValueError("SANTA_DB_URL not found in environment!")
    return create_engine(db_url, echo=False)


def reset_and_init_db(engine):
    """Drop and recreate all tables."""
    print("🗑️  Dropping existing tables...")
    SQLModel.metadata.drop_all(engine)
    print("🔨 Creating fresh tables...")
    SQLModel.metadata.create_all(engine)


def load_fake_data(json_path: Path, engine) -> tuple[int, int]:
    """Load fake children data from JSON into database."""
    with open(json_path, "r", encoding="utf-8") as f:
        children_data = json.load(f)
    
    children_count = 0
    letters_count = 0
    
    with Session(engine) as session:
        for data in children_data:
            # Map country string to enum
            country_str = data["country"].lower()
            try:
                country = CountryEnum(country_str)
            except ValueError:
                country = CountryEnum.UNKNOWN
            
            # Map gender string to enum
            gender_str = data["gender"].lower()
            gender = GenderEnum(gender_str)
            
            # Create Child
            child = Child(
                name=data["name"],
                age=data["age"],
                city=data["city"],
                country=country,
                gender=gender
            )
            session.add(child)
            session.commit()
            session.refresh(child)
            children_count += 1
            
            # Create Letter
            letter = Letter(
                content=data["letter"],
                is_spam=False,
                received_at=datetime.utcnow(),
                goodness_score=data["goodness"],
                gift_request=data["gifts"],
                child_id=child.id
            )
            session.add(letter)
            session.commit()
            letters_count += 1
            
            print(f"   ✅ Loaded: {child.name} ({child.country.value}) - {len(data['gifts'])} gifts")
    
    return children_count, letters_count


def main():
    print("🎄" + "="*50 + "🎄")
    print("     FAKE ETL - Direct Database Population")
    print("🎄" + "="*50 + "🎄\n")
    
    # Get paths
    script_dir = Path(__file__).parent
    json_path = script_dir / "fake_children.json"
    
    if not json_path.exists():
        print(f"❌ Error: {json_path} not found!")
        return
    
    # Create engine
    engine = get_engine()
    
    # Reset DB
    print("🔄 Resetting Database...")
    reset_and_init_db(engine)
    
    # Load data
    print("\n📥 Loading fake children data...")
    children_count, letters_count = load_fake_data(json_path, engine)
    
    print("\n" + "="*50)
    print(f"✨ SUCCESS! Loaded {children_count} children and {letters_count} letters!")
    print("="*50)
    print("\n🎅 Database is now populated and ready for Metabase! 🎅")


if __name__ == "__main__":
    main()
