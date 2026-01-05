"""
Main Entry Point for Elf-ETL.
Orchestrates the Single File Pipeline execution.
"""
import time
import sys
import os
from pathlib import Path

# Add src to pythonpath
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import reset_db
from pipeline.flow import build_single_file_pipeline

def main():
    # 1. Initialize DB
    max_retries = 5
    for i in range(max_retries):
        try:
            print(f"🎄 Resetting & Initializing Database (Attempt {i+1}/{max_retries})...")
            reset_db()
            break
        except Exception as e:
            if i == max_retries - 1:
                print(f"💥 Failed to connect to DB after {max_retries} attempts: {e}")
                raise
            print(f"  ⏳ DB not ready yet, waiting 2s... ({e})")
            time.sleep(2)

    # 2. Clear Logs
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file = os.path.join(base_dir, "logs", "pipeline.log")
    if os.path.exists(log_file):
        print("🧹 Clearing pipeline log...")
        with open(log_file, "w") as f:
            f.truncate(0)

    # 3. Build Pipeline
    print("🚂 Building Single-File Functional Pipeline...")
    pipeline = build_single_file_pipeline()
    
    # 4. Define Test Files (Dynamic Scan)
    data_dir = os.path.join(base_dir, "data", "test_letters")
    test_files = []
    if os.path.exists(data_dir):
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith(".txt"):
                    # Get relative path from base_dir for the loop below
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, base_dir)
                    test_files.append(rel_path)
    else:
        print(f"⚠️ Warning: Data directory not found at {data_dir}")

    if not test_files:
        print("⚠️ No .txt files found to process!")
    
    # 4. Loop and Execute
    print(f"📬 Starting Processing of {len(test_files)} files...")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for relative_path in test_files:
        full_path = os.path.join(base_dir, relative_path)
        print(f"\n📄 Processing: {relative_path}")
        
        try:
            # We assume the "read" node takes "file_path" as argument.
            # In DataPizza, initial_data keys match the node names.
            # And the value is passed to the _run method.
            # Our FileReader._run takes 'file_path'.
            
            # NOTE: With target_key not set on the first node, 
            # the value of initial_data["read"] is passed as **kwargs or positional?
            # Based on docs/tests, it's safer to pass a dict if expecting specific args,
            # BUT our FileReader takes a single argument 'file_path'.
            # Let's try passing the value directly for the node 'read'.
            
            results = pipeline.execute(initial_data={
                "read": {"file_path": full_path} 
                # passing a dict here means FileReader._run receives this dict as **kwargs?
                # Or as the first argument?
                # Our previous error suggested mismatched args.
                # Let's rely on the fix in FileReader which accepts `file_path`.
                # If we pass {"file_path": ...}, it should map to the argument `file_path`.
            })
            
            # Check results to see what happened (optional)
            if "log_spam" in results and results["log_spam"]:
                print(f"   🚫 {results['log_spam']}")
            elif "load" in results:
                print(f"   ✅ Letter Saved!")
            else:
                print("   ⚠️ Unknown Result State")
                
        except Exception as e:
            print(f"   💥 Error processing file: {e}")
            # print full stack trace for debugging
            import traceback
            traceback.print_exc()

        # Rate Limit spacing
        print("   💤 Sleeping 35s to respect API Quota...")
        time.sleep(35)

    print("\n✨ Batch Processing Completed! ✨")

if __name__ == "__main__":
    main()
