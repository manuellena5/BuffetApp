-- Supabase/Postgres schema for BuffetApp (cajas + detalle + catálogo mínimo)
-- Ejecutar en Supabase SQL editor, o via script de bootstrap.

-- Extensiones útiles
create extension if not exists "pgcrypto";

-- Catálogo: categorías
create table if not exists public.categorias (
  id bigserial primary key,
  descripcion text not null unique
);

-- Catálogo: productos (min set compatible con app)
create table if not exists public.products (
  id bigserial primary key,
  codigo_producto text not null unique,
  nombre text not null,
  precio_venta numeric(12,2) not null default 0,
  stock_actual integer not null default 0,
  contabiliza_stock boolean not null default true,
  visible boolean not null default true,
  categoria_id bigint references public.categorias(id) on delete set null,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);
create index if not exists idx_products_visible on public.products(visible);

-- Cabecera de cajas cerradas en la nube
create table if not exists public.cajas (
  uuid uuid primary key default gen_random_uuid(),
  caja_local_id bigint,
  codigo_caja text,
  fecha_apertura timestamptz,
  fecha_cierre timestamptz,
  usuario_apertura text,
  usuario_cierre text,
  cajero_apertura text,
  cajero_cierre text,
  fondo_inicial numeric(12,2),
  total_ventas numeric(12,2),
  total_efectivo_teorico numeric(12,2),
  conteo_efectivo_final numeric(12,2),
  transferencias_final numeric(12,2),
  ingresos numeric(12,2),
  retiros numeric(12,2),
  diferencia numeric(12,2),
  total_tickets bigint,
  observaciones_apertura text,
  obs_cierre text,
  descripcion_evento text,
  disciplina text,
  dispositivo text,
  enviado_en timestamptz
);
create index if not exists idx_cajas_fecha on public.cajas(fecha_apertura, fecha_cierre);

-- Detalle de caja: items/tickets agregados
create table if not exists public.caja_items (
  id bigserial primary key,
  caja_uuid uuid not null references public.cajas(uuid) on delete cascade,
  ticket_id bigint,
  fecha timestamptz,
  producto_id bigint,
  producto_nombre text,
  categoria text,
  cantidad integer,
  precio_unitario numeric(12,2),
  total numeric(12,2),
  metodo_pago text
);
create index if not exists idx_caja_items_uuid on public.caja_items(caja_uuid);

-- Notas RLS: mantener desactivado inicialmente para pruebas.
-- Luego activar y crear políticas por API Key/tenant si es necesario.
