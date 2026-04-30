"""
Seeder Runner
Main entry point to run all database seeders
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.seeders.user_seeder import seed_users
from database.seeders.server_seeder import seed_servers
from database.seeders.bitacora_seeder import seed_bitacora
from database.seeders.version_seeder import seed_versions


def run_all_seeders():
    """Run all database seeders in order"""
    print("=" * 50)
    print("Starting Database Seeding...")
    print("=" * 50)
    
    # Order matters - users first, then servers, versions, and finally bitacora
    seeders = [
        ("Users", seed_users),
        ("Versions", seed_versions),
        ("Servers", seed_servers),
        ("Bitacora", seed_bitacora),
    ]
    
    for name, seeder_func in seeders:
        print(f"\n[SEEDER] Running {name} seeder...")
        try:
            seeder_func()
            print(f"[SEEDER] {name} seeder completed ✓")
        except Exception as e:
            print(f"[SEEDER] {name} seeder failed ✗: {e}")
    
    print("\n" + "=" * 50)
    print("Database Seeding Complete!")
    print("=" * 50)


def run_specific_seeder(seeder_name: str):
    """Run a specific seeder by name"""
    seeders = {
        "users": seed_users,
        "servers": seed_servers,
        "bitacora": seed_bitacora,
        "versions": seed_versions,
    }
    
    seeder_name = seeder_name.lower()
    if seeder_name in seeders:
        print(f"Running {seeder_name} seeder...")
        seeders[seeder_name]()
        print(f"{seeder_name} seeder completed!")
    else:
        print(f"Unknown seeder: {seeder_name}")
        print(f"Available seeders: {', '.join(seeders.keys())}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific seeder
        run_specific_seeder(sys.argv[1])
    else:
        # Run all seeders
        run_all_seeders()
