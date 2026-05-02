import pymysql
from typing import Optional

def get_skin_base64_from_skinrestorer(db_config: dict, player_name: str) -> Optional[str]:
    """
    Consulta la base de datos de SkinRestorer y retorna el valor Base64 de la skin para el jugador.
    db_config: {host, user, password, database}
    """
    conn = pymysql.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT Skin FROM Players WHERE Nick = %s", (player_name,))
            row = cursor.fetchone()
            if not row:
                return None
            skin_name = row['Skin']
            cursor.execute("SELECT Value FROM Skins WHERE Name = %s", (skin_name,))
            skin_row = cursor.fetchone()
            if skin_row:
                return skin_row['Value']
    finally:
        conn.close()
    return None
def set_skin_in_skinrestorer(db_config: dict, player_name: str, skin_value: str, signature: str = "") -> bool:
    """
    Actualiza la skin en la base de datos de SkinRestorer.
    """
    conn = pymysql.connect(
        host=db_config['host'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cursor:
            # 1. Asegurar que la skin existe en la tabla Skins
            # Usamos el nombre del jugador como nombre de la skin para simplificar
            skin_name = f"custom_{player_name}"
            cursor.execute(
                "INSERT INTO Skins (Name, Value, Signature, Timestamp) VALUES (%s, %s, %s, %s) "
                "ON DUPLICATE KEY UPDATE Value=%s, Signature=%s, Timestamp=%s",
                (skin_name, skin_value, signature, "none", skin_value, signature, "none")
            )
            
            # 2. Vincular al jugador en la tabla Players
            cursor.execute(
                "INSERT INTO Players (Nick, Skin) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE Skin=%s",
                (player_name, skin_name, skin_name)
            )
            conn.commit()
            return True
    except Exception as e:
        print(f"Error updating SkinRestorer: {e}")
        return False
    finally:
        conn.close()
