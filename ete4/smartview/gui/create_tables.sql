-- Run this file to (re)create all the tables needed for the backend.

drop table if exists users;
create table users (
    id integer primary key autoincrement,
    username text unique,
    name text not null,
    password text not null);

drop table if exists trees;
create table trees (
    id integer primary key autoincrement,
    name text unique not null,
    description text,
    birth datetime,
    newick text);

drop table if exists user_owns_trees;
create table user_owns_trees (
    id_user integer,
    id_tree integer unique);

drop table if exists user_reads_trees;
create table user_reads_trees (
    id_user integer,
    id_tree integer);
