"""add on delete cascade for foreign keys

Revision ID: 50f2dad864b6
Revises: c875424dbf9b
Create Date: 2024-05-17 11:08:04.125154+03:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '50f2dad864b6'
down_revision = 'ae770d64f644'
branch_labels = None
depends_on = None
from sqlalchemy import Inspector


def update_foreign_key_ondelete(inspector, table_name, column_name, ondelete_value):
    foreign_keys = inspector.get_foreign_keys(table_name)

    for foreign_key in foreign_keys:
        foreign_key_name = f"{table_name}_{column_name}_fkey"

        if column_name in foreign_key['constrained_columns'] and foreign_key['name'] == foreign_key_name:
            # if ondelete is not exists - foreign key doesn't have "delete rule"
            # or in case he has another rule
            if (foreign_key['options'].get('ondelete') is None or
                    foreign_key['options']['ondelete'] != ondelete_value):
                op.drop_constraint(foreign_key['name'], table_name=table_name, type_='foreignkey')
                op.create_foreign_key(constraint_name=foreign_key['name'],
                                      source_table=table_name,
                                      referent_table=foreign_key['referred_table'],
                                      local_cols=foreign_key['constrained_columns'],
                                      remote_cols=foreign_key['referred_columns'],
                                      ondelete=ondelete_value)


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn.engine)
    tables = inspector.get_table_names()
    if 'granularity' in tables:
        update_foreign_key_ondelete(inspector, 'granularity', 'kpi_id', 'CASCADE')

    if 'kpi_values' in tables:
        update_foreign_key_ondelete(inspector, 'kpi_values', 'granularity_id', 'CASCADE')
        update_foreign_key_ondelete(inspector, 'kpi_values', 'kpi_id', 'CASCADE')


def downgrade():
    pass
