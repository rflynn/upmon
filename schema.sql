
pragma page_size = 4096;

begin;

delete from sqlite_sequence;

drop table if exists metadata;
create table metadata (
    id                      integer primary key autoincrement,
    name                    varchar(64) not null unique,
    value                   varchar(256)
);
insert into metadata (id, name, value)
          select 1, 'v', '0.0.0'
;

drop table if exists http_method;
create table http_method (
    id                      integer primary key autoincrement,
    name                    varchar(32) not null unique
);
insert into http_method (id, name)
          select 1, 'OPTIONS'
union all select 2, 'GET'
union all select 3, 'HEAD'
union all select 4, 'POST'
union all select 5, 'PUT'
union all select 6, 'DELETE'
union all select 7, 'TRACE'
union all select 8, 'CONNECT'
union all select 9, 'PATCH'
;

-- where 
drop table if exists reqloc;
create table reqloc (
    id                      integer primary key autoincrement,
    name                    varchar(64) not null unique
);

drop table if exists http_request;
create table http_request (
    id                      integer primary key autoincrement,
    http_method_id          integer       not null,
    name                    varchar(4096) not null unique,
    foreign key (http_method_id) references http_method (id)
);
insert into http_request (id, http_method_id, name)
          select 1, (select id from http_method where name='GET'), ''
;

drop table if exists [except];
create table [except] (
    id                      integer primary key autoincrement,
    name                    varchar(64) not null unique
);

drop table if exists content_type;
create table content_type (
    id                      integer primary key autoincrement,
    name                    varchar(64) not null unique
);

drop table if exists url;
create table url (
    id                      integer primary key autoincrement,
    scheme                  varchar(32)   not null,
    netloc                  varchar(64)   not null,
    path                    varchar(1024) not null,
    query                   varchar(2048),
    fragment                varchar(256),
    username                varchar(256),
    password                varchar(256),
    hostname                varchar(1024),
    port                    varchar(16),
    unique (scheme, netloc, path, query)
);

drop table if exists sha1;
create table sha1 (
    id                      integer primary key autoincrement,
    name                    blob not null unique
);

drop table if exists result;
create table result (
    id                      integer primary key autoincrement,
    reqloc_id               integer,
    http_request_id         integer not null,
    url_id                  integer not null,
    time_start              integer not null,
    duration_msec           integer not null,
    http_code               smallint,
    except_id               integer,
    content_type_id         integer,
    body_length             integer,
    body_sha1_id            integer,
    foreign key (reqloc_id)       references reqloc       (id),
    foreign key (http_request_id) references http_request (id),
    foreign key (url_id)          references url          (id),
    foreign key (except_id)       references [except]     (id),
    foreign key (content_type_id) references content_type (id),
    foreign key (body_sha1_id)    references sha1         (id)
);

commit;

