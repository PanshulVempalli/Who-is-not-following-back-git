import requests

username = "Sahil002620Q"

def get_all_users(endpoint):
    users = []
    page = 1
    while True:
        # Construct the URL for the specific page
        url = f"https://api.github.com/users/{username}/{endpoint}?per_page=100&page={page}"
        response = requests.get(url).json()
        
        # If the response is empty, we've reached the end of the list
        if not response:
            break
            
        users.extend([u['login'] for u in response])
        page += 1
        
    return set(users)

# Fetch the data
following = get_all_users("following")
followers = get_all_users("followers")

# Calculate the difference using set subtraction
not_following_back = following - followers

print(f"--- Users not following {username} back ({len(not_following_back)}) ---")
for user in sorted(not_following_back):
    print(user)
    
