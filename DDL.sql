use tutorrep_db;

drop table if exists Materials;
drop table if exists SI_Leaders;
drop table if exists Classes;
drop table if exists Person;

create table Person ( 
    username varchar(8) not null primary key,
    name varchar(50),
    role enum("PLTC Admin","professor","student"),
    INDEX (username)
    )

ENGINE = InnoDB;

create table Classes ( 
    classID int auto_increment not null primary key,
    semester varchar(20),
    department varchar(10),
    classNumber varchar(10),
    className varchar(10),
    section varchar(5),
    INDEX (classID)
    )

ENGINE = InnoDB;

create table SI_Leaders ( 
    username varchar(8),
    classID int,
    foreign key (username) references Person(username) 
        on update restrict 
        on delete restrict,
    foreign key (classID) references Classes(classID) 
        on update restrict 
        on delete restrict
    )

ENGINE = InnoDB;

create table Materials ( 
    mID int auto_increment not null primary key,
    fileName varchar(50),
    classID int,
    week int,
    topic varchar(80),
    kind enum("handout","lesson plan","other","solutions"),
    uploader_id varchar(8),
    foreign key (uploader_id) references Person(username) 
        on update restrict 
        on delete restrict,
    foreign key (classID) references Classes(classID) 
        on update restrict 
        on delete restrict
    )

ENGINE = InnoDB;


load data local infile 'Person.csv' 
into table Person
fields terminated by ','
lines terminated by '\n'
ignore 1 lines;

load data local infile 'classes.csv' 
into table Classes
fields terminated by ','
lines terminated by '\n'
ignore 1 lines;


load data local infile 'SIleaders.csv' 
into table SI_Leaders
fields terminated by ','
lines terminated by '\n'
ignore 1 lines;

load data local infile 'materials.csv' 
into table Materials
fields terminated by ','
lines terminated by '\n'
ignore 1 lines;
