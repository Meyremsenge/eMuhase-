"""
Database Migration: Float to Numeric, Add Audit Trail, Soft Delete

Revision ID: float_to_numeric_001
Revises: cf95fc97ef3f
Create Date: 2026-03-26 12:00:00.000000

Bu migration:
1. Float → Numeric(12,2) finansal alanları günceller
2. AuditLog tablosu ekler
3. Soft delete (silinme_tarihi) kolonu ekler
4. CHECK constraints ekler (KDV, indirim, miktar aralıkları)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = 'float_to_numeric_001'
down_revision = 'cf95fc97ef3f'
branch_labels = None
depends_on = None


def upgrade():
    # ═══════════════════════════════════════════════════════════
    # AuditLog Tablosunu Oluştur
    # ═══════════════════════════════════════════════════════════
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tablo_adi', sa.String(length=100), nullable=False),
        sa.Column('kayit_id', sa.Integer(), nullable=False),
        sa.Column('islem_tipi', sa.String(length=20), nullable=False),
        sa.Column('eski_veriler', sa.JSON(), nullable=True),
        sa.Column('yeni_veriler', sa.JSON(), nullable=True),
        sa.Column('degisen_alanlar', sa.JSON(), nullable=True),
        sa.Column('olusturma_tarihi', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_tablo_adi'), 'audit_logs', ['tablo_adi'], unique=False)
    op.create_index(op.f('ix_audit_logs_kayit_id'), 'audit_logs', ['kayit_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_olusturma_tarihi'), 'audit_logs', ['olusturma_tarihi'], unique=False)

    # ═══════════════════════════════════════════════════════════
    # Ürünler tablosuna Soft Delete + Constraints
    # ═══════════════════════════════════════════════════════════
    op.add_column('urunler', sa.Column('silinme_tarihi', sa.DateTime(), nullable=True))
    
    # Float → Numeric('12', '2')
    with op.batch_alter_table('urunler', schema=None) as batch_op:
        batch_op.alter_column('alis_fiyat',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='0.00')
        batch_op.alter_column('satis_fiyat',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='0.00')
        batch_op.alter_column('stok_miktari',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='0.00')
        # Constraints ekle
        batch_op.create_check_constraint('check_kdv_orani', 'kdv_orani >= 0 AND kdv_orani <= 100')
        batch_op.create_check_constraint('check_alis_fiyat', 'alis_fiyat >= 0')
        batch_op.create_check_constraint('check_satis_fiyat', 'satis_fiyat >= 0')
        batch_op.create_check_constraint('check_stok_miktari', 'stok_miktari >= 0')

    # ═══════════════════════════════════════════════════════════
    # Müşteriler tablosuna Soft Delete
    # ═══════════════════════════════════════════════════════════
    op.add_column('musteriler', sa.Column('silinme_tarihi', sa.DateTime(), nullable=True))

    # ═══════════════════════════════════════════════════════════
    # Alış Faturalari - Float → Numeric + Constraints + Soft Delete
    # ═══════════════════════════════════════════════════════════
    op.add_column('alis_faturalari', sa.Column('silinme_tarihi', sa.DateTime(), nullable=True))
    op.create_index('ix_alis_faturalari_fatura_no', 'alis_faturalari', ['fatura_no'], unique=False)
    
    with op.batch_alter_table('alis_faturalari', schema=None) as batch_op:
        batch_op.alter_column('ara_toplam',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='0.00')
        batch_op.alter_column('kdv_toplam',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='0.00')
        batch_op.alter_column('indirim_toplam',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='0.00')
        batch_op.alter_column('genel_toplam',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='0.00')
        batch_op.create_check_constraint('check_alis_ara_toplam', 'ara_toplam >= 0')
        batch_op.create_check_constraint('check_alis_kdv_toplam', 'kdv_toplam >= 0')
        batch_op.create_check_constraint('check_alis_indirim_toplam', 'indirim_toplam >= 0')
        batch_op.create_check_constraint('check_alis_genel_toplam', 'genel_toplam >= 0')

    # ═══════════════════════════════════════════════════════════
    # Alış Fatura Kalemleri - Float → Numeric + Constraints
    # ═══════════════════════════════════════════════════════════
    with op.batch_alter_table('alis_fatura_kalemleri', schema=None) as batch_op:
        batch_op.alter_column('miktar',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='1')
        batch_op.alter_column('birim_fiyat',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='0.00')
        # indirim_orani: Float → Integer (%)
        batch_op.alter_column('indirim_orani',
               existing_type=sa.Float(),
               type_=sa.Integer(),
               existing_nullable=True,
               nullable=False,
               server_default='0')
        batch_op.create_check_constraint('check_alis_kalem_miktar', 'miktar > 0')
        batch_op.create_check_constraint('check_alis_kalem_fiyat', 'birim_fiyat >= 0')
        batch_op.create_check_constraint('check_alis_kalem_kdv', 'kdv_orani >= 0 AND kdv_orani <= 100')
        batch_op.create_check_constraint('check_alis_kalem_indirim', 'indirim_orani >= 0 AND indirim_orani <= 100')

    # ═══════════════════════════════════════════════════════════
    # Satış Faturalari - Float → Numeric + Constraints + Soft Delete
    # ═══════════════════════════════════════════════════════════
    op.add_column('satis_faturalari', sa.Column('silinme_tarihi', sa.DateTime(), nullable=True))
    op.create_index('ix_satis_faturalari_fatura_no', 'satis_faturalari', ['fatura_no'], unique=False)
    
    with op.batch_alter_table('satis_faturalari', schema=None) as batch_op:
        batch_op.alter_column('ara_toplam',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='0.00')
        batch_op.alter_column('kdv_toplam',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='0.00')
        batch_op.alter_column('indirim_toplam',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='0.00')
        batch_op.alter_column('genel_toplam',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='0.00')
        batch_op.create_check_constraint('check_satis_ara_toplam', 'ara_toplam >= 0')
        batch_op.create_check_constraint('check_satis_kdv_toplam', 'kdv_toplam >= 0')
        batch_op.create_check_constraint('check_satis_indirim_toplam', 'indirim_toplam >= 0')
        batch_op.create_check_constraint('check_satis_genel_toplam', 'genel_toplam >= 0')

    # ═══════════════════════════════════════════════════════════
    # Satış Fatura Kalemleri - Float → Numeric + Constraints
    # ═══════════════════════════════════════════════════════════
    with op.batch_alter_table('satis_fatura_kalemleri', schema=None) as batch_op:
        batch_op.alter_column('miktar',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='1')
        batch_op.alter_column('birim_fiyat',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='0.00')
        # indirim_orani: Float → Integer (%)
        batch_op.alter_column('indirim_orani',
               existing_type=sa.Float(),
               type_=sa.Integer(),
               existing_nullable=True,
               nullable=False,
               server_default='0')
        batch_op.create_check_constraint('check_satis_kalem_miktar', 'miktar > 0')
        batch_op.create_check_constraint('check_satis_kalem_fiyat', 'birim_fiyat >= 0')
        batch_op.create_check_constraint('check_satis_kalem_kdv', 'kdv_orani >= 0 AND kdv_orani <= 100')
        batch_op.create_check_constraint('check_satis_kalem_indirim', 'indirim_orani >= 0 AND indirim_orani <= 100')

    # ═══════════════════════════════════════════════════════════
    # İade Faturalari - Float → Numeric + Constraints + Soft Delete
    # ═══════════════════════════════════════════════════════════
    op.add_column('iade_faturalari', sa.Column('silinme_tarihi', sa.DateTime(), nullable=True))
    op.create_index('ix_iade_faturalari_fatura_no', 'iade_faturalari', ['fatura_no'], unique=False)
    
    with op.batch_alter_table('iade_faturalari', schema=None) as batch_op:
        batch_op.alter_column('ara_toplam',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='0.00')
        batch_op.alter_column('kdv_toplam',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='0.00')
        batch_op.alter_column('genel_toplam',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='0.00')
        batch_op.create_check_constraint('check_iade_ara_toplam', 'ara_toplam >= 0')
        batch_op.create_check_constraint('check_iade_kdv_toplam', 'kdv_toplam >= 0')
        batch_op.create_check_constraint('check_iade_genel_toplam', 'genel_toplam >= 0')

    # ═══════════════════════════════════════════════════════════
    # İade Fatura Kalemleri - Float → Numeric + Constraints
    # ═══════════════════════════════════════════════════════════
    with op.batch_alter_table('iade_fatura_kalemleri', schema=None) as batch_op:
        batch_op.alter_column('miktar',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='1')
        batch_op.alter_column('birim_fiyat',
               existing_type=sa.Float(),
               type_=sa.Numeric(precision=12, scale=2),
               existing_nullable=True,
               nullable=False,
               server_default='0.00')
        batch_op.create_check_constraint('check_iade_kalem_miktar', 'miktar > 0')
        batch_op.create_check_constraint('check_iade_kalem_fiyat', 'birim_fiyat >= 0')
        batch_op.create_check_constraint('check_iade_kalem_kdv', 'kdv_orani >= 0 AND kdv_orani <= 100')


def downgrade():
    """Downgrade işlemleri - Eski haline döndür"""
    # İade Fatura Kalemleri
    with op.batch_alter_table('iade_fatura_kalemleri', schema=None) as batch_op:
        batch_op.drop_constraint('check_iade_kalem_kdv', type_='check')
        batch_op.drop_constraint('check_iade_kalem_fiyat', type_='check')
        batch_op.drop_constraint('check_iade_kalem_miktar', type_='check')
        batch_op.alter_column('birim_fiyat',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        batch_op.alter_column('miktar',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)

    # İade Faturalari
    with op.batch_alter_table('iade_faturalari', schema=None) as batch_op:
        batch_op.drop_constraint('check_iade_genel_toplam', type_='check')
        batch_op.drop_constraint('check_iade_kdv_toplam', type_='check')
        batch_op.drop_constraint('check_iade_ara_toplam', type_='check')
        batch_op.alter_column('genel_toplam',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        batch_op.alter_column('kdv_toplam',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        batch_op.alter_column('ara_toplam',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        op.drop_index('ix_iade_faturalari_fatura_no', table_name='iade_faturalari')
    
    op.drop_column('iade_faturalari', 'silinme_tarihi')

    # Satış Fatura Kalemleri
    with op.batch_alter_table('satis_fatura_kalemleri', schema=None) as batch_op:
        batch_op.drop_constraint('check_satis_kalem_indirim', type_='check')
        batch_op.drop_constraint('check_satis_kalem_kdv', type_='check')
        batch_op.drop_constraint('check_satis_kalem_fiyat', type_='check')
        batch_op.drop_constraint('check_satis_kalem_miktar', type_='check')
        batch_op.alter_column('indirim_orani',
               existing_type=sa.Integer(),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        batch_op.alter_column('birim_fiyat',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        batch_op.alter_column('miktar',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)

    # Satış Faturalari
    with op.batch_alter_table('satis_faturalari', schema=None) as batch_op:
        batch_op.drop_constraint('check_satis_genel_toplam', type_='check')
        batch_op.drop_constraint('check_satis_indirim_toplam', type_='check')
        batch_op.drop_constraint('check_satis_kdv_toplam', type_='check')
        batch_op.drop_constraint('check_satis_ara_toplam', type_='check')
        batch_op.alter_column('genel_toplam',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        batch_op.alter_column('indirim_toplam',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        batch_op.alter_column('kdv_toplam',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        batch_op.alter_column('ara_toplam',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        op.drop_index('ix_satis_faturalari_fatura_no', table_name='satis_faturalari')
    
    op.drop_column('satis_faturalari', 'silinme_tarihi')

    # Alış Fatura Kalemleri
    with op.batch_alter_table('alis_fatura_kalemleri', schema=None) as batch_op:
        batch_op.drop_constraint('check_alis_kalem_indirim', type_='check')
        batch_op.drop_constraint('check_alis_kalem_kdv', type_='check')
        batch_op.drop_constraint('check_alis_kalem_fiyat', type_='check')
        batch_op.drop_constraint('check_alis_kalem_miktar', type_='check')
        batch_op.alter_column('indirim_orani',
               existing_type=sa.Integer(),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        batch_op.alter_column('birim_fiyat',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        batch_op.alter_column('miktar',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)

    # Alış Faturalari
    with op.batch_alter_table('alis_faturalari', schema=None) as batch_op:
        batch_op.drop_constraint('check_alis_genel_toplam', type_='check')
        batch_op.drop_constraint('check_alis_indirim_toplam', type_='check')
        batch_op.drop_constraint('check_alis_kdv_toplam', type_='check')
        batch_op.drop_constraint('check_alis_ara_toplam', type_='check')
        batch_op.alter_column('genel_toplam',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        batch_op.alter_column('indirim_toplam',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        batch_op.alter_column('kdv_toplam',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        batch_op.alter_column('ara_toplam',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        op.drop_index('ix_alis_faturalari_fatura_no', table_name='alis_faturalari')
    
    op.drop_column('alis_faturalari', 'silinme_tarihi')

    # Ürünler
    with op.batch_alter_table('urunler', schema=None) as batch_op:
        batch_op.drop_constraint('check_stok_miktari', type_='check')
        batch_op.drop_constraint('check_satis_fiyat', type_='check')
        batch_op.drop_constraint('check_alis_fiyat', type_='check')
        batch_op.drop_constraint('check_kdv_orani', type_='check')
        batch_op.alter_column('stok_miktari',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        batch_op.alter_column('satis_fiyat',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
        batch_op.alter_column('alis_fiyat',
               existing_type=sa.Numeric(precision=12, scale=2),
               type_=sa.Float(),
               existing_nullable=False,
               nullable=True)
    
    op.drop_column('urunler', 'silinme_tarihi')
    op.drop_column('musteriler', 'silinme_tarihi')

    # Audit Logs tabla silme
    op.drop_index(op.f('ix_audit_logs_olusturma_tarihi'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_kayit_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_tablo_adi'), table_name='audit_logs')
    op.drop_table('audit_logs')
