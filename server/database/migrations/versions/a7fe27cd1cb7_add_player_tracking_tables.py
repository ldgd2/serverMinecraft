"""add_player_tracking_tables

Revision ID: a7fe27cd1cb7
Revises: 1228e00c2718
Create Date: 2026-01-06 10:12:40.305459

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7fe27cd1cb7'
down_revision: Union[str, None] = '1228e00c2718'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # players table
    if not conn.execute(sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='players'")).fetchone():
        op.create_table('players',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('server_id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.String(), nullable=True),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['server_id'], ['servers.id'], name=op.f('fk_players_server_id_servers')),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_players'))
        )
        with op.batch_alter_table('players', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_players_name'), ['name'], unique=False)
            batch_op.create_index(batch_op.f('ix_players_uuid'), ['uuid'], unique=False)

    # player_details table
    if not conn.execute(sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='player_details'")).fetchone():
        op.create_table('player_details',
            sa.Column('player_id', sa.Integer(), nullable=False),
            sa.Column('total_playtime_seconds', sa.Integer(), nullable=True),
            sa.Column('last_joined_at', sa.DateTime(), nullable=True),
            sa.Column('last_ip', sa.String(), nullable=True),
            sa.ForeignKeyConstraint(['player_id'], ['players.id'], name='fk_player_details_player'),
            sa.PrimaryKeyConstraint('player_id', name=op.f('pk_player_details'))
        )

    # player_achievements table
    if not conn.execute(sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='player_achievements'")).fetchone():
        op.create_table('player_achievements',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('player_id', sa.Integer(), nullable=False),
            sa.Column('achievement_id', sa.String(), nullable=True),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('unlocked_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['player_id'], ['players.id'], name='fk_player_achievements_player'),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_player_achievements'))
        )
        with op.batch_alter_table('player_achievements', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_player_achievements_id'), ['id'], unique=False)

    # player_bans table
    if not conn.execute(sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='player_bans'")).fetchone():
        op.create_table('player_bans',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('player_id', sa.Integer(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('reason', sa.String(), nullable=True),
            sa.Column('source', sa.String(), nullable=True),
            sa.Column('issued_at', sa.DateTime(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['player_id'], ['players.id'], name='fk_player_bans_player'),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_player_bans'))
        )
        with op.batch_alter_table('player_bans', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_player_bans_id'), ['id'], unique=False)

    # player_stats table
    if not conn.execute(sa.text("SELECT 1 FROM information_schema.tables WHERE table_name='player_stats'")).fetchone():
        op.create_table('player_stats',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('player_id', sa.Integer(), nullable=False),
            sa.Column('stat_key', sa.String(), nullable=True),
            sa.Column('stat_value', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['player_id'], ['players.id'], name='fk_player_stats_player'),
            sa.PrimaryKeyConstraint('id', name=op.f('pk_player_stats'))
        )
        with op.batch_alter_table('player_stats', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_player_stats_id'), ['id'], unique=False)
            batch_op.create_index(batch_op.f('ix_player_stats_stat_key'), ['stat_key'], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    for table in ['player_stats', 'player_bans', 'player_achievements', 'player_details', 'players']:
        if conn.execute(sa.text(f"SELECT 1 FROM information_schema.tables WHERE table_name='{table}'")).fetchone():
            op.drop_table(table)

