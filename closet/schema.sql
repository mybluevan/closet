PRAGMA foreign_keys = ON;
drop table if exists categories;
create table categories (
  id integer primary key autoincrement,
  parent integer references categories,
  slug text not null unique,
  name text not null,
  picture text
);
create index parentindex on categories(parent);
drop table if exists colours;
create table colours (
  id integer primary key autoincrement,
  name text not null,
  code text not null
);
drop table if exists brands;
create table brands (
  id integer primary key autoincrement,
  name text not null,
  logo text
);
drop table if exists styles;
create table styles (
  id integer primary key autoincrement,
  name text not null,
  picture text
);
drop table if exists attributes;
create table attributes (
  id integer primary key autoincrement,
  name text not null
);
drop table if exists garments;
create table garments (
  id integer primary key autoincrement,
  category text references categories not null,
  brand integer references brands,
  style integer references styles,
  primarycolour integer references colours,
  secondarycolour integer references colours,
  description text,
  picture text
);
create index garmentindex on garments(category, brand, style, primarycolour);
create index secondarycolourindex on garments(secondarycolour) where secondarycolour is not null;
drop table if exists garment_attributes;
create table garment_attributes (
  garment integer references garments not null,
  attr integer references attributes not null,
  primary key (garment, attr)
);
