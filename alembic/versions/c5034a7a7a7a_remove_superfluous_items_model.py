"""remove superfluous items model

Revision ID: c5034a7a7a7a
Revises: 3d61e6b9a42c
Create Date: 2023-11-07 22:07:56.725797

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c5034a7a7a7a'
down_revision = '3d61e6b9a42c'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index('ix_item_description', table_name='item')
    op.drop_index('ix_item_id', table_name='item')
    op.drop_index('ix_item_title', table_name='item')
    op.drop_table('item')


def downgrade():
    op.create_table('item',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('title', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('owner_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], name='item_owner_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='item_pkey')
    )
    op.create_index('ix_item_title', 'item', ['title'], unique=False)
    op.create_index('ix_item_id', 'item', ['id'], unique=False)
    op.create_index('ix_item_description', 'item', ['description'], unique=False)
