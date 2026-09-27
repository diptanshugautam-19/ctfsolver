import jwt

secret = "password"
payload = {"user": "abu", "role": "admin"}
token = jwt.encode(payload, secret, algorithm="HS256")
print(token)
