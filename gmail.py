from __future__ import print_function
import pickle
import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import requests
import base64
from datetime import datetime
from email.mime.text import MIMEText

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://mail.google.com/', 'https://www.googleapis.com/auth/gmail.modify',
          'https://www.googleapis.com/auth/gmail.compose', 'https://www.googleapis.com/auth/gmail.send']

chase = 'Chase < no-reply@alertsp.chase.com >'


class Date:

    def __init__(self, day, month, year):
        self.month = month
        self.year = year
        self.day = day
        self.calc_month()

    def calc_month(self):
        months_dict = {
            'Jan': 1,
            'Feb': 2,
            'Mar': 3,
            'Apr': 4,
            'May': 5,
            'Jun': 6,
            'Jul': 7,
            'Aug': 8,
            'Sep': 9,
            'Oct': 10,
            'Nov': 11,
            'Dec': 12
        }
        self.month = months_dict[self.month]


class Email:

    def __init__(self, eid, efrom, ebody, date):
        self.eid = eid
        self.efrom = efrom
        self.ebody = ebody
        self.date = date
        self.amount = None
        self.calc_amount()
        self.calc_date()

    def calc_amount(self):
        body = self.ebody.decode("utf-8")
        # Split on USD and pull the index with the dollar value in it
        value_string = body.split("($USD)")[2]
        # Split at whitespace and pull first value for the amount
        self.amount = float(value_string.split()[0])

    def calc_date(self):
        # Sample Date
        # Sun, 2 Jun 2019 17:01:31 -0400 (EDT)
        sp = self.date.split()
        day = sp[1]
        month = sp[2]
        year = sp[3]
        self.date = Date(day, month, year)


def BuildRequest():
    pass


def Login():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds.token


def GetMessages(token):
    try:
        get_list_url = 'https://www.googleapis.com/gmail/v1/users/me/messages'
        r = requests.get(get_list_url, headers={
            'Authorization': 'Bearer ' + token})
        emails = r.json()
        return emails['messages']
    except:
        print("Error connecting")


def AssignMessage(token, emails):
    """
    Retrieves email based on id
    """
    email_list = []
    for email in emails:
        get_message_url = 'https://www.googleapis.com/gmail/v1/users/me/messages/'
        r = requests.get("%s%s" % (get_message_url, email['id']), headers={
            'Authorization': 'Bearer ' + token})
        email = r.json()

        try:
            efrom = list(filter(
                lambda emailf: emailf['value'] == "Chase <no-reply@alertsp.chase.com>", email['payload']['headers']))[0]['value']

            body = base64.b64decode(email['payload']['body']['data'])

            date = list(filter(
                lambda emaild: emaild['name'] == 'Date', email['payload']['headers']))[0]['value']

            the_email = Email(email['id'], efrom, body, date)
            email_list.append(the_email)
        except Exception as e:
            pass

    return email_list


def AssignTotals(emails):
    this_year = str(datetime.now().year)
    this_day = str(datetime.now().day)
    this_month = datetime.now().month
    year_total = 0
    day_total = 0
    month_total = 0
    for email in emails:
        if email.date.year == this_year:
            year_total += email.amount
        if email.date.day == this_day:
            day_total += email.amount
        if email.date.month == this_month:
            month_total += email.amount
        else:
            print(email.date.month)
            print(this_month)

    return round(day_total,2),round(month_total,2),round(year_total,2)

# Google Suggested Function


def create_message(sender, to, subject, message_text):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.

    Returns:
      An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text, 'plain')
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    return {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}


def SendMail(day, month, year, token):
    body = ("%s %s %s" % (day, month, year))
    to = "****redacted***8@messaging.sprintpcs.com"
    sender = "alert***redacted*****@gmail.com"
    subject = "yo"
    message = create_message(sender, to, subject, body)

    send_url = "https://www.googleapis.com/gmail/v1/users/me/messages/send"
    print(str(message))
    r = requests.post(send_url, headers={
        'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', 'Accept': 'application/json'}, data=str(message))
    print(message)
    print(r.text)


def main():

    # Call the Gmail API
    token = Login()
    email_list = GetMessages(token)
    assigned_emails = AssignMessage(token, email_list)
    day_total, month_total, year_total = AssignTotals(assigned_emails)
    print("Day: %s" % day_total)
    print("Month: %s" % month_total)
    print("Year: %s" % year_total)
    SendMail(day_total, month_total, year_total, token)


if __name__ == '__main__':
    main()
