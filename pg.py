from fetch import get_rows
import time, psycopg2, os

conn = psycopg2.connect(
    host="localhost",
    database="vaccines",
    user="postgres",
    password="")

def migrate():
    write('CREATE TABLE IF NOT EXISTS scripts (script_name TEXT NOT NULL, date_ran TIMESTAMPTZ NOT NULL)')
    run_scripts = [i[0] for i in read('SELECT script_name FROM scripts')]
    
    scripts = os.listdir('./sql/')
    for script in scripts:
        if script in run_scripts:
            continue
        with open(f'./sql/{script}') as f:
            write(f.read())
            write(f'INSERT INTO scripts (script_name, date_ran) VALUES (\'{script}\', NOW())')

def read_singles(str):
    res = read(str)
    return [r[0] for r in res]

def read(str):
    cur = conn.cursor()
    cur.execute(str)
    res = cur.fetchall()
    cur.close()

    return res

def write(str):
    cur = conn.cursor()
    cur.execute(str)
    cur.close()

def fetch_zips():
    return read_singles('SELECT zip_code FROM zip_codes')   

def save_zip(zip):
    write(f"""
            DO
            $do$
            BEGIN   
            IF NOT EXISTS (SELECT * FROM zip_codes WHERE zip_code = '{zip}')
            THEN
                INSERT INTO zip_codes (zip_code)
                SELECT '{zip}';
            END IF;
            END;
            $do$
        """)  
    
def save_rows(zip, rows): 
    # save new records
    print(f'saving {len(rows)} records...')
    
    for r in rows:
        write(f"""
            INSERT INTO distances (place_id
                ,zip_code
                ,address1
                ,distance
                ,link 
                ,source
                ,date_updated)
            SELECT '{r['unique_id']}'
                ,z.id
                ,'{r['address']}'
                ,'{r['distance_miles']}'
                ,'{r['book_href']}'
                ,'{r['source']}'
                ,NOW()
            FROM zip_codes z
            WHERE z.zip_code = '{zip}'
            ON CONFLICT ON CONSTRAINT uq_distances_place_id DO UPDATE 
                SET  date_updated = NOW();
        """)          

if __name__ == '__main__':
    try:
        migrate()

        zips = fetch_zips()

        for zip in zips:
            save_zip(zip)
            relevant_rows = get_rows(zip)
            print(f'Found {len(relevant_rows)} records for {zip}')    
            
            if len(relevant_rows) > 0:
                save_rows(zip, relevant_rows)
                time.sleep(1)
    except Exception as e:
        print('## Error hit: ')
        print(e)
    finally:
        conn.commit()
        conn.close()

