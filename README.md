# boxperts-tableau-wdc 
Boxperts-tableau-wdc is a web driver application to get metafields data from box.com.

## Installation

[1] You need to create a new application in box.com.
just visit 
[Box Applications Page](https://app.box.com/developers/services/)
and click on "Create a Box Application" link.

[2] Save 'client_id' and 'client_secret' somewhere

[3] enter the 'redirect_uri' (NOTE: redirect URI should fit OAUTH2 specification)

[4] Click "Save Application" button at the bottom of the page

[5] clone this repo. Right after that do (You'll have to install docker first):

 `cp settings.py.default settings.py`

  `cp web.env.default web.end`

  `docker-compose build && docker-compose up -d`
  
  
 
