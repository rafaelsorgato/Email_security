# Email_security
#### Video Demo:  https://youtu.be/QsUI1hX4OzM
#### Description: This program aims to detect possible advertising or phishing emails, detection is done by using regex or wildcard.

STEPS:
To use, simply download all files, install all requirements in requirements.txt and run main.py.
<br>Open http://127.0.0.1:5000 in your browser to use the page, login:root, pass:123456 (you can change in profile)

USAGE:

FIRST: Choose a word/regex and a score, if this word/regex exists in the email (body, subject or url) it will be scored. Scoring is incremental, if you have more than 1 match in an email all scores will be added together. You can adjust in the "actions" tab how much score you need to quarantine or delete an email.
<img src="https://github.com/rafaelsorgato/images_videos_of_my_projects/blob/main/videos/email_security1.gif" style="width=400px;heigth=400px">

<br>


SECOND: 

In the table tab it is already possible to see the emails that matched the word/regex, by clicking on the subject you can see the email. If the score of this email is 25, it will be sent to the "quarantine" folder of your email, if it is 100, it will be sent to the trash (values that can be changed in the "actions" tab of step 1)
<img src="https://github.com/rafaelsorgato/images_videos_of_my_projects/blob/main/videos/email_security2.gif" style="width=400px;heigth=400px">

<br>

In your email you will see a new folder called "quarantine", all quarantined emails will be in this folder for you to make a decision.
<br> Deleted emails will be sent to trash and will be automatically deleted after 10 days
<img src="https://github.com/rafaelsorgato/images_videos_of_my_projects/blob/main/videos/email_security3.gif" style="width=400px;heigth=400px">
