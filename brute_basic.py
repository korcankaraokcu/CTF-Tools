import requests

session = requests.session()
url = "http://hack.bckdr.in/BATMAN/?st="

for x in range(0, 20):
    r = session.get(url + str(x))
    if r.text.find("Flag is") != -1:
        print(x)

session.close()
