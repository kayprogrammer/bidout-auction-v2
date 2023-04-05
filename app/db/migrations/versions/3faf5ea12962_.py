"""empty message

Revision ID: 3faf5ea12962
Revises: 
Create Date: 2023-04-05 16:52:59.762566

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3faf5ea12962"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "timezones",
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("pkid", sa.Integer(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("pkid"),
        sa.UniqueConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("first_name", sa.String(length=50), nullable=True),
        sa.Column("last_name", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("password", sa.String(), nullable=True),
        sa.Column("tz_id", sa.UUID(), nullable=True),
        sa.Column("is_email_verified", sa.Boolean(), nullable=True),
        sa.Column("is_superuser", sa.Boolean(), nullable=True),
        sa.Column("is_staff", sa.Boolean(), nullable=True),
        sa.Column("pkid", sa.Integer(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tz_id"], ["timezones.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("pkid"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("id"),
    )
    op.create_table(
        "jwts",
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("access", sa.String(), nullable=True),
        sa.Column("refresh", sa.String(), nullable=True),
        sa.Column("pkid", sa.Integer(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("pkid"),
        sa.UniqueConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "otps",
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("code", sa.Integer(), nullable=True),
        sa.Column("pkid", sa.Integer(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("pkid"),
        sa.UniqueConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("otps")
    op.drop_table("jwts")
    op.drop_table("users")
    op.drop_table("timezones")
    # ### end Alembic commands ###
