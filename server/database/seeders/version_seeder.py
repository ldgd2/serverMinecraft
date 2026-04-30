"""
Version Seeder
Seeds Minecraft versions into the database
"""
from database.connection import SessionLocal
from database.models.version import Version


def seed_versions():
    """Seed the versions table with Minecraft versions"""
    db = SessionLocal()
    
    try:
        if not db.query(Version).first():
            print("Seeding Versions...")
            
            versions = [
                Version(
                    name="1.21",
                    type="RELEASE",
                    url="https://piston-data.mojang.com/v1/objects/1.21/server.jar",
                    downloaded=False
                ),
                Version(
                    name="1.20.6",
                    type="RELEASE",
                    url="https://piston-data.mojang.com/v1/objects/1.20.6/server.jar",
                    downloaded=False
                ),
                Version(
                    name="1.20.4",
                    type="RELEASE",
                    url="https://piston-data.mojang.com/v1/objects/1.20.4/server.jar",
                    downloaded=False
                ),
                Version(
                    name="1.20.2",
                    type="RELEASE",
                    url="https://piston-data.mojang.com/v1/objects/1.20.2/server.jar",
                    downloaded=False
                ),
                Version(
                    name="1.19.4",
                    type="RELEASE",
                    url="https://piston-data.mojang.com/v1/objects/1.19.4/server.jar",
                    downloaded=False
                ),
                Version(
                    name="1.18.2",
                    type="RELEASE",
                    url="https://piston-data.mojang.com/v1/objects/1.18.2/server.jar",
                    downloaded=False
                ),
                Version(
                    name="1.16.5",
                    type="RELEASE",
                    url="https://piston-data.mojang.com/v1/objects/1.16.5/server.jar",
                    downloaded=False
                ),
                Version(
                    name="1.12.2",
                    type="RELEASE",
                    url="https://piston-data.mojang.com/v1/objects/1.12.2/server.jar",
                    downloaded=False
                ),
                Version(
                    name="1.8.9",
                    type="RELEASE",
                    url="https://piston-data.mojang.com/v1/objects/1.8.9/server.jar",
                    downloaded=False
                ),
                Version(
                    name="24w14a",
                    type="SNAPSHOT",
                    url="https://piston-data.mojang.com/v1/objects/24w14a/server.jar",
                    downloaded=False
                )
            ]
            
            for version in versions:
                db.add(version)
            
            db.commit()
            print(f"Seeded {len(versions)} Minecraft versions successfully.")
        else:
            print("Versions already exist. Skipping seed.")
    except Exception as e:
        print(f"Error seeding versions: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_versions()
