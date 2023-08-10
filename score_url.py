import sqlite3,hashlib,os,re
from flask import redirect

def score_url():
        conn = sqlite3.connect('db.sqlite', check_same_thread=False)
        cursor = conn.cursor()
        url_list = cursor.execute('''
        SELECT url FROM urls''').fetchall()

        scores=[]
        regex_list = cursor.execute('''SELECT text, type, score FROM score WHERE type=?''', ("regex",)).fetchall()
        for regex in regex_list:
            for url in url_list:
                located = re.search(regex[0],url[0])
                if located:
                     scores.append(url[0])


        for score in scores:
            print(score)


score_url()


