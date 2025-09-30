-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.category (
  kategori_id integer NOT NULL DEFAULT nextval('category_kategori_id_seq'::regclass),
  nama text NOT NULL UNIQUE,
  label text NOT NULL UNIQUE,
  CONSTRAINT category_pkey PRIMARY KEY (kategori_id)
);
CREATE TABLE public.custom_users (
  user_id uuid NOT NULL DEFAULT gen_random_uuid(),
  name text,
  email text NOT NULL UNIQUE,
  password text NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  CONSTRAINT custom_users_pkey PRIMARY KEY (user_id)
);
CREATE TABLE public.destinasi (
  destinasi_id integer NOT NULL DEFAULT nextval('destinasi_destinasi_id_seq'::regclass),
  nama_destinasi text NOT NULL,
  kategori_id integer NOT NULL,
  deskripsi text,
  image_url text,
  full_deskripsi text,
  CONSTRAINT destinasi_pkey PRIMARY KEY (destinasi_id),
  CONSTRAINT destinasi_kategori_id_fkey FOREIGN KEY (kategori_id) REFERENCES public.category(kategori_id)
);
CREATE TABLE public.preference (
  user_id uuid NOT NULL,
  kategori_id integer NOT NULL,
  weight real NOT NULL DEFAULT 1.0,
  CONSTRAINT preference_pkey PRIMARY KEY (user_id, kategori_id),
  CONSTRAINT test_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.custom_users(user_id),
  CONSTRAINT test_kategori_id_fkey FOREIGN KEY (kategori_id) REFERENCES public.category(kategori_id)
);
CREATE TABLE public.ratings (
  rating_id bigint NOT NULL DEFAULT nextval('ratings_rating_id_seq'::regclass),
  user_id uuid NOT NULL,
  destinasi_id integer NOT NULL,
  rating smallint NOT NULL CHECK (rating >= 1 AND rating <= 5),
  created_at timestamp with time zone DEFAULT now(),
  review text,
  CONSTRAINT ratings_pkey PRIMARY KEY (rating_id),
  CONSTRAINT ratings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.custom_users(user_id),
  CONSTRAINT ratings_destinasi_id_fkey FOREIGN KEY (destinasi_id) REFERENCES public.destinasi(destinasi_id)
);