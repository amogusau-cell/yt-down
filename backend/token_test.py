from jose import jwt

token = jwt.encode({"Text": "baka"}, "veryverysecret", algorithm="HS256")

print(token)