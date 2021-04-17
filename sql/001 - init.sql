CREATE TABLE zip_codes (
     id SERIAL
    ,zip_code VARCHAR(5)
);

CREATE TABLE distances (
     id SERIAL
    ,place_id TEXT 
    ,zip_code INT NOT NULL
    ,address1 TEXT
    ,distance FLOAT
    ,link TEXT
    ,source TEXT
    ,date_updated TIMESTAMP
    ,CONSTRAINT uq_distances_place_id UNIQUE (place_id)
);