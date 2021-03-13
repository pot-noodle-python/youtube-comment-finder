import os
import time
from urllib.parse import urlparse, parse_qs
import googleapiclient.discovery

class Finder:
    def __init__(self):
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        
        with open('token.txt') as f:
            DEVELOPER_KEY = f.readline()

        self.youtube = googleapiclient.discovery.build(api_service_name, api_version, developerKey = DEVELOPER_KEY)
    
    def find(self, url, term, condition, maxresults):
        valid_comments = []
        first = True
        ID = self.video_id(url)
        print("ID: ", ID)
        if type(ID) == None:
            return None
        else:
            request = self.youtube.videos().list(part="statistics", id="OMAZB31W9nE")
            response = request.execute()
            comment_count = response["items"][0]["statistics"]["commentCount"]
            count = 0
            while True:
                if first:
                    first = False
                    if condition == "Full Comment Text" or condition == "Partial Comment Text":
                        request = self.youtube.commentThreads().list(part="snippet,id", searchTerms = term, maxResults=100, videoId=ID)
                    else:
                        request = self.youtube.commentThreads().list(part="snippet,id", maxResults=100, videoId=ID)
                    response = request.execute()
                else:
                    try:
                        if condition == "Full Comment Text" or condition == "Partial Comment Text":
                            request = self.youtube.commentThreads().list(part="snippet,id", searchTerms = term, maxResults=100, pageToken=response["nextPageToken"], videoId=ID)
                        else:
                            request = self.youtube.commentThreads().list(part="snippet,id", maxResults=100, pageToken=response["nextPageToken"], videoId=ID)
                        response = request.execute()
                    except:
                        break
                
                for comment in response["items"]:
                    count += 1
                    comment_ID = comment['id']
                    comment_dict = {
                        "url" : f"""https://www.youtube.com/watch?v={ID}&lc={comment_ID}""",
                        "author" : comment["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                        "text" : comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                    }

                    if condition == "Full Comment Text":
                        if comment_dict["text"] == term:
                            valid_comments.append(comment_dict)
                    elif condition == "Partial Comment Text":
                        if term in comment_dict["text"]:
                            valid_comments.append(comment_dict)
                    elif condition == "Comment Author":
                        if term == comment_dict["author"]:
                            valid_comments.append(comment_dict)
                    
                    if len(valid_comments) == int(maxresults):
                        return valid_comments
                    
                    print(f"processed {count} of {comment_count} comments")

            return valid_comments
    
    def video_id(self, url):
        # Examples:
        # - http://youtu.be/SA2iWivDJiE
        # - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
        # - http://www.youtube.com/embed/SA2iWivDJiE
        # - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
        query = urlparse(url)
        if query.hostname == 'youtu.be': return query.path[1:]
        if query.hostname in {'www.youtube.com', 'youtube.com'}:
            if query.path == '/watch': return parse_qs(query.query)['v'][0]
            if query.path[:7] == '/embed/': return query.path.split('/')[2]
            if query.path[:3] == '/v/': return query.path.split('/')[2]
        # fail?
        return None
