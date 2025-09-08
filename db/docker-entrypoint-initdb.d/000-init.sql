CREATE USER akvo WITH CREATEDB PASSWORD 'password';

CREATE DATABASE kb_mcp
WITH OWNER = kb_mcp_server
     TEMPLATE = template0
     ENCODING = 'UTF8'
     LC_COLLATE = 'en_US.UTF-8'
     LC_CTYPE = 'en_US.UTF-8';

CREATE DATABASE kb_mcp_test
WITH OWNER = kb_mcp_server
     TEMPLATE = template0
     ENCODING = 'UTF8'
     LC_COLLATE = 'en_US.UTF-8'
     LC_CTYPE = 'en_US.UTF-8';
