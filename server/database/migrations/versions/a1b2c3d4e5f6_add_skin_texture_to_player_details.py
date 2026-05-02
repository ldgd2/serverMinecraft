"""add skin texture to player_details

Revision ID: a1b2c3d4e5f6
Revises: c80744b50a6e, 227578bb994e
Create Date: 2026-05-02

Merge de cabezas + añade skin_value y skin_signature a player_details.
Reemplaza tablas separadas de SkinRestorer con columnas en player_details
y VIEWs para compatibilidad con el mod (sin tablas extra).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, tuple] = ('c80744b50a6e', '227578bb994e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Añadir columnas de textura firmada a player_details de forma segura
    # Usamos execute con raw SQL para aprovechar IF NOT EXISTS y evitar que falle si ya las creamos manualmente
    op.execute('ALTER TABLE player_details ADD COLUMN IF NOT EXISTS skin_url VARCHAR')
    op.execute('ALTER TABLE player_details ADD COLUMN IF NOT EXISTS skin_value TEXT')
    op.execute('ALTER TABLE player_details ADD COLUMN IF NOT EXISTS skin_signature TEXT')

    # Crear VIEWs para SkinRestorer (lee de player_details, sin tablas extra)
    op.execute("""
        CREATE OR REPLACE VIEW "Skins" AS
        SELECT
            pd.player_id AS "ID",
            CONCAT('custom_', p.name) AS "Name",
            pd.skin_value AS "Value",
            COALESCE(pd.skin_signature, '') AS "Signature",
            'none' AS "Timestamp"
        FROM player_details pd
        JOIN players p ON pd.player_id = p.id
        WHERE pd.skin_value IS NOT NULL
    """)

    op.execute("""
        CREATE OR REPLACE VIEW "Players" AS
        SELECT
            p.id AS "ID",
            p.name AS "Nick",
            CONCAT('custom_', p.name) AS "Skin"
        FROM players p
        JOIN player_details pd ON pd.player_id = p.id
        WHERE pd.skin_value IS NOT NULL
    """)


def downgrade() -> None:
    op.execute('DROP VIEW IF EXISTS "Players"')
    op.execute('DROP VIEW IF EXISTS "Skins"')
    op.drop_column('player_details', 'skin_signature')
    op.drop_column('player_details', 'skin_value')
    op.drop_column('player_details', 'skin_url')
