from datetime import datetime
from decouple import config
from fetch import get_rows
import requests, json, time

AIRTABLE_API_KEY = config('AIRTABLE_API_KEY')

headers = {
    'Authorization': f'Bearer {AIRTABLE_API_KEY}',
    'Content-Type': 'application/json',
}

def fetch_zips():
    req = requests.get('https://api.airtable.com/v0/appRsYQLVLVLkfRJ3/Zips?view=Grid%20view', headers=headers)
    return [r['fields']['Zip'] for r in json.loads(req.text)['records']]

def fetch_rows():
    req = requests.get('https://api.airtable.com/v0/appRsYQLVLVLkfRJ3/Records?view=Grid%20view', headers=headers)
    return json.loads(req.text)['records']

def save_rows(zip, rows, existing):
    records = [{ 'fields': {
            'Unique Id': r['unique_id'],
            'Zip': zip,
            'Address': r['address'],
            'Active': r['active'],
            'Distance': r['distance_miles'],
            'Book Link': r['book_href'],
            'Source': r['source'],
            'Date Added': datetime.now().isoformat()
        }} for r in rows]

    # get new records to add
    existing_unique_ids = [e['fields']['Unique Id'] for e in existing]

    new = [r for r in records if r['fields']['Unique Id'] not in existing_unique_ids]
    data = '{ "records": %s }' % json.dumps(new)
    
    # save new records
    print(f'saving {len(new)} new records...')
    requests.post('https://api.airtable.com/v0/appRsYQLVLVLkfRJ3/Records', 
        headers=headers, 
        data=data,
        params=[('filterByFormula', f'Zip = {zip}')])
   
    # get existing records to update
    updates = []
    for unique_id in existing_unique_ids:
        updated = next((r for r in records if r['fields']['Unique Id'] == unique_id), None)

        if (updated == None):
            continue

        old = next(e for e in existing if e['fields']['Unique Id'] == unique_id)

        for key in updated['fields']:
            if key == 'Active' or key == 'Date Added':
                continue
            if updated['fields'][key] != old['fields'][key]:
                updates.append({
                    'id': old['id'],
                    'fields': updated['fields']
                })
                break
    
    if len(updates) > 0:
        data = '{ "records": %s }' % json.dumps(updates) 
        
        # save updated records
        print(f'updating {len(updates)} existing records...')
        requests.patch('https://api.airtable.com/v0/appRsYQLVLVLkfRJ3/Records', headers=headers, data=data)
    
    return len(new) + len(updates)

def save_summary(rows_edited):
    data = '{ "records": %s }' % json.dumps([{ 
        'fields': { 
            'Count': rows_edited, 
            'Date Added': datetime.now().isoformat() 
        }
    }])
    
    requests.post('https://api.airtable.com/v0/appRsYQLVLVLkfRJ3/Summary', headers=headers, data=data)

if __name__ == '__main__':
    zips = fetch_zips()
    rows_edited = 0

    for zip in zips:
        relevant_rows = get_rows(zip)
        existing = fetch_rows()

        print(f'Found {len(relevant_rows)} records for {zip}')    
        
        if len(relevant_rows) > 0:
            rows_edited += save_rows(zip, relevant_rows, existing)
            time.sleep(1)
    
    if rows_edited > 0:
        print('Rows updated. Triggering summary...')
        save_summary(rows_edited)

