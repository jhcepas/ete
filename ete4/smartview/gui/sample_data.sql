-- Run this file to add sample values into the database.

insert into users values
    (1, 'admin', 'system administrator',
     'pbkdf2:sha256:50000$713rFBmU$1e10a0e9b5fca0b4550b39dffd01931d8cdc64760d5995856e9c775e94e983dd'),
    (2, 'guest', 'example guest user',
     'pbkdf2:sha256:50000$w4xHhhi8$75b2502e4680383c5fc89423e446b847021b52b086648897b8a6dcba60e771cb'),
    (3, 'guest2', 'other example guest user',
     'pbkdf2:sha256:50000$g2cIiryf$b0da4704216e5128544a831ba293adcc7aae3d730df9464cba5943fdf2b33c92');

-- abc -> pbkdf2:sha256:50000$713rFBmU$1e10a0e9b...
-- 123 -> pbkdf2:sha256:50000$w4xHhhi8$75b2502e4...
-- xyz -> pbkdf2:sha256:50000$g2cIiryf$b0da47042...


insert into trees values
    (1, 'Sample Tree', 'A simple test of a tree', '2021-01-01 00:00:00.000000',
    '(B:2,(C:3,D:4)E:5)A:1;'),
    (2, 'Multinest', 'An empty-looking tree', '2021-01-01 00:00:00.000000',
    '(((((((((,),),),),),),),),);'),
    (3, 'Directories', 'From the filesystem', '2021-01-01 00:00:00.000000',
    '(boot/,dev/,etc/,(user1/,user2/)home/,(bin/,lib/)usr/,var/,tmp/)/;');

insert into user_owns_trees values  -- id_user, id_tree
    (1, 1), (1, 2),
    (2, 3);

insert into user_reads_trees values  -- id_user, id_tree
    (1, 3), (1, 2),
    (3, 1), (3, 2);
