import os
import time
from urllib.parse import urlparse, parse_qs
import googleapiclient.discovery


class Finder:
    def __init__(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"

        with open('token.txt') as f:
            DEVELOPER_KEY = f.readline()

        self.youtube = googleapiclient.discovery.build(
            api_service_name, api_version, developerKey=DEVELOPER_KEY)

    def find(self, url, term, condition, maxresults, filter_comments):
        self.filter_comments = filter_comments
        valid_comments = []
        first = True
        ID = self.video_id(url)
        if type(ID) == None:
            return None
        else:
            search_term = f'"{term}"'
            request = self.youtube.videos().list(part="statistics", id=ID)
            response = request.execute()
            total_comments = response["items"][0]["statistics"]["commentCount"]
            

            #check if max results is less that 
            if not int(maxresults) <= 1/100 * int(total_comments):
                maxresults = 1/100 * int(total_comments)

            while True:
                if first:
                    first = False
                    try:
                        request = self.youtube.commentThreads().list(part="snippet,id", searchTerms=search_term,
                                                                     maxResults=100, videoId=ID, textFormat="plainText")
                        response = request.execute()
                        print(f"searching {term}")
                    except Exception as e:
                        print(e)
                        return self.return_comments(valid_comments, total_comments)
                else:
                    try:
                        request = self.youtube.commentThreads().list(part="snippet,id", maxResults=100,
                                                                     pageToken=response["nextPageToken"], searchTerms=search_term, videoId=ID, textFormat="plainText")
                        response = request.execute()
                        print(f"searching {term}")
                    except Exception as e:
                        print(e)
                        return self.return_comments(valid_comments, total_comments)
                
                for comment in response["items"]:
                    comment_ID = comment['id']
                    comment_dict = {
                        "url": f"""https://www.youtube.com/watch?v={ID}&lc={comment_ID}""",
                        "author": comment["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                        "text": comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
                        "pfp": comment["snippet"]["topLevelComment"]["snippet"]["authorProfileImageUrl"],
                        "likes": comment["snippet"]["topLevelComment"]["snippet"]["likeCount"]
                    }
                    if condition == "Full Comment Text":
                        if term.lower() == comment_dict["text"].lower():
                            valid_comments.append(comment_dict)      
                    elif condition == "Partial Comment Text":
                        if term.lower() in comment_dict["text"].lower():
                            valid_comments.append(comment_dict)

                    if len(valid_comments) >= int(maxresults):
                        return self.return_comments(valid_comments, total_comments)

    def video_id(self, url):
        # Examples:
        # - http://youtu.be/SA2iWivDJiE
        # - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
        # - http://www.youtube.com/embed/SA2iWivDJiE
        # - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
        query = urlparse(url)
        if query.hostname == 'youtu.be':
            return query.path[1:]
        if query.hostname in {'www.youtube.com', 'youtube.com'}:
            if query.path == '/watch':
                return parse_qs(query.query)['v'][0]
            if query.path[:7] == '/embed/':
                return query.path.split('/')[2]
            if query.path[:3] == '/v/':
                return query.path.split('/')[2]
        # fail?
        return None
    
    def return_comments(self, comments, total):
        if self.filter_comments == "Most Likes":
            comments = sorted(comments, key=lambda k: int(k["likes"]))[::-1]
        elif self.filter_comments == "Least Likes":
            comments = sorted(comments, key=lambda k: int(k["likes"]))
        elif self.filter_comments == "Longest Comment":
            comments = sorted(comments, key=lambda k: len(k["text"]))[::-1]
        elif self.filter_comments == "Shortest Comment":
            comments = sorted(comments, key=lambda k: len(k["text"]))
        elif self.filter_comments == "Alphabetical Order":
            comments = sorted(comments, key=lambda k: k["text"])

        
        
        return comments, total

