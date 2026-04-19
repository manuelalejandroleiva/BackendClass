"""add rents tables

Revision ID: 05_add_rentas
Revises: 45bc09c0693e
Create Date: 2026-04-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '05_add_rentas'
down_revision: Union[str, Sequence[str], None] = '45bc09c0693e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('vehicles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plate', sa.String(), nullable=False),
        sa.Column('brand', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('vin', sa.String(), nullable=True),
        sa.Column('device_id', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('AVAILABLE', 'RENTED', 'MAINTENANCE', 'INACTIVE', name='vehiclestatus'), nullable=False),
        sa.Column('current_latitude', sa.Float(), nullable=True),
        sa.Column('current_longitude', sa.Float(), nullable=True),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('battery_level', sa.Float(), nullable=True),
        sa.Column('last_update', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicles_id'), 'vehicles', ['id'], unique=False)
    op.create_index(op.f('ix_vehicles_plate'), 'vehicles', ['plate'], unique=True)
    op.create_index(op.f('ix_vehicles_device_id'), 'vehicles', ['device_id'], unique=False)
    op.create_index(op.f('ix_vehicles_status'), 'vehicles', ['status'], unique=False)

    op.create_table('gps_locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('altitude', sa.Float(), nullable=True),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('heading', sa.Float(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gps_locations_id'), 'gps_locations', ['id'], unique=False)
    op.create_index(op.f('ix_gps_locations_vehicle_id'), 'gps_locations', ['vehicle_id'], unique=False)
    op.create_index(op.f('ix_gps_locations_timestamp'), 'gps_locations', ['timestamp'], unique=False)

    op.create_table('rentals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('start_latitude', sa.Float(), nullable=False),
        sa.Column('start_longitude', sa.Float(), nullable=False),
        sa.Column('end_latitude', sa.Float(), nullable=True),
        sa.Column('end_longitude', sa.Float(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('total_distance', sa.Float(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'COMPLETED', 'CANCELLED', name='rentalstatus'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rentals_id'), 'rentals', ['id'], unique=False)
    op.create_index(op.f('ix_rentals_vehicle_id'), 'rentals', ['vehicle_id'], unique=False)
    op.create_index(op.f('ix_rentals_user_id'), 'rentals', ['user_id'], unique=False)

    op.create_table('geofences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('center_latitude', sa.Float(), nullable=False),
        sa.Column('center_longitude', sa.Float(), nullable=False),
        sa.Column('radius_meters', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('alert_on_entry', sa.Boolean(), nullable=True),
        sa.Column('alert_on_exit', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_geofences_id'), 'geofences', ['id'], unique=False)
    op.create_index(op.f('ix_geofences_vehicle_id'), 'geofences', ['vehicle_id'], unique=False)

    op.create_table('geofence_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('geofence_id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.Enum('GEOFENCE_ENTRY', 'GEOFENCE_EXIT', 'SPEED_LIMIT', 'LOW_BATTERY', name='alerttype'), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['geofence_id'], ['geofences.id'], ),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_geofence_alerts_id'), 'geofence_alerts', ['id'], unique=False)
    op.create_index(op.f('ix_geofence_alerts_geofence_id'), 'geofence_alerts', ['geofence_id'], unique=False)
    op.create_index(op.f('ix_geofence_alerts_vehicle_id'), 'geofence_alerts', ['vehicle_id'], unique=False)
    op.create_index(op.f('ix_geofence_alerts_timestamp'), 'geofence_alerts', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_geofence_alerts_timestamp'), table_name='geofence_alerts')
    op.drop_index(op.f('ix_geofence_alerts_vehicle_id'), table_name='geofence_alerts')
    op.drop_index(op.f('ix_geofence_alerts_geofence_id'), table_name='geofence_alerts')
    op.drop_index(op.f('ix_geofence_alerts_id'), table_name='geofence_alerts')
    op.drop_table('geofence_alerts')
    op.drop_index(op.f('ix_geofences_vehicle_id'), table_name='geofences')
    op.drop_index(op.f('ix_geofences_id'), table_name='geofences')
    op.drop_table('geofences')
    op.drop_index(op.f('ix_rentals_user_id'), table_name='rentals')
    op.drop_index(op.f('ix_rentals_vehicle_id'), table_name='rentals')
    op.drop_index(op.f('ix_rentals_id'), table_name='rentals')
    op.drop_table('rentals')
    op.drop_index(op.f('ix_gps_locations_timestamp'), table_name='gps_locations')
    op.drop_index(op.f('ix_gps_locations_vehicle_id'), table_name='gps_locations')
    op.drop_index(op.f('ix_gps_locations_id'), table_name='gps_locations')
    op.drop_table('gps_locations')
    op.drop_index(op.f('ix_vehicles_status'), table_name='vehicles')
    op.drop_index(op.f('ix_vehicles_device_id'), table_name='vehicles')
    op.drop_index(op.f('ix_vehicles_plate'), table_name='vehicles')
    op.drop_index(op.f('ix_vehicles_id'), table_name='vehicles')
    op.drop_table('vehicles')