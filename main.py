#!/usr/bin/env python3
from flask import Flask, request, render_template, redirect, abort
import os, random, validators, logging, hashlib, time
from humanfriendly import format_timespan
from waitress import serve
from config import url_letters, domain, url_length, max_link_length, max_url_length, port, delete_interval, title

logging.basicConfig()
logger = logging.getLogger('waitress')
logger.setLevel(logging.DEBUG)

# starts the auto-deleter
n = os.fork()
if n > 0:
    print("Auto delete starting...")
    import auto_delete
    while True: pass
else: print("App starting...")

app = Flask(__name__)

print("App started!")

@app.route("/", methods=['GET'])
def home():
    return render_template("index.html", expires=format_timespan(delete_interval), domain=domain, title=title)

@app.route("/", methods=['POST'])
def info():
    url = request.form.get("lookup").strip()
    return redirect(f"/dash/{url}", code=302)

@app.route("/output", methods=['POST'])
def addlink():
    # gets the link that the user inputted, the preferred url, and strips them of any leading or trailing spaces
    link = request.form.get("link").strip()
    preferred_url = request.form.get("preferred_url").strip()
    passhash = str(hashlib.sha512(bytes(request.form.get("pass"), encoding='utf-8')).hexdigest())
    taken_urls = os.listdir("./urls")
    errors = ""
    # checks if the inputted link to be shortened is valid, to avoid unecessary processing of broken or outrageously long links
    if len(link) >= max_link_length:
        errors += "<li>Inputted link too long</li>"
    if validators.url(link) != True and validators.url(f"http://{link}") != True or link == "":      
        errors += "<li>Inputted link not valid</li>"
    elif validators.url(f"http://{link}"):
        link = f"http://{link}"

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
        return render_template("errors.html", errors=errors, title=title)

    # if there is no preferred url, randomly generate one
    if not preferred_url:
        while True:
            random_url = ""
            for i in range(url_length):
                random_url += random.choice(url_letters)
            taken_urls = os.listdir("./urls")
            if random_url not in taken_urls:
                break
        url = random_url

    # write url to file
    file = open(f"./urls/{url}", "a")
    file.write(f"{link}\n0\n{passhash}\n")
    return render_template("output.html", url=url, domain=domain, title=title)

# redirects user to desired link
@app.route("/l/<url>", methods=['GET'])
def expand_url(url):
    try: file = open(f"./urls/{url}", "r")
    except: abort(404)
    file_content = file.readlines()
    link = file_content[0][:-1]
    # add 1 to the click count of the link
    file_content[1] = str(int(file_content[1][:-1]) + 1) + "\n"
    file = open(f"./urls/{url}", "w")
    file.writelines(file_content)
    return redirect(link, code=302)

#############################
# DASHBOARD PAGE WITH LOGIN #
#############################

# login page
@app.route("/dash/<url>", methods=['GET'])
def loginpage(url):
    try: file = open(f"./urls/{url}", "r")
    except: abort(404)
    file_content = file.readlines()
    # makes sure the url has a password, the hash in the string is the hash for an empty string. if no password is set (empty password), then user is redirected straight to the dashboard
    if file_content[2] != "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e\n":
        return render_template("login.html", url=url, access="", title=title)
    else:
        clicks = file_content[1][:-1]
        expiry = format_timespan(delete_interval - (time.time() - os.stat(f"./urls/{url}").st_mtime), max_units=2)
        return render_template("info.html", url=url, link=file_content[0][:-1], clicks=clicks, expiry=expiry)

# checks if password is correct, and if yes return the dashboard
@app.route("/dash/<url>", methods=['POST'])
def dash(url):
    try: file = open(f"./urls/{url}", "r")
    except: abort(404)
    file_content = file.readlines()
    if file_content[2][:-1] == str(hashlib.sha512(bytes(request.form.get("pass"), encoding='utf-8')).hexdigest()):

        # checks for any "extra options" and executes them
        delurl = request.form.get("delete")
        rmpass = request.form.get("rmpass")
        rscount = request.form.get("rscount")
        link = request.form.get("link").strip()
        options = ""
        if delurl or rmpass or rscount or link:
            file = open(f"./urls/{url}", "w")
            if delurl:
                os.remove(f"./urls/{url}")
                return f"Deleted URL {url}"
            if rmpass:
                file_content[2] = "<li>cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e</li>"
                options += f"<li>Removed password for {url}</li>"
            if rscount:
                file_content[1] = "0\n"
                options += f"<li>Reset click counter for {url}</li>"
            if link: 
                errors = ""
                if len(link) >= max_link_length:
                    errors += "<li>Inputted link too long</li>"
                if validators.url(link) != True:
                    errors += "<li>Inputted link not valid, make sure it begins with http:// or https://</li>"
                if errors:
                    options += f'<li class="error">could not change link due to following errors: <ul>{errors}</ul></li>'
                else:
                    options += f"<li>Changed link from {file_content[0][:-1]} to {link}</li>"
                    file_content[0] = f"{link}\n"
                

            file.writelines(file_content)
            file = open(f"./urls/{url}", "r")
            file_content = file.readlines()

        if options: options = f"<ul>{options}</ul>"
        clicks = file_content[1][:-1]
        expiry = format_timespan(delete_interval - (time.time() - os.stat(f"./urls/{url}").st_mtime), max_units=2)
        return render_template("info.html", url=url, link=file_content[0][:-1], clicks=clicks, expiry=expiry, options=options)
    else: 
        return render_template("login.html", url=url, access='<p class="red">Access Denied</p>', title=title)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#app.run(debug = True)
serve(app, host="0.0.0.0", port=port)
