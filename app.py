import os
import datetime
import ast
import random

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import error, login_required

#export FLASK_ENV=development --> for testing before flask run


# Configure application
app = Flask(__name__)


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.run(debug=True)
# Ensure responses aren't cached


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///coop.db")


@app.route("/login", methods=["GET", "POST"])
def login():
    """login"""
    #forget any user
    session.clear()
    if request.method == "POST":
        #gather info
        username = request.form.get("username")
        password = request.form.get("password")
        #ensure stuff was put in
        if not username:
            return error("Must Provide a Username", "/login")
        elif not password:
            return error("Must Provide a Password", "/login")
        #make sure valid info
        rows = db.execute(
            "SELECT * FROM user WHERE username=:username", username=username)
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], password):
            return error("Invalid Username and/or Password", "/login")
        #set user_id in session
        session["user_id"] = rows[0]["id"]
        return redirect("/about")
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register and create profile in one"""
    if request.method == "POST":
        #get info from form
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        host = request.form.get("host")
        users = db.execute("SELECT username FROM user")
        #check to make sure info is correct
        if not username:
            return error("Must Provide a Username", "/register")
        elif not password:
            return error("Must Provide a Password", "/register")
        elif password != confirmation:
            return error("Passwords Do Not Match", "/register")
        for x in users:
            for y in x.values():
                if username == y:
                    return error("username already exists", "/register")
        if not host:
            host=0
        else:
            host=1
        #insert new user into table and store hashed password
        db.execute("INSERT INTO user (username, password, host) VALUES (:username, :password, :host)",
                   username=username, password=generate_password_hash(password), host=host)
        #set the user id in session
        user_id = db.execute(
            "SELECT id FROM user WHERE username = :username", username=username)[0]["id"]
        session["user_id"] = user_id
        #CREATE profile stuff
        name = request.form.get("name")
        bio = request.form.get("bio")
        race = request.form.get("race")
        age = request.form.get("age")
        location = request.form.get("location")
        phone = request.form.get("phone")
        email = request.form.get("email")
        info = request.form.get("info")
        #make sure all filled
        if not name or not bio or not age or not location or not phone or not email:
            return error("Requirements Not Satisfied", "/register")
        if not info:
            info = None
        db.execute("INSERT INTO profile (id, username, name, bio, race, age, location, phone, email, info) VALUES (:user_id, :username, :name, :bio, :race, :age, :location, :phone, :email, :info);",
                       user_id=session["user_id"], username=username, name=name, bio=bio, race=race, age=age, location=location, phone=phone, email=email, info=info)
        return redirect("/profile")
    else:
        return render_template("register.html")


@app.route("/logout")
def logout():
    """Logout"""
    #forget user
    session.clear()
    return redirect("/")


@app.route("/")
def index():
    """home page if not logged in"""
    return render_template("index.html")

@app.route("/start")
def start():
    """Delete Account"""
    return render_template("login.html")

@app.route("/about", methods=["GET", "POST"])
def about():
    """Show profile"""
    return render_template("about.html")


@app.route("/profile", methods=["GET", "POST"])
def profile():
    """Show profile"""
    if request.method == "POST":
        #MUST HAVE VALUE OF PERSON WHO WAS CLICKED ON ID (CREATE A HIDDEN INPUT?)
        #if clicked on friend profile
        person_id = request.form.get("person_id")
        row = db.execute(
            "SELECT * FROM profile WHERE id = :user_id", user_id=person_id)[0]
        return render_template("profile.html", row=row, yours=None)
    else:
        #if going to your own profile
        row = db.execute(
            "SELECT * FROM profile WHERE id = :user_id", user_id=session["user_id"])[0]
        return render_template("profile.html", row=row, yours="yes")


@app.route("/updateProf", methods=["GET", "POST"])
def updateProf():
    """actually update the profile"""
    if request.method == "POST":
        #CREATE profile stuff
        name = request.form.get("name")
        bio = request.form.get("bio")
        race = request.form.get("race")
        age = request.form.get("age")
        location = request.form.get("location")
        phone = request.form.get("phone")
        email = request.form.get("email")
        info = request.form.get("info")
        #make sure all filled
        if not name or not bio or not race or not age or not location or not phone or not email:
            return error("Requirements Not Satisfied", "/profile")
        if not info:
            info = None
        db.execute("UPDATE profile SET name=:name, bio=:bio,race=:race, age=:age,location=:location,phone=:phone,email=:email,info=:info WHERE id=:user_id;",
                   user_id=session["user_id"], name=name, bio=bio, race=race, age=age, location=location, phone=phone, email=email, info=info)
        return redirect("/profile")


@app.route("/updateProf2", methods=["GET", "POST"])
def updateProf2():
    """upodate your profile link"""
    if request.method == "POST":
        row = request.form.get("row")
        #unwraps the dict form the string
        row = ast.literal_eval(row)
        return render_template("updateProfile.html", row=row)


@app.route("/friends", methods=["POST", "GET"])
def partners():
    """Show friends"""
    if request.method == "POST":
        person_id = request.form.get("person_id")
        if person_id == session["user_id"]:
            return error("Cannot partner with self", "/browse")
        #check if partening already exists
        prev = db.execute("SELECT * FROM friends WHERE username2 = :user AND username1=:user1",
                          user=session["user_id"], user1=person_id)
        prev2 = db.execute("SELECT * FROM friends WHERE username1 = :user  AND username2=:user2",
                           user=session["user_id"], user2=person_id)
        if len(prev) == 0 and len(prev2) == 0:
            db.execute("INSERT INTO friends (username1, username2) VALUES (:user1, :user2)",
                       user1=session["user_id"], user2=person_id)
        return redirect("/friends")
    else:
        friendsName = []
        #check if your username is in the user1 slot
        friend_name = db.execute(
            "SELECT username1 FROM friends WHERE username2 = :user", user=session["user_id"])
        #if not nothing
        if len(friend_name) != 0:
            #loop through ever dict pair
            for friend in friend_name:
                #append the value of the dict
                friendsName.append(friend["username1"])
        #check if your username is in the user2 slot
        friend_name2 = db.execute(
            "SELECT username2 FROM friends WHERE username1 = :user", user=session["user_id"])
        #if not nothing
        if len(friend_name2) != 0:
            #loop through every dict pair
            for friend in friend_name2:
                #append val of dict
                friendsName.append(friend["username2"])
        #create array for profiles of partners
        friends = []
        #if not nothing
        if len(friendsName) != 0:
            #loop through every id of friends
            for friend in friendsName:
                #append their matching profile row
                row = db.execute(
                    "SELECT * FROM profile WHERE id=:person_id", person_id=friend)[0]
                friends.append(row)
        #display the partners by inputting the list of friend's profiles
        # if len(friends) == 0:
        #     return render_template("noPartners.html")
        return render_template("friends.html", friends=friends)


@app.route("/remove", methods=["POST", "GET"])
def remove():
    """remove friends"""
    if request.method == "POST":
        person_id = request.form.get("person_id_remove")
        #delete partner
        db.execute("DELETE FROM friends WHERE username1=:user1 AND username2=:user2;",
                   user1=session["user_id"], user2=person_id)
        db.execute("DELETE FROM friends WHERE username2=:user1 AND username1=:user2;",
                   user1=session["user_id"], user2=person_id)
        return redirect("/friends")


@app.route("/browse", methods=["POST", "GET"])
def browse():
    """Browse other people"""
    if request.method == "POST":
        #means something was searched
        searchVal = request.form.get("search2")
        #filter out reg words from search Arr
        words = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours",
                 "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it",
                 "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom",
                 "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have",
                 "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or",
                 "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between",
                 "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in",
                 "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when",
                 "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
                 "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will",
                 "just", "don", "should", "now"]
        #if there are no searches
        if not searchVal:
            #get all from internship database
            rows = db.execute(
                "SELECT * FROM profile WHERE id NOT IN (:user_id)", user_id=session["user_id"])
            return render_template("browse.html", rows=rows)
        #if there are items in the search bar
        else:
            searchArr = searchVal.split(" ")
            searchArrCopy = searchArr
            #loop through all words in stop words array
            for word in words:
                #if word in the searched items
                if word in searchArr:
                    #remove it from the copy
                    searchArrCopy.remove(word)
            #define the reg array as the copy array that has been updates
            searchArr = searchArrCopy
            #get rows that correspond with search from internship database
            for val in searchArr:
                rows = []
                rowsTemp = db.execute("SELECT * FROM profile WHERE id NOT IN (:user_id) AND (username LIKE ('%' || :search || '%') OR bio LIKE ('%' || :search || '%') OR name LIKE ('%' || :search || '%'))", search=val, user_id=session["user_id"])
                for row in rowsTemp:
                    if row not in rows:
                        rows.append(row)
            return render_template("browse.html", rows=rows)
    else:
        #if just clicked on to browse all
        rows = db.execute(
            "SELECT * FROM profile WHERE id NOT IN (:user_id)", user_id=session["user_id"])
        return render_template("browse.html", rows=rows)


@app.route("/events", methods=["POST", "GET"])
def events():
    """Browse projects"""
    if request.method == "POST":
        #means something was searched
        searchVal = request.form.get("search2")
        #filter out reg words from search Arr
        words = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours",
                 "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it",
                 "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom",
                 "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have",
                 "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or",
                 "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between",
                 "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in",
                 "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when",
                 "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
                 "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will",
                 "just", "don", "should", "now"]
        #if there are no searches
        if not searchVal:
            #get all from internship database
            rows = db.execute("SELECT * FROM events")
            return render_template("events.html", rows=rows)
        #if there are items in the search bar
        else:
            searchArr = searchVal.split(" ")
            searchArrCopy = searchArr
            #loop through all words in stop words array
            for word in words:
                #if word in the searched items
                if word in searchArr:
                    #remove it from the copy
                    searchArrCopy.remove(word)
            #define the reg array as the copy array that has been updates
            searchArr = searchArrCopy
            #get rows that correspond with search from internship database
            for val in searchArr:
                rows = []
                rowsTemp = db.execute(
                    "SELECT * FROM events WHERE eventName LIKE ('%' || :search || '%') OR desc LIKE ('%' || :search || '%') OR location LIKE ('%' || :search || '%')", search=val)
                for row in rowsTemp:
                    if row not in rows:
                        rows.append(row)
            return render_template("events.html", rows=rows)
    else:
        #if just clicked on to browse all
        rows = db.execute("SELECT * FROM events")
        return render_template("events.html", rows=rows)

@app.route("/eventsPage", methods=["GET","POST"])
def eventsPage():
    if request.method == "POST":
        row = request.form.get("row")
        #unwraps the dict form the string
        row = ast.literal_eval(row)
        return render_template("eventsPage.html",row=row)

@app.route("/addEvent", methods=["GET", "POST"])
def addEvents():
    """Create Project"""
    if request.method == "POST":
        #get all values
        name = request.form.get("name")
        date = request.form.get("date")
        time = request.form.get("time")
        location = request.form.get("location")
        desc = request.form.get("desc")
        contact = request.form.get("contact")
        info = request.form.get("info")
        #make sure all filled
        if not name or not date or not time or not location or not desc or not contact:
            return error("Requirements Not Satisfied", "/events")
        #insert into database table
        if not info:
            info=None
        db.execute("INSERT INTO events (id,eventName,date,time,location,description,contact,info) VALUES (:user_id,:name,:date,:time,:location,:description,:contact,:info)",
                   user_id=session["user_id"], name=name, date=date, time=time, location=location, description=desc, contact=contact, info=info)
        return redirect("/events")
    else:
        return render_template("addEvent.html")


@app.route("/removeEvents", methods=["POST", "GET"])
def removeEvents():
    """Remove a project"""
    if request.method == "POST":
        #return url
        desc = request.form.get("desc")
        #delete project with same url
        db.execute("DELETE FROM events WHERE description=:desc", desc=desc)
        return redirect("/events")


@app.route("/registered", methods=["POST", "GET"])
def registered():
    """Delete Account"""
    if request.method == "POST":
        group=request.form.get("group")
        return render_template("registered.html",group=group)

@app.route("/resources")
def resources():
    """Delete Account"""
    return render_template("resources.html")

@app.route("/meeting")
def meeting():
    """Delete Account"""
    return render_template("meetings.html")

@app.route("/contact")
def contact():
    """Delete Account"""
    return render_template("contact.html")

@app.route("/deleteAcc")
def deleteAcc():
    """Delete Account"""
    #delete profile, user, and friends
    #profile
    db.execute("DELETE FROM profile WHERE id=:user_id",
               user_id=session["user_id"])
    #users
    db.execute("DELETE FROM user WHERE id=:user_id",
               user_id=session["user_id"])
    #friends
    db.execute("DELETE FROM friends WHERE username1=:user_id OR username2=:user_id",
               user_id=session["user_id"])
    return redirect("/logout")


@app.route("/chatbot", methods=["POST", "GET"])
def chatbot():
    if request.method == "POST":
        #get question
        text = request.form.get("input")
        #possible questions and responces
        QandA = {
            "what exactly does the black lives matter movement want": "BLM’s goal isn’t just about protesting police brutality against Black people, though that’s part of it. The group’s broader mission, according to its website, is to eradicate anti-Blackness and create a world “where every Black person has the social, economic, and political power to thrive.”",
            "isn’t affirmative action by its definition racist": "No. Affirmative action refers to a set of policies and laws that focus on improving opportunities for groups of people, like women and minorities. It gives these historically marginalized groups a seat at the table, so to speak. “Affirmative action is by definition ANTI-racist,” OiYan Poon, an affiliate faculty member in the Higher Education Leadership program at Colorado State University, told CNN in an email interview.",
            "how come white people can’t use the n-word but some black people say it all the time": "There’s no single answer to that question:#Some Black people say the word is too repulsive to use in any context, even by other Black folks. They claim that using it reflects “internalized oppression”: Black people unwittingly accepting racist stereotypes.#But other Black people say they can use the N-word because they have “reclaimed” it and taken the sting out of a slur by using the word as a term of endearment.",
            "is it racist to believe there are some biological differences between races": "The answer may be moot, given that the notion is inaccurate. But there are inherent dangers in perpetuating the idea, says Goodman, the biological anthropologist. If health disparities are attributed to genetics, then they can be dismissed as inevitable, rather than a consequence of “living in a racist society,” he says. “It’s not just incorrect. It’s harmful science.”",
            "why don’t black lives matter protesters also address black on black crime": "Black Lives Matter has protested black-on-black violence. And community groups across the US have addressed it for decades. For example, this summer in Chicago alone civic groups have led peace walks, held neighborhood vigils and mentored Black youth about avoiding crime. BLM and other activist groups actually consider the systemic racism that lands so many African Americans in poor, crime-riddled neighborhoods a form of structural violence.",
            "i’m a white person who wants to help combat racism where do I start": "Educate yourself, Start conversations, Get involved in your community",
            "is there a link between gun violence in black communities and the excessive use of force by police": "Some police officers may have implicit biases when responding to calls in Black neighborhoods, says Brookings Institute Fellow Rashawn Ray.",
            "why are some light-skinned black people prejudiced against darker-skinned people": "The term is known as colorism, and it’s something that’s been affecting Black people – in the US and abroad – for hundreds of years. The definition of colorism is the discrimination of people based on skin shades and is prevalent among people of the same ethnic or racial group. Many Blacks believed that having lighter skin brought more economic benefits and social mobility. If you married someone who could give you lighter-skinned children, they’d have a chance to get better jobs and advance in White-dominated society.",
            "which is the correct terminology: Black, African American or people of color": "It depends. “Black” refers to dark-skinned people of African descent, no matter their nationality. “African American” refers to people who were born in the United States and have African ancestry. Many people use the terms interchangeably. “People of color” was originally meant to be a synonym of “Black,” but its meaning has expanded to accommodate Latinos, Asians, Native Americans and other non-white groups, says Efrén Pérez, a professor of political science and psychology at the University of California Los Angeles. To say you are a person of color is more celebratory and positive than to say you are part of a “minority,” he says.",
            "why is it wrong to say you are blind to color": "In America, most underrepresented minorities will explain that race does matter, as it affects opportunities, perceptions, income, and so much more. When race-related problems arise, colorblindness tends to individualize conflicts and shortcomings, rather than examining the larger picture with cultural differences, stereotypes, and values placed into context. Instead of resulting from an enlightened (albeit well-meaning) position, colorblindness comes from a lack of awareness of racial privilege conferred by Whiteness (Tarca, 2005). White people can guiltlessly subscribe to colorblindness because they are usually unaware of how race affects people of color and American society as a whole.",
            "how am i expected to not be prejudiced when it seems like most crime is committed by black people": "The belief that most crimes are committed by Black people is based on generations of racism in the US. The report found that Black people are more likely to be pulled over by police officers or have drugs planted on them than their White counterparts. Judging from exonerations, innocent Black people are about 12 times more likely to be convicted of drug crimes than innocent White people. So until we start treating everyone equally under the law without preconceived racial biases, it’s hard to conclude that one particular race commits more crime.",
            "why can we have a statue of george washington, who owned slaves, but not robert e. lee": "The short answer is that George Washington fought for the United States and Robert E. Lee fought against it – on the side of a rebellion dedicated to the preservation of slavery.",
            "what is white supremacy": "The belief that white people are superior to those of all other races, especially the black race, and should therefore dominate society.",
            "as a white person, how do I speak to my white friends about their racist beliefs": "Be discreet: it’s best to have your discussions in a private forum or in person one-on-one.#Be curious, not judgmental: Make your discussion sound more like an invitation, instead of an accusation.#Research: it never hurts to have data disproving common misconceptions up your sleeve, but statistics don’t typically change people’s minds.#Stories: share your own moments of realizing you did or said something racist and how you’ve been educating yourself since.#Stay calm: These conversations aren’t meant to be easy. But if you lose your temper, you lose the point.#Be patient: Don’t expect to change anyone’s mind overnight. Instead, view your first talk as a first step.",
            "are all white people racists": "Many people who study race believe that it’s not just White people – everyone, including people of color, is a little bit racist. This is because racism is so ingrained in the US – its history, institutions, and even pop culture – that it’s almost impossible for a White person to not absorb racism.",
            "what’s wrong with all lives matter": "Sadly, our society has a long history of treating some people as less valuable than others. Study after study has confirmed that in equivalent situations, African Americans and Latinos are treated with deadly force far more often than White people, and authorities held less accountable. Unfortunately, racial bias continues to exist even when it is no longer conscious—this too is confirmed by multiple studies. A lack of accountability in the use of force combined with unconscious bias is too often a deadly combination – and one that could place police officers, as well as the public, in great danger. To say that Black lives matter is not to say that other lives do not; indeed, it is quite the reverse—it is to recognize that all lives do matter, and to acknowledge that African Americans are often targeted unfairly (witness the number of African Americans accosted daily for no reason other than walking through a White neighborhood—including some, like young Trayvon Martin, who lost their lives) and that our society is not yet so advanced as to have become truly color blind. This means that many people of goodwill face the hard task of recognizing that these societal ills continue to exist, and that White privilege continues to exist, even though we wish it didn’t and would not have asked for it.",
            "can people of color be racist": "It depends on who you ask, and what your definition of racism is. For some scholars, the answer is no. That’s because they define racism as a structural system that disadvantages nonwhite people because of their race — as opposed to racial prejudice, which is when people exhibit negative attitudes or bias towards others based on race. Others challenge the notion that people of color can’t be racist. Some believe that saying that Black people can’t be racist because they don’t have power ignores the limited power that Black people do have, and suggests that White people have all the power.",
            "what is the difference between being a non-racist and being an anti-racist": "“Non-racist” is the act of not being racist. Being Antiracist is working against racist systems and policies. Kendi says that to be “not racist” or “nonracist” is simply just a mask for racism – since doing nothing contributes to racism. One must be actively working against racism, Ibram X. Kendi says, because there’s no middle ground between being racist or antiracist. So to literally do nothing in the face of the status quo of racial inequity is to essentially support the status quo. It’s like, for instance, what slaveholders wanted people in the North to do in the face of slavery — which was nothing.",
            "what is white privilege": "White privilege refers to the individual and systemic advantages afforded to White people by virtue of them belonging to the dominant ethnic group in society. White privilege is subtle things that often go unnoticed – unless you’re not White. A common argument against the existence of White privilege is that it doesn’t reflect the experiences of White people who grew up poor, or who faced obstacles because of other facets of their identity, such as their gender, religion or sexual orientation. Certainly, there are White people who experience stark poverty, and there are people of color who are extremely wealthy. But acknowledging the existence of white privilege isn’t to say that all White people have had everything handed to them, or that they haven’t overcome significant challenges in life. It’s that with all other things being equal, a White person will still have an advantage because their race won’t be one of the things working against them.",
            "what is racial bias": "Implicit bias, or racist bias, refers to unconscious biases we have about people of other races that affect our decisions and actions.",
            "what is racism": "Prejudice, discrimination, or antagonism directed against a person or people on the basis of their membership of a particular racial or ethnic group, typically one that is a minority or marginalized."
        }
        #overlook words
        words = ["i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours",
                 "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it",
                 "its", "itself", "they", "them", "their", "theirs", "themselves", "which", "who", "whom",
                 "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have",
                 "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or",
                 "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between",
                 "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in",
                 "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when",
                 "where", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
                 "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will",
                 "just", "don", "should", "now"]
        #remove symbols
        symbols=["!","?",".",","]
        #transfer all the lowercase
        text = text.lower()
        #get rid of symbols
        for i in text:
            if i in symbols:
                text = text.replace(i, "")
        #remove overlook words
        text = text.split(" ")
        textCopy = text
        for word in text:
            if word in words:
                textCopy.remove(word)
        text = textCopy
        #define lists needed
        score = []
        keys = []
        #loop through all possible questions
        for key in QandA:
            #add each responce to a list
            keys.append(QandA[key])
            #create a list of each word in one question
            key = key.split(" ")
            counter = 0
            #loop through words in text
            for word in text:
                #if a word searched and a word in possible questions are the same
                if word in key:
                    #increase the counter
                    counter += 1
            #add the counter of total num of words matched to list score at same index
            score.append(counter)
        #figure out the index of the highest score
        if max(score) != 0:
            indices = []
            for num in score:
                if num == max(score):
                    indices.append(score.index(num))
            #if multiple choose one randomly
            final = random.choice(indices)
            #get the responce to the one chosen
            answer = keys[final]
        else:
            answer = "Sorry, would couldn't provide an answer to your question."
        print(answer)
        return render_template("chat.html", answer=answer)
    else:
        return render_template("chat.html", answer=None)


@app.route("/storyWallPost", methods=["POST", "GET"])
def wall():
    if request.method == "POST":
        story = request.form.get("story")
        username = request.form.get("username")
        if not username:
            username = db.execute(
                "SELECT username FROM profile WHERE id = :user_id", user_id=session["user_id"])[0]["username"]
        db.execute("INSERT INTO stories (id,username,story) VALUES (:user_id,:username,:story)", user_id=session["user_id"], username=username,story=story)
        return redirect("/storyWall")
    else:
        return render_template("storyWallPost.html")

@app.route("/storyWall")
def wallPost():
    stories = db.execute("SELECT * FROM stories")
    return render_template("storyWall.html",stories=stories)


    # if __name__ == "__main__":
    #     app.run()
