#!/usr/local/bin/python
"""Test requests made with facebook 60 day token"""

import json
from api_utilities import apiToolFacebookGraph

"""list of facebook handles for testing"""
facebook_handles = ["JohnnieWalkerUS", "febreze", "BudweiserUSA", "DisneyGames"]

api = apiToolFacebookGraph()

for handle in facebook_handles:
    json_fbpage = api.get_user_info(handle)
    print(json_fbpage.get("username"))
    print(json_fbpage.get("fan_count"))
    print(json_fbpage.get("talking_about_count"))
