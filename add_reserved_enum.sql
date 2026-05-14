-- Script para agregar 'RESERVED' al enum vehiclestatus
-- Ejecutar con: psql -U postgres -d mlack -f add_reserved_enum.sql

-- Verificar los valores actuales del enum
SELECT enumlabel FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'vehiclestatus')
ORDER BY enumsortorder;

-- Agregar el nuevo valor
ALTER TYPE vehiclestatus ADD VALUE IF NOT EXISTS 'RESERVED';

-- Verificar que se agregó correctamente
SELECT enumlabel FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'vehiclestatus')
ORDER BY enumsortorder;
