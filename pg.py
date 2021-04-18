from fetch import get_rows
import time, psycopg2, os
from decouple import config
from twilio.rest import Client

TWILIO_SID = config('TWILIO_SID')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN')

conn = psycopg2.connect(
    host="localhost",
    database="vaccines",
    user="postgres",
    password="")

def send_text(phone, message):
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

    message = client.messages.create(
        to=phone, 
        from_="+12027937890",
        body=message)

def migrate():
    write('CREATE TABLE IF NOT EXISTS scripts (script_name TEXT NOT NULL, date_ran TIMESTAMPTZ NOT NULL)')
    run_scripts = read_singles('SELECT script_name FROM scripts')
    
    scripts = os.listdir('./sql/')
    for script in scripts:
        if script in run_scripts:
            continue
        with open(f'./sql/{script}') as f:
            write(f.read())
            write(f'INSERT INTO scripts (script_name, date_ran) VALUES (\'{script}\', NOW())')

def read_singles(str, args=()):
    res = read(str, args)
    return [r[0] for r in res]

def read(str, args):
    cur = conn.cursor()
    cur.execute(str, args)
    res = cur.fetchall()
    cur.close()

    return res

def write(str, args=()):
    cur = conn.cursor()
    cur.execute(str, args)
    cur.close()
    conn.commit()

def fetch_zips():
    return read_singles('SELECT zip_code FROM zip_codes')   

def save_watching(zip, phone):
    write(f"""
        DO
        $do$
        BEGIN   
        IF NOT EXISTS ( SELECT * 
                        FROM watching w  
                        JOIN phones p
                            ON w.phone_id = p.id
                            AND p.phone = '{phone}'
                        JOIN zip_codes z 
                            ON w.zip_code_id = z.id
                            AND z.zip_code = '{zip}')
        THEN
            INSERT INTO watching (phone_id, zip_code_id)
            SELECT p.id, z.id
            FROM phones p
            JOIN zip_codes z
                ON z.zip_code = '{zip}'
            WHERE p.phone = '{phone}';
        END IF;
        END;
        $do$
    """)  

def save_unwatch(zip, phone):
    write('''
        DELETE FROM watching
        WHERE phone_id = (SELECT id FROM phones WHERE phone = %s)
            AND zip_code_id = (SELECT id FROM zip_codes WHERE zip_code = %s)
    ''', (phone, zip))

def save_unwatch_all(phone):
        write('''
        DELETE FROM watching
        WHERE phone_id = (SELECT id FROM phones WHERE phone = %s)
    ''', (phone))

def save_phone(phone):
    write(f"""
        DO
        $do$
        BEGIN   
        IF NOT EXISTS (SELECT * FROM phones WHERE phone = '{phone}')
        THEN
            INSERT INTO phones (phone)
            SELECT '{phone}';
        END IF;
        END;
        $do$
    """)  

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

def get_phones_to_notify(zips):
    return read('''
        SELECT p.phone, STRING_AGG(z.zip_code, ',' ORDER BY z.zip_code) zip_codes
        FROM phones p
        JOIN watching w
            ON p.id = w.phone_id
            AND ( DATE_PART('day', NOW() - w.date_updated) * 24 
                + DATE_PART('hour', NOW() - w.date_updated ))
                > 1
        JOIN zip_codes z
            ON w.zip_code_id = z.id
            AND z.zip_code = ANY(%s)
        GROUP BY p.phone
    ''', (zips,))

def save_phones_notified(zips):
    write('''
        UPDATE watching AS w
        SET date_updated = NOW()
        FROM phones p
        WHERE p.id = w.phone_id
            AND ( DATE_PART('day', NOW() - w.date_updated) * 24 
                + DATE_PART('hour', NOW() - w.date_updated ))
                > 1
            AND w.zip_code_id IN (SELECT id FROM zip_codes WHERE zip_code = ANY(%s))
    ''', (zips,))

if __name__ == '__main__':
    try:
        migrate()

        zips = fetch_zips()

        zips_to_notify = []
        for zip in zips:
            save_zip(zip)
            relevant_rows = get_rows(zip)
            print(f'Found {len(relevant_rows)} records for {zip}')    
            
            if len(relevant_rows) > 0:
                zips_to_notify.append(zip)
                save_rows(zip, relevant_rows)
                time.sleep(1)
        
        phone_zips = get_phones_to_notify(zips)
        for pz in phone_zips:
            send_text(pz[0], f'The following zip code(s) have new appointments available! Visit https://getmyvaccine.org\n{pz[1]}')
            save_phones_notified(zips)

    except Exception as e:
        print('## Error hit: ')
        print(e)
    finally:
        conn.close()

