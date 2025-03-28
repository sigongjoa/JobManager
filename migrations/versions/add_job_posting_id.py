"""add job_posting_id column to resumes table

Revision ID: add_job_posting_id
Create Date: 2024-03-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_job_posting_id'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('resumes', sa.Column('job_posting_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'resumes', 'job_postings', ['job_posting_id'], ['id'])
    # ### end Alembic commands ###

def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'resumes', type_='foreignkey')
    op.drop_column('resumes', 'job_posting_id')
    # ### end Alembic commands ### 