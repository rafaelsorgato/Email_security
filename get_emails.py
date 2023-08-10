



def extract_data():
    import re, win32com.client
    from urllib.parse import unquote
    import sqlite3
    import hashlib
    from time import sleep
    import pythoncom
    pythoncom.CoInitialize()

    outlook = win32com.client.Dispatch('outlook.application')

    mapi = outlook.GetNamespace("MAPI")


    conn = sqlite3.connect('db.sqlite' )
    cursor = conn.cursor()
    while True:
        subject_regex = cursor.execute('''SELECT text, type, score FROM score WHERE type=?''', ("subject",)).fetchall()
        subject_regex = [list(tupla) for tupla in subject_regex]
        body_regex = cursor.execute('''SELECT text, type, score FROM score WHERE type=?''', ("body",)).fetchall()
        body_regex = [list(tupla) for tupla in body_regex]
        url_regex = cursor.execute('''SELECT text, type, score FROM score WHERE type=?''', ("url",)).fetchall()
        url_regex = [list(tupla) for tupla in url_regex]

        quarantine = cursor.execute('''SELECT score FROM action WHERE action=?''', ("quarantine",)).fetchone()
        delete = cursor.execute('''SELECT score FROM action WHERE action=?''', ("delete",)).fetchone()

        root_folder = mapi.Folders.Item(1)
        quarantine_folder = root_folder.Folders("Quarantine") 
        inbox = mapi.GetDefaultFolder(6)
        messages = inbox.Items
        messages.Sort("[ReceivedTime]", True)

        for x in range(100):
            hash_list = cursor.execute("SELECT hash FROM emails")
            hash_list = [row[0] for row in cursor.fetchall()]
            sender = messages[x].SenderEmailAddress
            if (str(hashlib.sha256((messages[x].HTMLbody).encode('utf-8')).hexdigest())+str(messages[x].ReceivedTime.timestamp())) not in hash_list:
                subject_score = 0
                body_score = 0   
                for regex in subject_regex:
                    if re.search(str(regex[0]),str(messages[x].subject), flags=re.IGNORECASE):
                        subject_score = subject_score + regex[2]
                for regex in body_regex:
                    body_without_url = re.sub('http.?:\/\/\S+','',messages[x].body, flags=re.IGNORECASE)
                    if re.search(regex[0],body_without_url, flags=re.IGNORECASE):
                        body_score = body_score + regex[2]
                    body_without_url = ''
                cursor.execute("SELECT MAX(id) FROM emails")    
                emails_last_id = cursor.fetchone()[0]
                if not emails_last_id: emails_last_id=0 
                cursor.execute('''
                        INSERT INTO emails (id, subject, body, body_score, subject_score, hash, sender)
                        VALUES (?,?,?,?,?,?,?)
                        ''', (emails_last_id+1,str(messages[x]), messages[x].HTMLbody, body_score,subject_score,(str(hashlib.sha256((messages[x].HTMLbody).encode('utf-8')).hexdigest())+str(messages[x].ReceivedTime.timestamp())),sender,))
                conn.commit() 

                cursor.execute("SELECT MAX(id) FROM emails")    
                emails_last_id = cursor.fetchone()[0]

                pattern = re.compile(r'url=(.*?)&')  # Padrão para encontrar URLs
                url_list = re.findall(pattern, messages[x].body)
                for i in range(len(url_list)):
                    url_list[i] = unquote(url_list[i])
                pattern = re.compile(r'(http.?://\S+)')
                http_list = re.findall(pattern, messages[x].body)
                for i in range(len(http_list)):
                    http_list[i] = unquote(http_list[i])
                url_list.extend(http_list)
                url_list = list(set(url_list))
                higher_score = 0
                for url in url_list:
                    url_score = 0
                    for regex in url_regex:
                        if re.search(regex[0],url):
                            url_score = url_score + regex[2]
                            cursor.execute('''
                                    INSERT INTO urls (url, email_id, score)
                                    VALUES (?,?,?)
                                    ''', (url,emails_last_id, url_score,))
                            conn.commit() 
                    
                    if url_score > higher_score :
                        higher_score = url_score               
                if higher_score>0:
                    cursor.execute('''
                        UPDATE emails SET url_score = ? WHERE id = ?
                        ''', (higher_score, emails_last_id,))
                elif higher_score == 0 and subject_score == 0 and body_score == 0:
                    cursor.execute('''
                        DELETE FROM emails WHERE id = ?
                        ''', (emails_last_id,))
                    cursor.execute('''
                        DELETE FROM urls WHERE email_id = ?
                        ''', (emails_last_id,))
                elif higher_score==0 and (subject_score != 0 or body_score != 0):
                    cursor.execute('''
                        UPDATE emails SET url_score = ? WHERE id = ?
                        ''', (higher_score, emails_last_id,))
                conn.commit() 
                try:
                    root_folder.Folders.Add("Quarantine")
                except:
                    pass
                try:
                    if higher_score >= delete[0] or subject_score >= delete[0] or body_score >= delete[0]:
                        messages[x].Delete()
                        cursor.execute('''
                        UPDATE emails SET status = ? WHERE id = ?
                        ''', ("Deleted", emails_last_id,))
                        conn.commit() 
                    elif higher_score >= quarantine[0] or subject_score >= quarantine[0] or body_score >= quarantine[0]:
                        messages[x].Move(quarantine_folder)
                        cursor.execute('''
                        UPDATE emails SET status = ? WHERE id = ?
                        ''', ("Quarantined", emails_last_id,))
                        conn.commit() 
                    elif (higher_score < quarantine[0] and subject_score < quarantine[0] and body_score < quarantine[0]) and (higher_score > 0 or subject_score > 0 or body_score > 0):
                        messages[x].Move(quarantine_folder)
                        cursor.execute('''
                        UPDATE emails SET status = ? WHERE id = ?
                        ''', ("Only scored", emails_last_id,))
                        conn.commit() 
                except:
                    pass

        sleep(60)
