USE ROLE ACCOUNTADMIN;
CREATE WAREHOUSE IF NOT EXISTS <% SNOWFLAKE_WAREHOUSE %>  WAREHOUSE_SIZE = SMALL;
USE WAREHOUSE <% SNOWFLAKE_WAREHOUSE %>;

-- Create Role and Grant Ownership

CREATE ROLE IF NOT EXISTS <% SNOWFLAKE_ROLE %>;

-- ability to execute tasks
GRANT EXECUTE TASK ON ACCOUNT TO ROLE <% SNOWFLAKE_ROLE %>;
GRANT ROLE <% SNOWFLAKE_ROLE %> TO USER <% SNOWFLAKE_USER %>;
GRANT USAGE ON WAREHOUSE <% SNOWFLAKE_WAREHOUSE %> TO ROLE <% SNOWFLAKE_ROLE %>;

-- Demo Database and Schemas

CREATE DATABASE IF NOT EXISTS <% SNOWFLAKE_DATABASE %>
  COMMENT = 'Snowflake Cortex Agents MCP Demo Database';

GRANT OWNERSHIP ON DATABASE <% SNOWFLAKE_DATABASE %> TO ROLE <% SNOWFLAKE_ROLE %>;

USE ROLE <% SNOWFLAKE_ROLE %>;

USE DATABASE <% SNOWFLAKE_DATABASE %> ;

CREATE SCHEMA IF NOT EXISTS DATA;
CREATE SCHEMA IF NOT EXISTS MY_MODELS;

CREATE SCHEMA IF NOT EXISTS NETWORKS;
CREATE SCHEMA IF NOT EXISTS POLICIES;

USE <% SNOWFLAKE_DATABASE %>.DATA;
CREATE OR REPLACE STAGE DOCS
  encryption = (TYPE = 'SNOWFLAKE_SSE') directory = ( ENABLE = true );

-- streams to track changes in the documents stage
CREATE OR REPLACE STREAM invoices_insert_docs_stream ON STAGE docs;
CREATE OR REPLACE STREAM invoices_delete_docs_stream ON STAGE docs;

CREATE OR REPLACE STAGE MY_MODELS
  encryption = (TYPE = 'SNOWFLAKE_SSE')
  directory = ( ENABLE = true )
  comment = 'Stage for storing semantic models';

PUT file://<%DATA_DIR%>/support_tickets.yaml @MY_MODELS AUTO_COMPRESS = FALSE;

ALTER STAGE MY_MODELS refresh;

CREATE OR REPLACE FILE FORMAT CSVFORMAT
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  TYPE = 'CSV';

-- SUPPORT_TICKETS
CREATE OR REPLACE STAGE SUPPORT_TICKETS_DATA_STAGE
  FILE_FORMAT = CSVFORMAT
  URL = 's3://sfquickstarts/finetuning_llm_using_snowflake_cortex_ai/';

CREATE TABLE IF NOT EXISTS SUPPORT_TICKETS (
  TICKET_ID VARCHAR(60),
  CUSTOMER_NAME VARCHAR(60),
  CUSTOMER_EMAIL VARCHAR(60),
  SERVICE_TYPE VARCHAR(60),
  REQUEST VARCHAR,
  CONTACT_PREFERENCE VARCHAR(60)
);

COPY INTO SUPPORT_TICKETS
  FROM @SUPPORT_TICKETS_DATA_STAGE;


-- Table to hold the chunks of the documents
CREATE TABLE IF NOT EXISTS  <% SNOWFLAKE_DATABASE %>.data.CHUNKED_INVOICE_CONTENT (
        file_name VARCHAR,
        CHUNK VARCHAR
    );

-- Create Search Service
CREATE OR REPLACE CORTEX SEARCH SERVICE <% SNOWFLAKE_DATABASE %>.data.INVOICE_SEARCH_SERVICE
    ON chunk
    WAREHOUSE = <% SNOWFLAKE_WAREHOUSE %>
    TARGET_LAG = '1 MINUTE' -- change it higher value , this good for demo purposes
    EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
    AS (
    SELECT
        file_name,
        chunk
    FROM <% SNOWFLAKE_DATABASE %>.data.CHUNKED_INVOICE_CONTENT
    );

-- Stored Procedure to extract and chunk the documents
CREATE OR REPLACE PROCEDURE <% SNOWFLAKE_DATABASE %>.data.SYNC_DOC_CHUNKS()
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
BEGIN
    DELETE FROM CHUNKED_INVOICE_CONTENT
    USING invoices_delete_docs_stream
    WHERE
       CHUNKED_INVOICE_CONTENT.FILE_NAME = invoices_delete_docs_stream.RELATIVE_PATH
    AND
      invoices_delete_docs_stream.METADATA$ACTION = 'DELETE';

    CREATE OR REPLACE TEMPORARY TABLE PARSED_INVOICES_CONTENT AS SELECT
        relative_path,
        TO_VARCHAR(
            SNOWFLAKE.CORTEX.PARSE_DOCUMENT(
            '@docs',
            relative_path,
            {'mode': 'LAYOUT'}
            ) :content
        ) AS parsed_text
        FROM
          invoices_insert_docs_stream
        WHERE
           METADATA$ACTION = 'INSERT';

    -- Chunk and insert data

    INSERT INTO CHUNKED_INVOICE_CONTENT (file_name, CHUNK)
    SELECT
        relative_path,
        c.value AS CHUNK
    FROM
       PARSED_INVOICES_CONTENT,
        LATERAL FLATTEN( input => SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER (
            parsed_text,
            'markdown',
            1800,
            250
        )) c;

    RETURN (SELECT COUNT(*) FROM CHUNKED_INVOICE_CONTENT) || ' documents chunked successfully.';
END;
$$;

-- Schedule it
CREATE OR REPLACE TASK <% SNOWFLAKE_DATABASE %>.data.SYNC_DOCS
    WAREHOUSE = <% SNOWFLAKE_WAREHOUSE %>
    SCHEDULE = '1 MINUTE' -- change it higher value , this good for demo purposes
WHEN
    SYSTEM$STREAM_HAS_DATA('<% SNOWFLAKE_DATABASE %>.data.invoices_insert_docs_stream')
AS
    CALL <% SNOWFLAKE_DATABASE %>.data.SYNC_DOC_CHUNKS();

-- Resume the task
ALTER TASK  <% SNOWFLAKE_DATABASE %>.data.SYNC_DOCS resume;
