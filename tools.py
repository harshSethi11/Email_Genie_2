import gspread
import os
import json
import pandas
import streamlit as st
from google.oauth2.service_account import Credentials
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

app_pswd = os.environ.get("app_pswd")
sheet_id = os.environ.get("sheet_id")


email_add = "harshsethisgd@gmail.com"
my_name = "harsh sethi"
template_col_name = "template"

def customerDetailsGsheets( objective,personal_details,industry,recipientRole,recipientName):
    scopes = [
    "https://www.googleapis.com/auth/spreadsheets"
    ]
    creds = Credentials.from_service_account_file("credentials.json", scopes= scopes)
    client = gspread.authorize(creds)
    try:
        workbook = client.open_by_key(sheet_id)
    except gspread.SpreadsheetNotFound:
        return {"response": "Spreadsheet not found.", "status": "error"}

    # Select the specific worksheet (tab) where you want to append the data
    try:
        sheet = workbook.worksheet("Sheet1")  # Add the worksheet name here
    except gspread.WorksheetNotFound:
        return {"response": "Worksheet not found.", "status": "error"}
    
    # Append the customer details as a new row in the worksheet
    if not (objective and personal_details):
        return{
            "response" : "please enter the important details"
        }


    try:
        sheet.append_row([objective, personal_details, industry, recipientRole, recipientName])
        return {
            "response": "Saved customer details in Google Sheet.",
            "display": {
                "text": f"Customer details saved in Google Sheet: [Link]({workbook.url})"
            },
            "status": "success"
        }
    except Exception as e:
        return {"response": f"Error saving data: {str(e)}", "status": "error"}


def saveTemplate(template:str):
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets"
    ]

    # Authorize using the service account credentials
    creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    client = gspread.authorize(creds)

    # Open the workbook using the spreadsheet ID
    workbook = client.open_by_key(sheet_id)

    # Try to access the specific worksheet
    try:
        sheet = workbook.worksheet("Sheet1")
    except gspread.WorksheetNotFound:
        print(f"Worksheet 'Sheet1' not found.")
        return {
            "response": "Failed to save template. Worksheet not found.",
            "display": {
                "text": "Failed to save template. Worksheet not found."
            },
            "status": "error"
        }

    # Get the headers to locate the template column
    headers = sheet.row_values(1)
    try:
        templateColIndex = headers.index(template_col_name) + 1  # Replace with your actual column name
    except ValueError:
        print("Template column not found in the headers.")
        return {
            "response": "Failed to save template. Template column not found.",
            "display": {
                "text": "Failed to save template. Template column not found."
            },
            "status": "error"
        }

    # Find the last available row to insert the template
    lastRow = len([row for row in sheet.get_all_values() if any(row)])

    # Update the cell with the template in the correct column
    sheet.update_cell(lastRow, templateColIndex, template)

    # Return success response
    return {
        "response": "Saved template in Google Sheet.",
        "display": {
            "text": f"Template saved successfully in Google Sheet: [Link]({workbook.url})"
        },
        "status": "success"
    }


def sendEmail(recipient_mail,mail_body,mail_subject):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    # Your Gmail credentials
    sender_email = email_add
    password = app_pswd
    receiver_email = recipient_mail

    # Set up the server using Gmail's SMTP server
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()  # Secure the connection
    server.login(sender_email, password)

    # Create email
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = mail_subject

    # Email body
    body = mail_body
    msg.attach(MIMEText(body, 'plain'))

    # Send the email
    try:
        server.sendmail(sender_email, receiver_email, msg.as_string())
         # Log email stats
        email_status = {
            'date': datetime.now().isoformat(),
            'requests': 1,
            'delivered': 1  # Assuming delivery was successful
        }
        with open('email_stats.json', 'a') as f:
            json.dump(email_status, f)
            f.write('\n')  # New line for each log entry

        # Disconnect from the server
        server.quit()

        print("Email sent successfully!")
        return {
            "response": "Email sent",
            "display": {
                "text": f"Email sent to {recipient_mail}"
            }
        }
    except Exception as e:
        print(e.message)
        server.quit()
        return {
            "response": f"Failed to send email. Error: {e.message}",
            "display": {
                "text": f"Failed to send email to {recipient_mail}"
            }
        }

   
toolsInfo = {
    "customerDetailsGsheets": {
        "func": customerDetailsGsheets,
        "schema": {
            "type": "function",
            "function": {
                "name": "customerDetailsGsheets",
                "description": "Saves customer details in Google Sheets",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "objective": {
                            "type": "string",
                            "description": "Objective or purpose of the email"
                        },
                        "personal_details": {
                            "type": "string",
                            "description": "Personal details about the sender"
                        },
                        "industry": {
                            "type": "string",
                            "description": "Recipient's industry"
                        },
                        "recipientRole": {
                            "type": "string",
                            "description": "Recipient's role in the company"
                        },
                        "recipientName": {
                            "type": "string",
                            "description": "Name of the recipient"
                        }
                    },
                    "required": ["objective", "personal_details", "industry", "recipientRole", "recipientName"]
                }
            }
        },
    },

    "saveTemplate": {
        "func": saveTemplate,
        "schema": {
            "type": "function",
            "function": {
                "name": "saveTemplate",
                "description": "Saves the email template in Google Sheets",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "template": {
                            "type": "string",
                            "description": "Email template to save"
                        }
                    },
                    "required": ["template"]
                }
            }
        },
    },

    "sendEmail": {
        "func": sendEmail,
        "schema": {
            "type": "function",
            "function": {
                "name": "sendEmail",
                "description": "Sends an email to the recipient",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipient_mail": {
                            "type": "string",
                            "description": "Email address of the recipient"
                        },
                        "mail_body": {
                            "type": "string",
                            "description": "Body content of the email"
                        },
                        "mail_subject": {
                            "type": "string",
                            "description": "Subject of the email"
                        }
                    },
                    "required": ["recipient_mail", "mail_body", "mail_subject"]
                }
            }
        },
    },
}




