"""Add enum-like CHECK constraints

Revision ID: add_enum_checks_002
Revises: float_to_numeric_001
Create Date: 2026-05-03
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_enum_checks_002"
down_revision = "float_to_numeric_001"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    if _table_exists("kullanicilar"):
        with op.batch_alter_table("kullanicilar", schema=None) as batch_op:
            batch_op.create_check_constraint(
                "check_user_role",
                "role IN ('user','admin')",
            )

    if _table_exists("alis_faturalari"):
        with op.batch_alter_table("alis_faturalari", schema=None) as batch_op:
            batch_op.create_check_constraint(
                "check_alis_durum",
                "durum IN ('beklemede','odendi','iptal')",
            )

    if _table_exists("satis_faturalari"):
        with op.batch_alter_table("satis_faturalari", schema=None) as batch_op:
            batch_op.create_check_constraint(
                "check_satis_durum",
                "durum IN ('beklemede','tahsil_edildi','iptal')",
            )

    if _table_exists("iade_faturalari"):
        with op.batch_alter_table("iade_faturalari", schema=None) as batch_op:
            batch_op.create_check_constraint(
                "check_iade_turu",
                "iade_turu IN ('alis_iade','satis_iade')",
            )
            batch_op.create_check_constraint(
                "check_iade_durum",
                "durum IN ('beklemede','tamamlandi','iptal')",
            )


def downgrade():
    if _table_exists("iade_faturalari"):
        with op.batch_alter_table("iade_faturalari", schema=None) as batch_op:
            batch_op.drop_constraint("check_iade_durum", type_="check")
            batch_op.drop_constraint("check_iade_turu", type_="check")

    if _table_exists("satis_faturalari"):
        with op.batch_alter_table("satis_faturalari", schema=None) as batch_op:
            batch_op.drop_constraint("check_satis_durum", type_="check")

    if _table_exists("alis_faturalari"):
        with op.batch_alter_table("alis_faturalari", schema=None) as batch_op:
            batch_op.drop_constraint("check_alis_durum", type_="check")

    if _table_exists("kullanicilar"):
        with op.batch_alter_table("kullanicilar", schema=None) as batch_op:
            batch_op.drop_constraint("check_user_role", type_="check")
