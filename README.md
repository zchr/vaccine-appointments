# Vaccine Watcher
## What
There are [some](https://www.getmyvaccine.org/) [phenomenal](https://www.findashot.org/) [websites](https://www.vaccinespotter.org/) to help find Covid vaccine appointments in the U.S. After destroying my `Cmd-r` keys, I thought it would be great if I could subscribe to some zip codes and then get an email digest if any vaccine appointments were newly available.

## Thank you
This only works because of the hard work by the team at [GetMyVaccine.org](https://www.getmyvaccine.org). If you can, go [buy them a coffee](https://www.buymeacoffee.com/getmyvaccine)!
### Help others
Vaccine searching is intimidating, complicated, and impossible for many. Please consider volunteering to [help others book an appointment](https://vaccinefairy.org/). 

## What you'll need
 * Ability to pivot quickly to address operationally-prioritized tasks
 * Demonstrated expertise with Cassandra, Kafka, and a third thing
 * Experience converting from monolithic to microservices and then back to monolithic

Okay not really. This setup does require a couple of (free) accounts, though:
 * [Airtable](https://airtable.com/): Used for saving all of our data and sending email alerts
 * [Heroku](https://heroku.com/): Used to deploy & run the python script

## Setting up
### Airtable
Airtable made it easy to keep track of vaccine locations and send email notifications. 
#### 1. Copy the template
After you've signed up for an Airtable account, make a copy of [this](https://airtable.com/shrJGocdUO4wiY9ci) template (there's a `Copy` button on the top right). You'll see three different tables:
* `Records`: This is where we store location-level information
  * The default view (`Grid view`) has data on all locations that we have ever collected
  * The view `Recently Updated` filters down to locations where an appointment was available within the past 10 minutes
* `Summary`: We add a row to this table anytime one (or many) of our zip codes have a new vaccination appointment nearby, and it will trigger an email
* `Zips`: A single column where you put the zip codes that you are interested in tracking

Once you've made a copy, delete the rows in each table.

#### 2. Set up email alerts
We can use Airtable Automations to send an email whenever we have updated vaccine availability. 
 * In the Automations tab, click "Create a custom automation"
 * For "trigger", choose "When a record enters a view"
   * Table: `Summary`
   * View: `Grid view`
 * Add the action "Find records", which is where we'll filter down to only recently-updated appointment information 
   * Table: `Records`
   * Conditions: `Where Last Updated <= 5` (this translates to "Only email me about vaccine appointments updated within the last 5 minutes")
  * Add a second action "Send an email"
    * To: Your email
    * Subject: "New vaccination information!"
    * Message: Click the `+` to choose the Records from Step 2, and render them as an HTML grid

### Heroku
#### 1. Deploy
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)
#### 2. Update environment variables
 * `AIRTABLE_API_KEY`: You can find this on your [Airtable account page](https://airtable.com/account)
 * `VACCINE_MAX_MILES`: Max number of miles you want to consider from each zip code you're tracking (defaults to `40` miles)
 * `VACCINE_MAX_MINUTES`: Max number of minutes before you'll consider appointment information "out-dated" (defaults to `5` minutes)

#### 3. Set up a cron job
There are a couple add-ons I considered:
 * [Heroku Scheduler](https://devcenter.heroku.com/articles/scheduler): Free, but the most frequent it will run a job is every 10 minutes
 * [Cron To Go](https://elements.heroku.com/addons/crontogo): Free trial (7 days), way more flexible and very precise

Whichever add-on you choose, set it up to run the command `python3 vaccine.py`. I set mine up to run every 5 minutes.


 





 
  