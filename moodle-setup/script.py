import os
import time
import sys
import urllib.request
import json
import mysql.connector as database
from subprocess import call


def find_user_id(username):
    for user in data["users"]:
        if user["username"] == username:
            return user["id"]
    return -1


# Getting environment variables
MARIADB_PORT = os.environ['MARIADB_PORT']
MOODLE_PORT = os.environ['MOODLE_PORT']
MARIADB_DATABASE = os.environ['MARIADB_DATABASE']
MARIADB_USER = os.environ['MARIADB_USER']

# Loading json file
file_ = open('config.json')
data = json.load(file_)
file_.close()
print("Json file loaded!")

# Waiting for moodle webserver to start
while True:
    try:
        contents = urllib.request.urlopen("http://moodle:" + MOODLE_PORT).read()
        print("Moodle webserver is up and running!")
        break
    except:
        print("Waiting for moodle webserver to start...")
        time.sleep(5)

# Checking if oauth plugin is installed or not
if os.path.exists("/usr/src/app/moodle_data/local/oauth"):
    print("Oauth plugin is already installed!")
    sys.exit(0)

# Installing oauth plugin
print("Installing Oauth plugin...")
call(["cp", "-r", "/usr/src/app/oauth", "/usr/src/app/moodle_data/local/"])
print("Oauth plugin installed!")

# Connecting to database, at this point the database is already started
print("Connecting to database...")
connection = database.connect(
    host="mariadb",
    port=MARIADB_PORT,
    database=MARIADB_DATABASE,
    user=MARIADB_USER,
)

# Waiting for Oauth tables to be created
while True:
    try:
        cursor = connection.cursor(buffered=True)
        cursor.execute("SELECT * FROM mdl_oauth_clients")
        print("Oauth tables are created!")
        break
    except:
        print("Waiting for Oauth tables to be created... Login to moodle as admin, press buttons: continue -> refresh database -> continue")
        time.sleep(5)

# Inserting users to database
print("Inserting users to database...")
for user in data["users"]:
    username = user["username"]
    first_name = user["first_name"]
    last_name = user["last_name"]
    email = user["email"]

    cursor.execute('insert into mdl_user set auth = "manual", confirmed = 1, policyagreed = 1, deleted = 0, suspended = 0, mnethostid = 1, username = "'+ username +'", password = "$2y$10$ndYSjHRuFxWmFSpSgW2cl.47EDEezJ8XG0wr2TWYHQXfKStdMRRT2", firstname = "'+ first_name +'", lastname = "'+ last_name +'", email = "'+ email +'", emailstop = 0, lang = "en", calendartype = "gregorian", timezone = 99, firstaccess = 0, lastaccess = 0, lastlogin = 0, currentlogin = 0, picture = 0, descriptionformat = 1, mailformat = 1, maildigest = 0, maildisplay = 2, autosubscribe = 1, trackforums = 0, timecreated = 1680873634, timemodified = 1680873634, trustbitmask = 0, moodlenetprofile = NULL')
    connection.commit()
    user["id"] = cursor.lastrowid

print("Users inserted!")

# Inserting courses to database
print("Inserting courses to database...")
for course in data["courses"]:
    course_name = course["name"]
    course_short_name = course["name"]

    # inserting course
    cursor.execute('insert into mdl_course set category = 1, sortorder = 10001, fullname = "'+ course_name +'", shortname = "'+ course_short_name +'", summaryformat = 1, format = "topics", showgrades = 1, newsitems = 5, startdate = 1680908400, enddate = 1712444400, relativedatesmode = 0, marker = 0, maxbytes = 0, legacyfiles = 0, showreports = 0, visible = 1, visibleold = 1, downloadcontent = NULL, groupmode = 0, groupmodeforce = 0, defaultgroupingid = 0, timecreated = 1680883730, timemodified = 1680883730, requested = 0, enablecompletion = 1, completionnotify = 0, cacherev = 1680883736, originalcourseid = NULL, showactivitydates = 1, showcompletionconditions = 1')
    connection.commit()
    course["id"] = cursor.lastrowid

    # creating course context
    cursor.execute('insert into mdl_context set contextlevel = 50, instanceid = '+ str(course["id"]) +', depth = 3, locked = 0')
    connection.commit()
    course["context_id"] = cursor.lastrowid
    cursor.execute('update mdl_context set path = concat("/1/3/", cast(id as char)) where id=' + str(course["context_id"]))
    connection.commit()

    # creating course enrol mode (manual)
    cursor.execute('insert into mdl_enrol set enrol = "manual", courseid = '+ str(course["id"]) +', sortorder = 0, name = NULL, enrolperiod = 0, enrolstartdate = 0, enrolenddate = 0, expirynotify = 0, expirythreshold = 86400, notifyall = 0, password = NULL, cost = NULL, currency = NULL, roleid = 5, customint1 = NULL, customint2 = NULL, customint3 = NULL, customint4 = NULL, customint5 = NULL, customint6 = NULL, customint7 = NULL, customint8 = NULL, customchar1 = NULL, customchar2 = NULL, customchar3 = NULL, customdec1 = NULL, customdec2 = NULL, customtext1 = NULL, customtext2 = NULL, customtext3 = NULL, customtext4 = NULL, timecreated = 1680883730, timemodified = 1680883730')
    connection.commit()
    course["enrol_id"] = cursor.lastrowid

    # enrolling users to course
    for user in course["participants"]:
        user_id = find_user_id(user["username"])
        role = 5 if user["role"] == "student" else 3

        # enrolling user to course
        cursor.execute('insert into mdl_user_enrolments set status = 0, enrolid = '+ str(course["enrol_id"]) +', userid = '+str(user_id)+', timestart = 1680884699, timeend = 0, modifierid = 2, timecreated = 1680884721, timemodified = 1680884721')
        connection.commit()
        # assigning role to user
        cursor.execute('insert into mdl_role_assignments set roleid = '+ str(role) +', contextid = '+str(course["context_id"])+', userid = '+str(user_id)+', timemodified = 1680896286, modifierid = 2, itemid = 0, sortorder = 0')
        connection.commit()

print("Courses inserted!")

# Init moodle webservice API
print("Init moodle webservice API...")

# Enabling web services
cursor.execute('update mdl_config set value="1" where name="enablewebservices"')
connection.commit()

# Enabling protocols
#   Appending line '$CFG->webserviceprotocols = 'rest,soap,xmlrpc';' 
#   to config.php after first line that starts with $CFG->
with open('/usr/src/app/moodle_data/config.php', 'r+') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if line.startswith('$CFG->'):
            lines[i] = lines[i] + "$CFG->webserviceprotocols = 'rest,soap,xmlrpc';\n"
            break
    f.seek(0)
    for line in lines:
        f.write(line)

# Creating a custom external service
cursor.execute('insert into mdl_external_services set name = "Custom Service", enabled = 1, restrictedusers = 1, component = NULL, timecreated = 1680964993, timemodified = NULL, downloadfiles = 0, uploadfiles = 0')
connection.commit()
service_id = cursor.lastrowid

# Adding functions to the service
for function in data["moodle-webservice"]["functions"]:
    cursor.execute('insert into mdl_external_services_functions set externalserviceid = '+ str(service_id) +', functionname = "'+ function +'"')
    connection.commit()

# Authorise only specific users (admin)
cursor.execute('insert into mdl_external_services_users set externalserviceid = '+ str(service_id) +', userid = 2, iprestriction = NULL, validuntil = NULL, timecreated = 1680965294')
connection.commit()

# Create a token
token = data["moodle-webservice"]["token"]
private_token = data["moodle-webservice"]["private-token"]
# cursor.execute('insert into mdl_external_tokens set token = '+ token +', privatetoken = '+private_token+', tokentype = 0, userid = 2, externalserviceid = '+ str(service_id) +', sid = NULL, contextid = 1, creatorid = 2, iprestriction = NULL, validuntil = 0, timecreated = 1680965403, lastaccess = NULL')
cursor.execute('insert into mdl_external_tokens set tokentype = 0, userid = 2, externalserviceid = '+ str(service_id) +', sid = NULL, contextid = 1, creatorid = 2, iprestriction = NULL, validuntil = 0, timecreated = 1680965403, lastaccess = NULL')
cursor.execute('update mdl_external_tokens set token = "'+ token +'", privatetoken = "'+ private_token +'" where id = ' + str(cursor.lastrowid))
connection.commit()

print("Moodle webservice API configured!")

# Setting up Oauth
print("Setting up Oauth...")
client_id = data["oauth"]["client-id"]
client_secret = data["oauth"]["client-secret"]
redirect_uri = data["oauth"]["redirect-uri"]
cursor.execute('insert into mdl_oauth_clients set client_id = "'+ client_id +'", client_secret = "'+ client_secret +'", redirect_uri = "'+ redirect_uri +'", grant_types = "authorization_code", scope = "user_info", user_id = 0')
connection.commit()
print("Oauth configured!")

connection.close()
print("Done!")
