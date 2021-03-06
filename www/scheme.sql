drop database if exists wtf;
create database wtf
use wtf
grant select,insert,update,delete on wtf.* to'wolfgang'@'localhost'identified by 'asdzxc753159';

create table user(
		'id'varchar(50)not null,
		'name'varchar(50)not null,
		'email'varchar(50) not null,
		'password'varchar(50)not null,
		'admin'bool not null,
		'name'varchar(50)not null,
		'image'varchar(500)not null,
		'create_at'real not null,
		unique key 'idx_email'('email'),
		key 'idx_create_at'('create_at'),
		primary key ('id')
		)engine=innodb default charset=utf-8;

create table blog(
		'id'varchar(50)not null,
		'user_id'varchar(50)not null,
		'user_name'varchar(50) not null,
		'user_image'varchar(500)not null,
		'title'varchar(50)not null,
		'summary'varchar(200)not null,
		'content'mediumtext not null,
		'create_at'real not null,
		key 'idx_create_at'('create_at'),
		primary key ('id')
		)engine=innodb default charset=utf-8;

create table comment(
		'id'varchar(50)not null,
		'user_id'varchar(50)not null,
		'blog_id'varchar(50) not null,
		'user_name'varchar(50)not null,
		'user_image'varchar(500)not null,
		'content'mediumtext not null,
		'create_at'real not null,
		key 'idx_create_at'('create_at'),
		primary key ('id')
		)engine=innodb default charset=utf-8;