#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2013-06-07 19:28
@author: Yang Junyong <yanunon@gmail.com>

Modified on 2015-01-06 15:28
@author: goodbest <lovegoodbest@gmail.com>

#changelog:
add: download album by id
add: download playlist by id
add: download 320k first
add: download artist albums
add: download mv by id
'''

import md5
import base64
import urllib2
import urllib
import json
import random
import os
import sys
import datetime

#set cookie
cookie_opener = urllib2.build_opener()
cookie_opener.addheaders.append(('Cookie', 'appver=2.0.2'))
cookie_opener.addheaders.append(('Referer', 'http://music.163.com'))
urllib2.install_opener(cookie_opener)

def encrypted_id(id):
    byte1 = bytearray('3go8&$8*3*3h0k(2)2')
    byte2 = bytearray(id)
    byte1_len = len(byte1)
    for i in xrange(len(byte2)):
        byte2[i] = byte2[i]^byte1[i%byte1_len]
    m = md5.new()
    m.update(byte2)
    result = m.digest().encode('base64')[:-1]
    result = result.replace('/', '_')
    result = result.replace('+', '-')
    return result


def search_album_by_name(name):
    search_url = 'http://music.163.com/api/search/get'
    params = {
            's': name,
            'type': 10,
            'offset': 0,
            'sub': 'false',
            'limit': 20
    }
    params = urllib.urlencode(params)
    resp = urllib2.urlopen(search_url, params)
    resp_js = json.loads(resp.read())
    if resp_js['code'] == 200 and resp_js['result']['albumCount'] > 0:
        result = resp_js['result']
        album_id = 0
        if result['albumCount'] > 1:
            for i in range(len(result['albums'])):
                album = result['albums'][i]
                print '[%2d] artist: %-20s\talbum: %-50s\ttracks: %d' % (i+1, album['artist']['name'][:20], album['name'][:50], album['size'])
            select_i = int(raw_input('Select One:'))
            if select_i < 1 or select_i > len(result['albums']):
                print 'error select'
                return None
            else:
                album_id = select_i-1
        return result['albums'][album_id]
    else:
        return None


def search_song_by_name(name):
    search_url = 'http://music.163.com/api/search/get'
    params = {
            's': name,
            'type': 1,
            'offset': 0,
            'sub': 'false',
            'limit': 20
    }
    params = urllib.urlencode(params)
    resp = urllib2.urlopen(search_url, params)
    resp_js = json.loads(resp.read())
    if resp_js['code'] == 200 and resp_js['result']['songCount'] > 0:
        result = resp_js['result']
        song_id = result['songs'][0]['id']
        if result['songCount'] > 1:
            for i in range(len(result['songs'])):
                song = result['songs'][i]
                print '[%2d]song:%s\tartist:%s\talbum:%s' % (i+1,song['name'], song['artists'][0]['name'], song['album']['name'])
            select_i = int(raw_input('Select One:'))
            if select_i < 1 or select_i > len(result['songs']):
                print 'error select'
                return None
            else:
                song_id = result['songs'][select_i-1]['id']
        
        return get_song_by_ID(song_id)

    else:
        return None


def search_artist_by_name(name):
    search_url = 'http://music.163.com/api/search/get'
    params = {
            's': name,
            'type': 100,
            'offset': 0,
            'sub': 'false',
            'limit': 10
    }
    params = urllib.urlencode(params)
    resp = urllib2.urlopen(search_url, params)
    resp_js = json.loads(resp.read())
    if resp_js['code'] == 200 and resp_js['result']['artistCount'] > 0:
        result = resp_js['result']
        artist_id = 0
        if result['artistCount'] > 1:
            for i in range(len(result['artists'])):
                artist = result['artists'][i]
                print '[%2d] artist: %s \t albums: %d' % (i+1, artist['name'], artist['albumSize'])
            select_i = int(raw_input('Select One:'))
            if select_i < 1 or select_i > len(result['artists']):
                print 'error select'
                return None
            else:
                return result['artists'][select_i-1]
        else:
            return result['artists'][artist_id]
            
    else:
        return None


def get_song_by_ID(songID):
    detail_url = 'http://music.163.com/api/song/detail?ids=[%d]' % songID
    resp = urllib2.urlopen(detail_url)
    song_js = json.loads(resp.read())
    return song_js['songs'][0]


def get_mv_by_ID(mvID):
    detail_url = 'http://music.163.com/api/mv/detail?id=%d' % mvID
    resp = urllib2.urlopen(detail_url)
    mv = json.loads(resp.read())
    return mv['data']


def get_album_songs_by_ID(albumID):
    url = 'http://music.163.com/api/album/%d/' % albumID
    resp = urllib2.urlopen(url)
    albumInfo= json.loads(resp.read())
    return albumInfo


def get_playlist_songs_by_ID(playlistID):
    url = 'http://music.163.com/api/playlist/detail?id=%d' % playlistID
    resp = urllib2.urlopen(url)
    songs = json.loads(resp.read())
    return songs['result']


def get_artist_albums_by_ID(artistID):
    albums = []
    offset = 0
    while True:
        url = 'http://music.163.com/api/artist/albums/%d?offset=%d&limit=50' % (artistID, offset)
        resp = urllib2.urlopen(url)
        tmp_albums = json.loads(resp.read())
        albums.extend(tmp_albums['hotAlbums'])
        if tmp_albums['more'] == True:
            offset += 50
        else:
            break
    return albums


def save_song_to_disk(song, folder):
    name = song['name']
    if song['position']:
        fpath = os.path.join(folder, '%02d-%s.mp3' %(song['position'], name))
    else:
        fpath = os.path.join(folder, name+'.mp3')
    if os.path.exists(fpath):
        return
    
    quality=0
    if song['hMusic']:
        song_dfsId = str(song['hMusic']['dfsId'])
        quality=320
    elif song['mMusic']:
        song_dfsId = str(song['mMusic']['dfsId'])
        quality=160
    else:
        song_dfsId = str(song['lMusic']['dfsId'])
        quality=96
    url = 'http://m%d.music.126.net/%s/%s.mp3' % (random.randrange(1, 3), encrypted_id(song_dfsId), song_dfsId)
    print 'saving song %s, %skbps' %(song['name'], quality)
    #print '%s\t%s' % (url, name)
    #return
    resp = urllib2.urlopen(url)
    data = resp.read()
    f = open(fpath, 'wb')
    f.write(data)
    f.close()


def save_mv_to_disk(mv, folder):
    name = mv['name']
    fpath = os.path.join(folder, '%s-%s.mp4' %(mv['artistName'], name))
    if os.path.exists(fpath):
        return
    
    best_bitrate=0
    for bitrate in mv['brs'].keys():
        if int(bitrate) > int(best_bitrate):
            best_bitrate = bitrate
    video_url = mv['brs'][best_bitrate]
    print 'saving mv %s, %sp' %(name, best_bitrate)

    resp = urllib2.urlopen(video_url)
    data = resp.read()
    f = open(fpath, 'wb')
    f.write(data)
    f.close()


def download_song_by_search(name, folder='.'):
    song = search_song_by_name(name)
    if not song:
        print 'Not found ' + name
        return

    if not os.path.exists(folder):
        os.makedirs(folder)
    save_song_to_disk(song, folder)


def download_song_by_ID(songID, folder='.'):
    song=get_song_by_ID(songID)
    save_song_to_disk(song, folder)
    

def download_mv_by_ID(mvID, folder='.'):
    mvInfo=get_mv_by_ID(mvID)
    save_mv_to_disk(mvInfo, folder)


def download_album_by_search(name, folder='.'):
    album = search_album_by_name(name)
    if not album:
        print 'Not found ' + name
        return
    download_album_by_ID(album['id'], folder)


def download_album_by_artist(name, folder='.'):
    artistInfo= search_artist_by_name(name)
    download_album_by_artist_ID(artistInfo['id'], folder)


def download_album_by_artist_ID(artistID, folder='.'):
    albums = get_artist_albums_by_ID(artistID)
    if len(albums) > 1:
        for i in range(len(albums)):
            album = albums[i]
            print '[%2d] albums: %-40s\t tracks: %d\t date: %s' % (i+1, album['name'][:40], album['size'], datetime.datetime.fromtimestamp(album['publishTime']/1000).strftime('%Y-%m-%d'))
        select_i = str(raw_input('Select album: (seperate album number by space for multiple downloads; input 0 to download all\n')).strip()
        if select_i == '0':
            downlist=range(1,len(albums)+1)
        else:
            downlist= [int(j) for j in select_i.split(' ')]
            for j in downlist:
                if j < 0 or j > len(albums):
                    print 'error select'
                    return None
    else:
        downlist=[1]
    print 'Start downloading %d albums' % len(downlist)
    for album in downlist:
        download_album_by_ID(albums[album-1]['id'], folder)


def download_album_by_ID(albumID, folder='.'):
    albumInfo = get_album_songs_by_ID(albumID)
    if not albumInfo['album']:
        print 'Not found '
        return
    
    name = albumInfo['album']['name']
    artist = albumInfo['album']['artist']['name']
    folder = os.path.join(folder, artist+'-'+name)

    if not os.path.exists(folder):
        os.makedirs(folder)

    songs = albumInfo['album']['songs']
    print 'saving total %s songs....' %len(songs)
    for song in songs:
        save_song_to_disk(song, folder)


def download_playlist_by_ID(playlistID, folder='.'):
    playlistInfo = get_playlist_songs_by_ID(playlistID)
    if not playlistInfo:
        print 'Not found'
        return
    folder = os.path.join(folder, 'Playlist-'+str(playlistInfo['name']))

    if not os.path.exists(folder):
        os.makedirs(folder)
    songs=playlistInfo['tracks']
    print 'saving total %s songs....' %len(songs)
    for song in songs:
        save_song_to_disk(song, folder)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'parameter help:'
        print 'python NeteaseCloudMusic.py option1 option2 [option3]'
        print 'option1: type; option2: query string; option3: file path'
        print 'search song  & download:     option1 = song    , option2 = <song Name> '
        print 'search album & download:     option1 = album   , option2 = <album Name> '
        print 'search artist& download:     option1 = art     , option2 = <artist Name> '
        print 'download song  by ID:        option1 = sid     , option2 = <song ID> '
        print 'download mv    by ID:        option1 = mvid    , option2 = <mv ID> '
        print 'download album by ID:        option1 = albumid , option2 = <album ID> '
        print 'download album by artist ID: option1 = artid   , option2 = <artist ID> '
        print 'download playlist by ID:     option1 = pid     , option2 = <playlist ID> '
        
        sys.exit(0)
        
    if sys.argv[1]=='albumid':
        if len(sys.argv)==3:
            download_album_by_ID(int(sys.argv[2]))
        else:
            download_album_by_ID(int(sys.argv[2]), sys.argv[3])
        
    elif sys.argv[1]=='album':
        if len(sys.argv)==3:
            download_album_by_search(sys.argv[2])
        else:
            download_album_by_search(sys.argv[2], sys.argv[3])
            
    elif sys.argv[1]=='art':
        if len(sys.argv)==3:
            download_album_by_artist(sys.argv[2])
        else:
            download_album_by_artist(sys.argv[2], sys.argv[3])
    
    elif sys.argv[1]=='artid':
        if len(sys.argv)==3:
            download_album_by_artist_ID(int(sys.argv[2]))
        else:
            download_album_by_artist_ID(int(sys.argv[2]), sys.argv[3])
            
    elif sys.argv[1]=='pid':
        if len(sys.argv)==3:
            download_playlist_by_ID(int(sys.argv[2]))
        else:
            download_playlist_by_ID(int(sys.argv[2]), sys.argv[3])
            
    elif sys.argv[1]=='song':
        if len(sys.argv)==3:
            download_song_by_search(sys.argv[2])
        else:
            download_song_by_search(sys.argv[2], sys.argv[3])

    elif sys.argv[1]=='sid':
        if len(sys.argv)==3:
            download_song_by_ID(int(sys.argv[2]))
        else:
            download_song_by_ID(int(sys.argv[2]), sys.argv[3])

    elif sys.argv[1]=='mvid':
        if len(sys.argv)==3:
            download_mv_by_ID(int(sys.argv[2]))
        else:
            download_mv_by_ID(int(sys.argv[2]), sys.argv[3])
    else:
        print 'give correct parameter'
        sys.exit(0)
    
    