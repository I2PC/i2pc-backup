#!/usr/bin/python
"""
Simple HTTP server to be used as an internal, non-authorized notification email gateway.

Using multipart with curl:

  $ curl -X POST http://localhost:1396/ -F subject="SUBJECT" -F body="BODY"

Using postdata with wget:

  $ wget http://localhost:1396/ --post-data "SUBJECT;BODY"
"""
import cgi
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import smtplib
import socket
import sys
import traceback
import urllib

def debug(msg):
    print(msg, file=sys.stderr)

def send_email(sender_email, sender_pass, recipients, subject, body, smtp_server="smtp.gmail.com", port=587):
    server = smtplib.SMTP(smtp_server, port)
    server.ehlo()
    server.starttls()
    server.login(sender_email, sender_pass)
    contents = [
        "To: %s" % ", ".join(recipients),
        "From: %s" % sender_email,
        "Subject: %s" % subject,
        "", body,
    ]
    server.sendmail(sender_email, recipients, "\r\n".join(contents))
    debug("Email with subject '{}' sent to {}".format(subject, recipients))
    server.quit()

def parse_form_params(request):
    ctype, pdict = cgi.parse_header(request.headers["content-type"])
    if ctype != "multipart/form-data":
        length = int(request.headers['content-length'])
        field_data = request.rfile.read(length)
        subject, body = field_data.decode("utf-8").split(";", 1)
        return dict(subject=subject, body=body)
    else:
        pdict_bytes = dict(pdict, boundary=bytes(pdict["boundary"], "utf-8"))
        params_bytes = cgi.parse_multipart(request.rfile, pdict_bytes)
        return {k: v[0].decode("utf-8") for (k, v) in params_bytes.items()}

def send_email_from_request(request, email, password, recipients):
    params = parse_form_params(request)
    send_email(sender_email=email, sender_pass=password, recipients=recipients,
            subject=params["subject"], body=params["body"])

def json_response(response, obj, status=200):
    response.send_response(200)
    response.send_header("Content-type", "application/json")
    response.end_headers()
    body = bytes(json.dumps(obj, indent=4, sort_keys=True) + "\n", "utf-8")
    response.wfile.write(body)

def getHandler(email, password, recipients):
    class EmailHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            try:
                send_email_from_request(self, email, password, recipients)
                json_response(self, dict(status="ok"))
            except Exception as exc:
                traceback.print_exc()
                json_response(self, dict(status="error", message=str(exc)), status=400)
    return EmailHandler

def run_server(recipients, bindaddr="", port=8000):
    dirname = os.path.dirname(os.path.realpath(__file__))
    auth_path = os.path.join(dirname, "i2pc-backup-email-server.auth")
    email, password = open(auth_path).readline().split(None, 1)
    httpd = HTTPServer((bindaddr, port), getHandler(email, password, recipients))
    httpd.serve_forever()

if __name__ == "__main__":
    recipients = sys.argv[1:]
    if not recipients:
        raise ValueError("Usage: i2pc-backup-email-server RECIPIENT [...RECIPIENT]")
    run_server(port=1396, recipients=recipients)
    
