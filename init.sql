create table businessroles (
role_id serial primary key,
role_title varchar(60)
);

create table users (
user_id serial primary key,
user_name varchar(18) unique,
user_password varchar(60),
business_role bigint references businessroles(role_id),
created_at date default current_date
);

create table skills (
skill_id serial primary key,
title varchar(100) unique,
skill_role bigint references businessroles(role_id)
);

create table userskills (
skill_id bigint references skills(skill_id),
user_id bigint references users(user_id)
);

create table vacancies (
vacancy_id serial primary key,
title text,
employer text,
experience text,
url text
);

create table vacancyskills (
vacancy_id bigint references vacancies(vacancy_id),
skill_id bigint references skills(skill_id)
);

insert into businessroles (role_title) values ('unsorted');