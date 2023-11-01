"""create offer and product tables

Revision ID: 3d61e6b9a42c
Revises: d4867f3a4c0a
Create Date: 2023-11-01 10:04:52.907862

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3d61e6b9a42c'
down_revision = 'd4867f3a4c0a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('product',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_product_description'), 'product', ['description'], unique=False)
    op.create_index(op.f('ix_product_id'), 'product', ['id'], unique=False)
    op.create_index(op.f('ix_product_name'), 'product', ['name'], unique=False)
    op.create_table('offer',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('price', sa.Integer(), nullable=False),
    sa.Column('items_in_stock', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Uuid(), nullable=False),
    sa.ForeignKeyConstraint(['product_id'], ['product.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_offer_id'), 'offer', ['id'], unique=False)
    op.create_index(op.f('ix_offer_product_id'), 'offer', ['product_id'], unique=False)
    # missing migrations from the base project
    op.alter_column('user', 'email',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('user', 'hashed_password',
               existing_type=sa.VARCHAR(),
               nullable=False)


def downgrade():
    op.alter_column('user', 'hashed_password',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('user', 'email',
               existing_type=sa.VARCHAR(),
               nullable=True)
    # The above are missing migrations from the base project
    op.drop_index(op.f('ix_offer_product_id'), table_name='offer')
    op.drop_index(op.f('ix_offer_id'), table_name='offer')
    op.drop_table('offer')
    op.drop_index(op.f('ix_product_name'), table_name='product')
    op.drop_index(op.f('ix_product_id'), table_name='product')
    op.drop_index(op.f('ix_product_description'), table_name='product')
    op.drop_table('product')
