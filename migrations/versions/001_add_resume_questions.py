"""Add resume questions table

Revision ID: 001
Revises: 
Create Date: 2024-03-07
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # 새로운 테이블 생성
    op.create_table(
        'resume_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resume_id', sa.Integer(), nullable=True),
        sa.Column('question', sa.String(), nullable=True),
        sa.Column('answer', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resume_questions_id'), 'resume_questions', ['id'], unique=False)

def downgrade():
    # 테이블 삭제
    op.drop_index(op.f('ix_resume_questions_id'), table_name='resume_questions')
    op.drop_table('resume_questions') 