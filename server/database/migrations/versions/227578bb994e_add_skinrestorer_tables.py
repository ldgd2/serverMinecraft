"""add_skinrestorer_tables

Revision ID: 227578bb994e
Revises: c80744b50a6e
Create Date: 2026-05-02 13:42:17.017654

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '227578bb994e'
down_revision: Union[str, None] = 'c80744b50a6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear tabla Skins con el estilo ORM de Alembic
    op.create_table(
        'Skins',
        sa.Column('ID', sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column('Name', sa.String(length=255), nullable=False, unique=True),
        sa.Column('Value', sa.Text(), nullable=False),
        sa.Column('Signature', sa.Text(), nullable=False),
        sa.Column('Timestamp', sa.String(length=255), nullable=False)
    )
    
    # Crear tabla Players
    op.create_table(
        'Players',
        sa.Column('ID', sa.Integer(), sa.Identity(), primary_key=True),
        sa.Column('Nick', sa.String(length=255), nullable=False, unique=True),
        sa.Column('Skin', sa.String(length=255), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('Players')
    op.drop_table('Skins')
