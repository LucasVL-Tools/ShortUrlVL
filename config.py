url_letters = "QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm1234567890_-" #allowed characters in auto generated and custom urls. beware, as adding to this may lead to security vulnerabilities (eg, if incorrectly configured a user could set their url to be ../main.py and overwrite the python file)
domain = "url.lucasvl.nl" # domain to show for link output
url_length = 6 # length of randomly generated url
max_link_length = 500 # maximum length of link to be shortened
max_url_length = 64 # maximum length of a custom url
max_age = 24 # max age of a url before it deletes itself, in hours (decimal values OK)
default_age = 2 # default autodelete time if user does not change it
port = 8080 # port that the server runs on
host = "0.0.0.0" # address to listen on, recommended to keep this as is, unless you want to use a unix socket, in which case set it to an empty string
unix_socket = "./socket.sock" # path to the unix socket that you want to use (optional)
title = "My URL Shortener" # title displayed on browser bar

# Stuff for ReCaptcha. if you do not want to use ReCaptcha, change enable_captcha to False. otherwise, please replace the debug keys with keys you can generate at https://www.google.com/recaptcha/admin/ (captcha V2 checkbox version)
enable_captcha = True
captcha_site_key = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"
captcha_secret_key = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe" 
