#!/usr/bin/env python3
from flask import Flask, request, render_template, redirect, abort
import os, random, validators, logging, hashlib, time
from humanfriendly import format_timespan
from waitress import serve
from config import ( 
    url_letters, 
    domain, 
    url_length, 
    max_link_length, 
    max_url_length, 
    port, 
    max_age, 
    default_age, 
    title, 
    host, 
    unix_socket, 
    captcha_site_key, 
    captcha_secret_key, 
    enable_captcha 
)

# url = url.lucasvl.nl/whatever-is-here
# link = the link the user wants shortened
# use _ for variable names
# if it can go in to the config file, put it in to the config file and import the variable above
# happy developing! feel free to open up an issue on my gitea if you have any issues with forking or changing the project

# Logging stuff for the waitress WSGI server
logging.basicConfig()
logger = logging.getLogger('waitress')
logger.setLevel(logging.DEBUG)

# Starts the auto-deleter, done by forking the process and checking if the process is a parent or child. if process is child, run auto delete. if process is parent, run app.
n = os.fork()
if n > 0:
    import auto_delete
    while True: pass
else: print("App started!")

app = Flask(__name__)
app.config.update(
    XCAPTCHA_SITE_KEY = captcha_site_key,
    XCAPTCHA_SECRET_KEY = captcha_secret_key
)
if enable_captcha:
    from flask_xcaptcha import XCaptcha
    xcaptcha = XCaptcha(app=app, theme="dark")

##############################
# LINK CREATION AND HOMEPAGE #
##############################

# Code for serving home page
@app.route("/", methods=['GET'])
def home():
    return render_template("index.html", max_age=max_age, default_age=default_age, domain=domain, title=title)

# Code for URL lookup form on main page
@app.route("/", methods=['POST'])
def info():
    url = request.form.get("lookup").strip()
    return redirect(f"/dash/{url}", code=302)

# Code for link shortening. this part is what accepts the form info from the index page and outputs a shortened link
@app.route("/output", methods=['POST'])
def addlink():
    # first check if the captcha is correct. if not, show error. if correct, just continue like nothing ever happened (you saw nothing)
    if enable_captcha:
        if not xcaptcha.verify():
            return render_template("errors.html", errors="<li>Captcha Failed, please complete the captcha and try again.</li>", title=title)

    # gets the link that the user inputted, the preferred url, and the expiration date, and strips them of any leading or trailing spaces
    link = request.form.get("link").strip()
    preferred_url = request.form.get("preferred_url").strip()
    expires = request.form.get("expire").strip()
    expires_hours = expires
    reset_on_click = request.form.get("reset_on_click")
    
    # generates a hash of the inputted password
    passhash = str(hashlib.sha512(bytes(request.form.get("pass"), encoding='utf-8')).hexdigest())
    
    # run series of tests on user input to determine if it is valid
    taken_urls = os.listdir("./urls")
    errors = ""
    if len(link) >= max_link_length:
        errors += "<li>Inputted link too long</li>"

    # since validators module needs an https://, run both with and without adding one, and then use the valid one.
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
    
    #make sure an expiration time is provided. if not, return an error. if yes, convert to unix timestamp.
    if expires:
        try: 
            expires = float(expires)
            if expires > 0 and expires <= max_age:
                valid_expires = True
                expires = expires * 60 * 60 + time.time()
            else:
                errors += f"<li>Hours until expires value must be greater than 0, and less than or equal to {max_age}</li>"
        except: 
            errors += "<li>Hours until expires field must be a decimal number</li>"
    else: errors += "<li>No hours until expiration provided</li>"

    # in there are errors with the user input the code stops running here and returns the error page
    if errors:
        return render_template("errors.html", errors=errors, title=title)

    # if there is no preferred url, randomly generate one and set the url variable mentioned before to the random url
    if not preferred_url:
        while True:
            random_url = ""
            for i in range(url_length):
                random_url += random.choice(url_letters)
            taken_urls = os.listdir("./urls")
            if random_url not in taken_urls:
                break
        url = random_url

    # write everything to file and return the shortened url
    file = open(f"./urls/{url}", "a")
    file.write(f"{link}\n0\n{passhash}\n{expires}\n{expires_hours}\n{reset_on_click}\n")
    return render_template("output.html", url=url, domain=domain, title=title)


#################
# APP REDIRECTS #
#################

@app.route("/l/<url>", methods=['GET'])
def expand_url(url):
    #try opening the file, if it does not exist return 404 and stop there
    try: file = open(f"./urls/{url}", "r")
    except: abort(404)

    file_content = file.readlines()
    link = file_content[0][:-1]

    # add 1 to the click count of the url and then return a redirect to the correct link
    file_content[1] = str(int(file_content[1][:-1]) + 1) + "\n"
    expires_hours = float(file_content[4][:-1])
    if file_content[5] == "on\n":
        file_content[3] = str(expires_hours * 60 * 60 + time.time()) + "\n"
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
        return render_template("login.html", url=url, access="", title=title, max_age=max_age)
    else:
        clicks = file_content[1][:-1]
        # this mess calculates how long until the URL expires. on the off-chance that the auto delete script is late to delete, output 0 using max()
        expiry = format_timespan(max(int(float(file_content[3][:-1])) - int(time.time()), 0), max_units=2)
        return render_template("info.html", url=url, link=file_content[0][:-1], clicks=clicks, expiry=expiry)

# checks if password is correct, and if yes return the dashboard
@app.route("/dash/<url>", methods=['POST'])
def dash(url):
    try: file = open(f"./urls/{url}", "r")
    except: abort(404)
    file_content = file.readlines()

    # makes a hash of the password submitted and checks it against the stored hash. it it is execute the request
    if file_content[2][:-1] == str(hashlib.sha512(bytes(request.form.get("pass"), encoding='utf-8')).hexdigest()):
        # checks for any "extra options" and executes them
        delurl = request.form.get("delete")
        rmpass = request.form.get("rmpass")
        rscount = request.form.get("rscount")
        link = request.form.get("link").strip()
        expire = request.form.get("expire")
        reset_on_click = request.form.get("reset_on_click")
        options = ""
        # this if statement seems useless but it actually ensures against uneccesary latency and disk i/o by skipping opening the file to write
        if delurl or rmpass or rscount or link or expire or reset_on_click:
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
                if validators.url(link) != True and validators.url(f"http://{link}") != True or link == "":
                    errors += "<li>Inputted link not valid</li>"
                elif validators.url(f"http://{link}"):
                    link = f"http://{link}"
                if errors:
                    options += f'<li class="error">could not change link due to following errors: <ul>{errors}</ul></li>'
                else:
                    options += f"<li>Changed link from {file_content[0][:-1]} to {link}</li>"
                    file_content[0] = f"{link}\n"
            if expire:
                try:
                    expire = float(expire)
                    if expire > 0 and expire <= max_age:
                        expire_hours = expire
                        expire = expire * 60 * 60 + time.time()
                        file_content[3] = f"{expire}\n"
                        file_content[4] = f"{expire_hours}\n"
                    else:
                        errors = f"<li>Hours until expires value must be greater than 0, and less than or equal to {max_age}</li>"
                except:
                    errors += "<li>Hours until expires field must be a decimal number</li>"
            if reset_on_click and file_content[5] != "on\n":
                file_content[5] = "on\n"
                options += "<li>Auto-delete timer will now reset on every use of URL</li>"

            # writes changes from the options to the file, and reopen as read for the rest of the process
            file.writelines(file_content)
            file = open(f"./urls/{url}", "r")
            file_content = file.readlines()

        # format the options and render template with info
        if options: options = f"<ul>{options}</ul>"
        clicks = file_content[1][:-1]
        expiry = format_timespan(max(int(float(file_content[3][:-1])) - int(time.time()), 0), max_units=2)
        return render_template("info.html", url=url, link=file_content[0][:-1], clicks=clicks, expiry=expiry, options=options)
    else: 
        # if authentication fails, return access denied and send user back to login page
        return render_template("login.html", url=url, access='<p class="red">Access Denied</p>', title=title)

###############
# ERROR PAGES #
###############

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# checks for unix socket or host in config file and runs waitress accordingly. 
#app.run(debug = True)
if host:
    serve(app, host=host, port=port)
elif unix_socket:
    serve(app, unix_socket=unix_socket, unix_socket_perms="777")
else: print("Please specify a host or unix socket (you probably just want host to be set to 0.0.0.0)")
