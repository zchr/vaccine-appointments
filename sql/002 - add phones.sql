CREATE TABLE phones (
     id SERIAL
    ,phone VARCHAR(12)
    ,date_added TIMESTAMPTZ
    ,PRIMARY KEY(id)
);

CREATE TABLE watching (
     id SERIAL
    ,zip_code_id INT NOT NULL 
    ,phone_id INT NOT NULL
    ,date_updated TIMESTAMPTZ NOT NULL
    ,PRIMARY KEY(id)
    ,CONSTRAINT fk_watching_zip_codes
      FOREIGN KEY(zip_code_id) 
	  REFERENCES zip_codes(id)
    ,CONSTRAINT fk_watching_phones
      FOREIGN KEY(phone_id) 
	  REFERENCES phones(id)
);