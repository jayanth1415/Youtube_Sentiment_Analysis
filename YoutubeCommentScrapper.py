import csv
import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from collections import Counter
import warnings

warnings.filterwarnings('ignore')


#  YouTube API Configuration


DEVELOPER_KEY = "AIzaSyCAawUNp0r_wZjBeb_x4rS1sq8DoVEJ0xA"
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

youtube = build(
    YOUTUBE_API_SERVICE_NAME,
    YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY
)


#  Advanced Fake Detection


def detect_fake_comment(comment, username, duplicate_count):
    score = 0
    comment_lower = comment.lower()

    # Rule 1: Suspicious links
    if "http" in comment_lower or "www" in comment_lower:
        score += 3

    # Rule 2: Spam keywords
    spam_keywords = [
        "earn money", "subscribe back", "check my channel",
        "free gift", "dm me", "telegram", "whatsapp",
        "bitcoin", "investment"
    ]
    for word in spam_keywords:
        if word in comment_lower:
            score += 2

    # Rule 3: Too many special characters/emojis
    if len(re.findall(r'[^\w\s]', comment)) > 8:
        score += 2

    # Rule 4: Very short generic comments
    if len(comment.split()) <= 2:
        score += 1

    # Rule 5: Duplicate comment
    if duplicate_count > 1:
        score += 2

    # Rule 6: Suspicious username (numbers-heavy)
    if len(re.findall(r'\d', username)) > 4:
        score += 1

    # Final Classification
    if score >= 5:
        return "Fake", score
    elif score >= 2:
        return "Suspicious", score
    else:
        return "Real", score



# 📺 Get Channel ID


def get_channel_id(video_id):
    response = youtube.videos().list(
        part='snippet',
        id=video_id
    ).execute()

    return response['items'][0]['snippet']['channelId']



#  Fetch Comments +  Analysis


def save_video_comments_to_csv(video_id):
    comments = []

    results = youtube.commentThreads().list(
        part='snippet',
        videoId=video_id,
        textFormat='plainText',
        maxResults=100
    ).execute()

    while results:
        for item in results['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            username = item['snippet']['topLevelComment']['snippet']['authorDisplayName']
            comments.append([username, comment])

        if 'nextPageToken' in results:
            results = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                textFormat='plainText',
                pageToken=results['nextPageToken'],
                maxResults=100
            ).execute()
        else:
            break

    # Detect duplicate comments
    comment_texts = [c[1] for c in comments]
    duplicates = Counter(comment_texts)

    enhanced_comments = []
    fake_count = 0

    for username, comment in comments:
        duplicate_count = duplicates[comment]
        label, score = detect_fake_comment(comment, username, duplicate_count)

        if label == "Fake":
            fake_count += 1

        enhanced_comments.append([
            username,
            comment,
            duplicate_count,
            score,
            label
        ])

    filename = video_id + "_analysis.csv"

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            'Username',
            'Comment',
            'Duplicate_Count',
            'Fake_Score',
            'Fake_Detection'
        ])
        for row in enhanced_comments:
            writer.writerow(row)

    return filename



#  Get Video Statistics


def get_video_stats(video_id):
    try:
        response = youtube.videos().list(
            part='statistics',
            id=video_id
        ).execute()

        return response['items'][0]['statistics']

    except HttpError as error:
        print(f'An error occurred: {error}')
        return None



#  Get Channel Information


def get_channel_info(youtube, channel_id):
    try:
        response = youtube.channels().list(
            part='snippet,statistics,brandingSettings',
            id=channel_id
        ).execute()

        return {
            'channel_title': response['items'][0]['snippet']['title'],
            'video_count': response['items'][0]['statistics']['videoCount'],
            'channel_logo_url': response['items'][0]['snippet']['thumbnails']['high']['url'],
            'channel_created_date': response['items'][0]['snippet']['publishedAt'],
            'subscriber_count': response['items'][0]['statistics']['subscriberCount'],
            'channel_description': response['items'][0]['snippet']['description']
        }

    except HttpError as error:
        print(f'An error occurred: {error}')
        return None