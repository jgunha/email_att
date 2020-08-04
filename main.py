import os
import email
import imaplib
import requests
from GPSPhoto import gpsphoto
import csv
import hashlib
import urllib
import datetime
import re

#디렉토리 생성
def make_dir(convert_date):
    dir_date = str(datetime.datetime.strftime(convert_date, '%Y-%m-%d'))

    if not(os.path.isdir(dir_date)):
        os.makedirs(os.path.join(dir_date))
    #csv 파일 생성
    if not(os.path.isfile(os.getcwd()+'\\'+dir_date+'\\'+'result.csv')):
        f = open(os.getcwd() + '\\'+dir_date+'\\'+'result.csv', 'w', encoding='utf-8', newline='')
        wr = csv.writer(f)
        wr.writerow(['Number','Data', 'Shortened URL', 'Full URL', 'FileName', 'Latitiude', 'Longitude', 'Altitude', 'MD5', 'SHA1'])
        f.close()
    return dir_date

#정규표현식을 통한 url 추출
def find_url(message):
    p = re.compile("https://bit.ly/[a-zA-Z0-9]*")
    url = p.search(message).group()
    return url

#위도 경도 고도 정보 가져오기
def get_exif(jpg_file):
    return gpsphoto.getGPSData(jpg_file)

#파일 다운로드 & exif 정보 추출
def download(url):
    r = requests.get(url, verify=False)
    filename = urllib.parse.unquote(r.url.split('/')[-1])
    full_url = urllib.parse.unquote(r.url)
    open(os.getcwd() + '\\'+dir+'\\'+filename,'wb').write(r.content)
    info = get_exif(os.getcwd()+'\\'+dir+'\\'+filename)
    if 'Latitude' in info.keys():
        lat = info['Latitude']
        if lat < 0:
            lat = -lat
    else:
        lat = 'N/A'
    if 'Longitude' in info.keys():
        long = info['Longitude']
        if long < 0:
            long = -long
    else:
        long = 'N/A'
    if 'Altitude' in info.keys():
        alt = info['Altitude']
    else:
        alt = 'N/A'
    return full_url, lat, long, alt, filename


#문자열이 인코딩 정보 추출 후, 문자열, 인코딩 얻기
def find_encoding_info(txt):
    info = email.header.decode_header(txt)
    s, encoding = info[0]
    return s, encoding


#해시값 가져오기
def get_hash(file_name):
    BLOCKSIZE = 1024
    hasher = hashlib.md5()
    hasher2 = hashlib.sha1()
    with open(os.getcwd()+'\\'+dir+'\\'+file_name, 'rb') as f:
        buf = f.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            hasher2.update(buf)
            buf = f.read(BLOCKSIZE)
    f.close()
    hash_md5 = hasher.hexdigest()
    hash_sha1 = hasher2.hexdigest()
    return hash_md5, hash_sha1

#csv 작성
def write_csv(url, date, dir):
    full_url, lat, long, alt, file_name = download(url)
    #csv 작성
    f = open(os.getcwd() + '\\'+dir+'\\'+'result.csv', 'r')
    rd = csv.reader(f)
    for url_data in rd:
        #중복 제거
        if url == url_data[2]:
            return
        else:
            if url_data[0] == 'Number':
                row_count = 1
            else:
                row_count = int(url_data[0])+1

    f.close()
    f2 = open(os.getcwd() + '\\'+dir+'\\'+'result.csv', 'a', newline='')
    wr = csv.writer(f2)
    mail_date = datetime.datetime.strftime(date, '%Y-%m-%d %H:%M')
    hash_md5, hash_sha1 = get_hash(file_name)
    wr.writerow([row_count,mail_date ,url, full_url , file_name, lat, long, alt, hash_md5, hash_sha1])

#gmail imap 세션 설정
session = imaplib.IMAP4_SSL('imap.gmail.com')

#로그인
session.login('메일 주소','비밀 번호')


# 계속 동작
while(1):
    # 받은편지함 선택
    session.select('Inbox')

    #특정 발신 이메일, 안읽은 메일만 검색
    result, data = session.uid('search', None, '(UNSEEN)', '(HEADER From "certain email address")')

    #메일 나누기
    all_email = data[0].split()


    for mail in all_email:
        result, data = session.uid('fetch', mail,'(RFC822)')
        raw_email = data[0][1]
        raw_email_string = raw_email.decode('utf-8')
        email_message = email.message_from_string(raw_email_string)

        subject, encode = find_encoding_info(email_message['Subject'])

        message = ''

        if email_message.is_multipart():
            for part in email_message.get_payload():
                if part.get_content_type()=='text/plain':
                    bytes = part.get_payload(decode=True)
                    encode = part.get_content_charset()
                    message = message + str(bytes, encode)
                    convert_date = datetime.datetime.strptime(email_message['Date'], '%a, %d %b %Y %X %z')
                    dir = make_dir(convert_date)
                    url = find_url(message)
                    write_csv(url, convert_date, dir)
        else:
            if email_message.get_content_type() =='text/plain':
                bytes = email_message.get_payload(decode=True)
                encode = email_message.get_content_charset()
                message = str(bytes, encode)
            convert_date = datetime.datetime.strptime(email_message['Date'], '%a, %d %b %Y %X %z')
            dir = make_dir(convert_date)
            url = find_url(message)
            write_csv(url, convert_date, dir)

session.close()
session.logout()