import datetime
import json
import os
import functions_framework
from google.cloud import storage
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


# function entry point
@functions_framework.cloud_event
def report(event):
    # assert all needed env vars are set
    # SENDGRID_API_KEY
    # BUCKET_NAME
    assert "SENDGRID_API_KEY" in os.environ
    assert "BUCKET_NAME" in os.environ

    # if downloads directory doesn't exist, create it
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    # download unique_words.json from GCP bucket to downloads folder
    # always download the latest version of unique_words.json
    # if the file already exists, overwrite it
    storage_client = storage.Client()
    bucket = storage_client.bucket(os.environ["BUCKET_NAME"])
    blob = bucket.blob("unique_words.json")
    blob.download_to_filename("downloads/unique_words.json")

    # read unique_words.json into a dictionary
    with open("downloads/unique_words.json", "r") as f:
        unique_words = json.load(f)

    # format of the file is a dictionary with the following structure:
    #  {"filename": "filename", "date": "2023-01-01T00:00:00", "new_words": 381409}

    # datetime of now minus 7 days
    seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)

    # traverse the dictionary
    # count the total
    # count the total for the last 7 days
    # count the total for the last 24 hours
    total = 0
    total_seven_days = 0
    total_one_day = 0
    # get the files field containing the list of files
    for file in unique_words["files"]:
        # increment total
        total += file["new_words"]
        # get the date of the file
        date = datetime.datetime.strptime(file["date"], "%Y-%m-%dT%H:%M:%S")
        # if the date is within the last 7 days, increment total_seven_days
        if date > seven_days_ago:
            total_seven_days += file["new_words"]
        # if the date is within the last 24 hours, increment total_one_day
        if date > one_day_ago:
            total_one_day += file["new_words"]

    # format the date nicely
    nice_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    email_body = f"Report of new word forms found. Report generated at {nice_date}."

    # add empty lines before the total
    email_body += f"\n\n\n"

    email_body += f"Total: {total}\n"
    email_body += f"Total last 7 days: {total_seven_days}\n"
    email_body += f"Total last 24 hours: {total_one_day}\n"

    # add some empty lines before prompts
    email_body += f"\n\n\n"

    # get the latest prompt from prompts.md
    # download prompts.md from GCP bucket to downloads folder
    # always download the latest version of prompts.md
    prompt_blob = bucket.blob("prompts.md")
    prompt_blob.download_to_filename("downloads/prompts.md")

    # read prompts.md into a string
    with open("downloads/prompts.md", "r") as f:
        prompts = f.read()

    # read prompts.md line by line
    # current_prompts holds the prompt lines after the latest title
    current_prompts = []
    for line in prompts.splitlines():
        # if the line is a title, clear current_prompts
        if line.startswith("#"):
            current_prompts = []
        current_prompts.append(line)

    # add the current prompts to the email body
    email_body += "\n".join(current_prompts)
    # add signature
    email_body += "\n\n\n"
    email_body += "Sent by the New Word Forms Report Generator"

    # reformat the email body as html (for sendgrid)
    # make every line a <p> tag
    email_body_html = "<p>" + email_body.replace("\n", "</p><p>") + "</p>"
    # replace empty <p> tags with <br> tags
    email_body_html = email_body_html.replace("<p></p>", "<br>")

    subject = "New Word Forms Report"

    # assert env vars are set
    assert "FROM_EMAIL" in os.environ
    assert "TO_EMAIL" in os.environ

    # take the email addresse from env vars
    from_email = os.environ["FROM_EMAIL"]
    to_email = os.environ["TO_EMAIL"]

    # send email
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=email_body_html,
    )
    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)
