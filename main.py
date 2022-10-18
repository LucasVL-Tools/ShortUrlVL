#!/usr/bin/env python3
from flask import Flask, request, render_template, redirect
import os, random, validators
from config import url_letters, domain, url_length, max_link_length, max_url_length

# starts the auto-deleter
n = os.fork()
if n > 0:
    print("Auto delete starting...")
    import auto_delete
    while True: pass
else: print("App starting...")

app = Flask(__name__)

@app.route("/", methods=['GET'])
def home():
    return render_template("index.html")

@app.route("/output", methods=['POST'])
def addlink():
    # gets the link that the user inputted, the preferred url, and strips them of any leading or trailing spaces
    link = request.form.get("link").strip()
    preferred_url = request.form.get("preferred_url").strip()
    taken_urls = os.listdir("./urls")
    errors = ""
    # checks if the inputted link to be shortened is valid, to avoid unecessary processing of broken or outrageously long links
    if len(link) >= max_link_length:
        errors += "<li>Inputted link too long</li>"
    if validators.url(link) != True or link == "":      
        errors += "<li>Inputted link not valid, make sure it begins with http:// or https://</li>"

    # if the user has a preferred url, check if the url they chose meets the guidelines, and then set the url variable to the preferred url
    if preferred_url:
        valid_length = True
        valid_chars = True
        url_available = True

        if len(preferred_url) >= max_url_length:
            errors += "<li>Requested URL is too long</li>"
            valid_length = False

        # ensure url contains no invalid characters
        for l in preferred_url:
            if l not in url_letters:
                valid_chars = False
                break
        if valid_chars == False:
            errors += "<li>Requested URL contains invalid characters</li>"

        elif preferred_url in taken_urls:
            url_available = False
            errors += "<li>Requested URL is already taken</li>"

        # set url variable to the desired url if all checks pass
        if url_available == True and valid_chars == True and valid_length == True: 
            url = preferred_url

    if errors:
        return(f"Could not shorten url due to the following errors:<ul>{errors}</ul>")

    # if there is no preferred url, randomly generate one
    if not preferred_url:
        while True:
            random_url = ""
            for i in range(url_length):
                random_url += random.choice(url_letters)
            if random_url not in taken_urls:
                break
        url = random_url

    # write url/gnome to file
    file = open(f"./urls/{url}", "a")
    file.write(f"{link}")
    return render_template("output.html", url=url, domain=domain)

# redirects user to desired link
@app.route("/l/<url>", methods=['GET'])
def expand_url(url):
    file = open(f"./urls/{url}", "r")
    link = file.read()
    return redirect(link, code=302)

app.run(debug = True)
