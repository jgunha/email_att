import os
import email
import imaplib
import time
import requests

#디렉토리 생성
dir = time.strftime('%Y-%m-%d', time.localtime(time.time()))

if not(os.path.isdir(dir)):
    os.makedirs(os.path.join(dir))

#파일 다운로드
def download(url, file_name = None):
    print(url)
    if not file_name:
        file_name = url.split('/')[-1]
    '''with open(dir +'/' + file_name, "wb") as file:
        response = requests.get(url)
        file.write(response.content)'''
    response = requests.get(url)
    print(response.text)

#문자열이 인코딩 정보 추출 후, 문자열, 인코딩 얻기
def find_encoding_info(txt):
    info = email.header.decode_header(txt)
    s, encoding = info[0]
    return s, encoding

#gmail imap 세션 설정
session = imaplib.IMAP4_SSL('imap.gmail.com')

#로그인
session.login('[mail address]','[password]')

#받은편지함 선택
session.select('Inbox')

#특정 발신 이메일, 안읽은 메일만 검색
result, data = session.uid('search', None, '(UNSEEN)', '(HEADER From "[certain email address]]")')

#메일 나누기
all_email = data[0].split()

for mail in all_email:
    result, data = session.uid('fetch', mail,'(RFC822)')
    raw_email = data[0][1]
    raw_email_string = raw_email.decode('utf-8')
    email_message = email.message_from_string(raw_email_string)


    #메일정보
    print('From:', email_message['From'])
    print('Sender:', email_message['Sender'])
    print('To:', email_message['To'])
    print('Date:', email_message['Date'])

    subject, encode = find_encoding_info(email_message['Subject'])
    print('Subject', subject)

    message = ''
    print('[Message]')

    if email_message.is_multipart():
        for part in email_message.get_payload():
            if part.get_content_type()=='text/plain':
                bytes = part.get_payload(decode=True)
                encode = part.get_content_charset()
                message = message + str(bytes, encode)
    else:
        if email_message.get_content_type() =='text/plain':
            bytes = email_message.get_payload(decode=True)
            encode = email_message.get_content_charset()
            message = str(bytes, encode)

    print(message)
    #download(message)

session.close()
session.logout()