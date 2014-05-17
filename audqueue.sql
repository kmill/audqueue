create table song (
 name text not null,
 grouping text,
 composer text,
 artist text,
 album text not null,
 genre text,
 tracknum integer,
 numbertracks integer,
 discnum integer,
 numberdiscs integer,
 filetype text not null,
 filesize integer not null,
 bitrate integer,
 time integer,
 filename text unique,
 modified integer
);
