"""empty message

Revision ID: 5b9ee3b1fde0
Revises: 65bae104092c
Create Date: 2023-04-10 15:05:07.099954

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5b9ee3b1fde0"
down_revision = "65bae104092c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "usersessions",
        sa.Column("pkid", sa.Integer(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("pkid"),
        sa.UniqueConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("usersessions")
    # ### end Alembic commands ###