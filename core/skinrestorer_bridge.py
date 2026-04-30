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
