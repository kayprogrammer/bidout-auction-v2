"""Changed user session to guest user

Revision ID: a586b8ceabd8
Revises: 352e48beae40
Create Date: 2023-06-04 23:13:13.838020

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a586b8ceabd8'
down_revision = '352e48beae40'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('guestusers',
    sa.Column('pkid', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('pkid'),
    sa.UniqueConstraint('id')
    )
    op.drop_table('usersessions')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('usersessions',
    sa.Column('pkid', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('pkid', name='usersessions_pkey'),
    sa.UniqueConstraint('id', name='usersessions_id_key')
    )
    op.drop_table('guestusers')
    # ### end Alembic commands ###
