import jwt
import time

# Your secret key and algorithm
secret_key = "your_jwt_secret_key"
algorithm = "HS256"


# Payload data
payload = {
    "org_id": 2
}

# Create the token
token = jwt.encode(payload, key=secret_key, algorithm=algorithm)
print(f"Generated Token: {token}")

# Decode the token for verification
decoded_payload = jwt.decode(token, key=secret_key, algorithms=[algorithm])
print(f"Decoded Payload: {decoded_payload}")

