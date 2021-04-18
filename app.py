from flask import Flask, request, redirect
from pg import save_zip, save_phone, save_watching, save_unwatch, save_unwatch_all
from twilio.twiml.messaging_response import MessagingResponse

TWILIO_ERROR_MESSAGE = 'I don\'t understand. Please pass a 5-digit zipcode followed by "watch" (to receive notifications for a zip code) or "unwatch" (to stop receiving notifications for a zip code). You may also type "RESET" to unsubscribe to all zip codes'

app = Flask(__name__)

@app.route('/')
def main():
    return '''<div>
        <p>This is an app for getting text updates when vaccine appointments become available in a zip code that you care about. Text <a href="sms:+12027937890">(202) 793-7890</a> with:</p>
        <ul>
            <li><strong><em><5-digit zip code></em> watch</strong> to start receiving notifications for a zip code. E.g., <code>22203 watch</code></li>
            <li><strong><em><5-digit zip code></em> unwatch</strong> to stop receiving notifications for a zip code. E.g., <code>22203 unwatch</code></li>
            <li><strong>RESET</strong> to stop receiving notifications for any zip code</li>
        </ul>
    </div>
'''

@app.route('/sms', methods=['GET', 'POST'])
def sms():
    body = request.values.get('Body', None).lower()
    phone = request.values.get('From', None)
    resp = MessagingResponse()

    if body == 'reset':
        save_unwatch_all(phone)
        resp.message('YOu will no longer receive updates for any zip code')
        return str(resp)

    command = body.split(' ')

    if len(command) != 2:
        resp.message(TWILIO_ERROR_MESSAGE)
        return str(resp)
    
    zip = command[0]
    task = command[1]

    if len(zip) != 5 or not (task == 'watch' or task == 'unwatch'):
        resp.message(TWILIO_ERROR_MESSAGE)
        return str(resp)
    if task == 'watch':
        save_zip(zip)
        save_phone(phone)
        save_watching(zip, phone)
        resp.message(f'Great, you will now receive an update (at most once per hour) when {zip} has available appointments')
    else:
        save_unwatch(zip, phone)
        resp.message(f'You will no longer receive updates for {zip}')
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)