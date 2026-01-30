
import asyncio
import os
import shutil
from pathlib import Path
from uuid import uuid4

# Set up dummy environment if not present
if "LLM_API_KEY" not in os.environ:
    print("WARNING: LLM_API_KEY not found. Some operations (cognify) will fail or be skipped.")
    # We can set a dummy one just to pass initialization checks if needed, 
    # but cognee might validate it.
    os.environ["LLM_API_KEY"] = "dummy-key"
    
# Set local storage paths to avoid issues
os.environ["COGNEE_DATA_ROOT_DIRECTORY"] = os.path.abspath(".cognee_data")
os.environ["COGNEE_SYSTEM_ROOT_DIRECTORY"] = os.path.abspath(".cognee_system")


import cognee
from cognee.modules.users.methods import create_user
from cognee.modules.users.models import User

from cognee.base_config import get_base_config

async def main():
    print("--- Cognee Multi-User & Persistence Demo ---")

    # 1. Setup paths
    # By default, cognee uses .data_storage and .cognee_system in the current directory (or user home)
    # We can force a local directory for this test
    base_config = get_base_config()
    print(f"Data Root: {base_config.data_root_directory}")
    print(f"System Root: {base_config.system_root_directory}")

    # Clean up previous run if exists (optional, for fresh test)
    # if os.path.exists(".data_storage"):
    #     shutil.rmtree(".data_storage")
    
    # 2. Create Users
    print("\n[+] Creating Users...")
    try:
        user1 = await create_user(email=f"user1_{uuid4()}@example.com", password="password123")
        user2 = await create_user(email=f"user2_{uuid4()}@example.com", password="password123")
        print(f"User 1: {user1.email} (ID: {user1.id})")
        print(f"User 2: {user2.email} (ID: {user2.id})")
    except Exception as e:
        print(f"Error creating users: {e}")
        return

    # 3. Add Data (Segregated)
    print("\n[+] Adding Data...")
    
    # User 1 Data
    txt1 = "The secret code for User 1 is APPLE-42."
    print(f"Adding data for User 1: '{txt1}'")
    await cognee.add(txt1, dataset_name="user1_secrets", user=user1)

    # User 2 Data
    txt2 = "The secret code for User 2 is BANANA-99."
    print(f"Adding data for User 2: '{txt2}'")
    await cognee.add(txt2, dataset_name="user2_secrets", user=user2)

    # 4. Check Storage Persistence
    print("\n[+] Checking Storage Persistence...")
    # Inspect .data_storage structure
    data_storage_path = Path(base_config.data_root_directory)
    if data_storage_path.exists():
        print(f"Storage directory exists at: {data_storage_path}")
        # List subdirectories to see how it's organized
        for item in data_storage_path.glob("**/*"):
            if item.is_file():
                # Show relative path to see structure
                try:
                   rel_path = item.relative_to(data_storage_path)
                   print(f" - {rel_path}")
                except:
                    pass
    else:
        print("Storage directory not found yet (might need cognify to flush to disk).")

    # 5. Gemini Setup (Commented Example)
    print("\n[+] Gemini Configuration Info:")
    print("To use Gemini, you would set the following environment variables:")
    print('  os.environ["LLM_PROVIDER"] = "gemini"')
    print('  os.environ["LLM_API_KEY"] = "YOUR_GOOGLE_AI_API_KEY"')
    print('  os.environ["LLM_MODEL"] = "gemini-1.5-flash" (or similar)')
    
    # Note: 'cognify' is required to actually process/store the graph and vectors.
    # Without a valid API key, we can't run this step effectively in this demo script.
    # But if enabled:
    # await cognee.cognify(user=user1) 
    
    print("\n[+] Demo Complete. Data is persisted in the directories above.")

if __name__ == "__main__":
    asyncio.run(main())
