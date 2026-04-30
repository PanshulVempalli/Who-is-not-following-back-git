import requests

username = "Sahil002620Q"

def get_all_users(endpoint):
    users = []
        page = 1
            while True:
                    url = f"https://api.github.com/users/{username}/{endpoint}?per_page=100&page={page}"
                            response = requests.get(url).json()
                                    if not response:
                                                break
                                                        users.extend([u['login'] for u in response])
                                                                page += 1
                                                                    return set(users)

                                                                    following = get_all_users("following")
                                                                    followers = get_all_users("followers")

                                                                    not_following_back = following - followers

                                                                    print("--- Users not following you back ---")
                                                                    for user in sorted(not_following_back):
                                                                        print(user)
                                                                        