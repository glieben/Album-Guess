from dotenv import load_dotenv #to hide client and secretid
import os #uses os for tools like conversion
import base64 #some str need to be formatted as base64
import requests #for requests portion of client credentials. need to send a 'post.'
import json #json module.
from random import shuffle
from time import sleep
import tkinter

from PIL import Image, ImageTk
from io import BytesIO #converts into correct filetyope for pillow.

genre = "album_rock"#GENRE SET, spaces as underscores.

app = tkinter.Tk()
app.title("Album Quiz")
app.state("zoomed")
app.config(bg="#5c415a")

input = tkinter.Entry(app, bg="#1c1618", justify="center", font=("Comic Sans", 50), fg="white", insertbackground="white")
input.place(relx=0.5, rely=0.95, anchor="s", relwidth=0.65, relheight=0.1)
input.focus()

imageFrame = tkinter.Label(app)
imageFrame.place(relx=0.5, rely=0.45, anchor='center')

loop = 0
load_dotenv()#just hides secret and client ids from strangers.
order = []
for x in range(50):
    order.append(x)
shuffle(order)

clientId = os.getenv("CLIENT_ID")
secretId = os.getenv("CLIENT_SECRET")

#CLIENT CREDENTIALS WORKFLOW FOR NON LOGINS.
def getToken():
    authStr = clientId + ":" + secretId #authorization request need to be in this format.
    authBytes = authStr.encode("utf-8") #encode into bytes (utf-8)
    authBase64 = str(base64.b64encode(authBytes), "utf-8") #from base64 module, encode bytes into b64, with utf 8 to turn into str.
#request token, get token, then we can use token for 10mins to reqeust from server https://developer.spotify.com/images/documentation/web-api/auth-client-credentials.png

    url = "https://accounts.spotify.com/api/token" #from client credentials
    headers = {
        'Authorization' : 'Basic ' + authBase64,
        'Content-Type' : 'application/x-www-form-urlencoded'
    }

    data = {'grant_type' : 'client_credentials'}
    result = requests.post(url, headers=headers, data=data) #post = send req with headers and body creds.
#response is sent as a json dictionary, shown an example in api, we do not set the parameters.
    jsonResult = result.json() #print this line to debug, it says error invalid client.
    token = jsonResult['access_token']
    return token

def getAuthHeader(token): #api token for future requests.
    return {"Authorization" : "Bearer " + token}
#basic auth is to get token, bearer is user of token. from https://developer.spotify.com/images/documentation/web-api/auth-client-credentials.png

def getArtist(token, genre):
    global loop
    baseUrl = "https://api.spotify.com/v1/search?"
    headers = getAuthHeader(token)
#q=the search

    params = {
        "q" : f"genre:{genre}",
        "type" : "artist",
        "limit" : 1,
        "offset" : order[loop]#max is 1000
    }

    result = requests.get(baseUrl, headers=headers, params=params)
    jsonResult = json.loads(result.content)["artists"]["items"][0]["href"] #parse json result into python.
#limits data output.

#-------------------end of getartist
    artistUrl = jsonResult + "/albums"
    artistParams = {
        "include_groups": "album",
        "limit" : 30
    }

    albumsResult = requests.get(artistUrl, headers=headers, params=artistParams)
    albumsJson = json.loads(albumsResult.content)["items"] #parsing

    def albumPopularity(albums):
        nonlocal pop, albumToUse
        if "live" in albums["name"].lower():
            return 

        url = (albums["href"] + "/tracks")

        params = {
            "limit" : 1
        }

        result = requests.get(url, headers=headers, params=params)
        while result.status_code == 429:
            app.after(500)
            result = requests.get(url, headers=headers, params=params)

        trackUrl = json.loads(result.content)["items"][0]["href"]
        
        trackResult = requests.get(trackUrl, headers=headers)
        trackJson = json.loads(trackResult.content)

        try:
            if trackJson["popularity"] > pop:
                pop = trackJson["popularity"]
                albumToUse = albums
        except: None

        
 
    pop = 0
    albumToUse = None
    for albums in albumsJson:
        albumPopularity(albums)
    
    global answer, imageFrame
    answer = albumToUse["name"].replace(" ", "").lower()
    if "(" in answer:
        index = answer.find("(")
        answer = answer[:index]

    imageUrl = albumToUse["images"][0]["url"]
    imageResponse = requests.get(imageUrl)
    imgData = BytesIO(imageResponse.content)#conv to pil format
    pillowImg = Image.open(imgData)#pil opens

    tkinterImg = ImageTk.PhotoImage(pillowImg)#pil to tkinter format
    imageFrame.config(image=tkinterImg)
    imageFrame.image = tkinterImg#mainloop auto deletes the frame essentially, so this is needed for permanency

    print(answer)
    loop = loop + 1

token = getToken()

getArtist(token, genre)

def enter(event):
    value = input.get().lower()
    value = value.replace(" ", "")
    if len(value) > 0:
        if value == answer:
            getArtist(token, genre)


app.bind("<Return>", enter)

app.mainloop()