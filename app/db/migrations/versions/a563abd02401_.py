"""empty message

Revision ID: a563abd02401
Revises: 539952033c53
Create Date: 2023-05-23 16:42:18.033710

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a563abd02401'
down_revision = '539952033c53'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('subscribers',
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('exported', sa.Boolean(), nullable=True),
    sa.Column('pkid', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('pkid'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('id')
    )
    op.drop_table('suscribers')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('suscribers',
    sa.Column('email', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('exported', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('pkid', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('id', sa.UUID(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('pkid', name='suscribers_pkey'),
    sa.UniqueConstraint('email', name='suscribers_email_key'),
    sa.UniqueConstraint('id', name='suscribers_id_key')
    )
    op.drop_table('subscribers')
    # ### end Alembic commands ###
