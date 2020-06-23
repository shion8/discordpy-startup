from discord.ext import commands
import os
import traceback

bot = commands.Bot(command_prefix='/')
token = os.environ['DISCORD_BOT_TOKEN']


@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)


@bot.command()
async def ping(ctx):
    await ctx.send('peko')

@bot.command()
async def usada(ctx):
    await ctx.send('ぺこぺこぺこ')
    
@bot.command()
async def w(ctx):
    await ctx.send('草ぺこ')
    


import time
import requests
import json
import copy
from datetime import datetime, timedelta, timezone

Hololive = { "UCXTpFs_3PqI41qX2d9tL2Rw/featured" : [ "紫咲シオン", "https://yt3.ggpht.com/a/AGF-l79Wv6njnWc-lQDwczBQVLgBIRMD8PJ72ZIPLg=s800-c-k-c0xffffffff-no-rj-mo" ] , 

            
webhook_url_Hololive = '配信開始チャンネル用のwebhookリンク' #ホロライブ配信開始
webhook_url_Hololive_yotei = 'https://discordapp.com/api/webhooks/725131663125905416/n5odmYS0P7T5QvZz06FjLMaFMSsWLIaJeNPPUS0CsSkYY0OqJdE01mqDEES7xGbTBshK' #ホロライブ配信予定
broadcast_data = {} #配信予定のデータを格納

YOUTUBE_API_KEY = [複数のAPI(str型)をリストで管理]

def dataformat_for_python(at_time): #datetime型への変換
    at_year = int(at_time[0:4])
    at_month = int(at_time[5:7])
    at_day = int(at_time[8:10])
    at_hour = int(at_time[11:13])
    at_minute = int(at_time[14:16])
    at_second = int(at_time[17:19])
    return datetime(at_year, at_month, at_day, at_hour, at_minute, at_second)

def replace_JST(s):
    a = s.split("-")
    u = a[2].split(" ")
    t = u[1].split(":")
    time = [int(a[0]), int(a[1]), int(u[0]), int(t[0]), int(t[1]), int(t[2])]
    if(time[3] >= 15):
      time[2] += 1
      time[3] = time[3] + 9 - 24
    else:
      time[3] += 9
    return (str(time[0]) + "/" + str(time[1]).zfill(2) + "/" + str(time[2]).zfill(2) + " " + str(time[3]).zfill(2) + "-" + str(time[4]).zfill(2) + "-" + str(time[5]).zfill(2))

def post_to_discord(userId, videoId):
    haishin_url = "https://www.youtube.com/watch?v=" + videoId #配信URL
    content = "配信中！\n" + haishin_url #Discordに投稿される文章
    main_content = {
        "username": Hololive[userId][0], #配信者名
        "avatar_url": Hololive[userId][1], #アイコン
        "content": content #文章
    }
    requests.post(webhook_url_Hololive, main_content) #Discordに送信
    broadcast_data.pop(videoId)

def get_information():
    tmp = copy.copy(broadcast_data)
    api_now = 0 #現在どのYouTube APIを使っているかを記録
    for idol in Hololive:
        api_link = "https://www.googleapis.com/youtube/v3/search?part=snippet&channelId=" + idol + "&key=" + YOUTUBE_API_KEY[api_now] + "&eventType=upcoming&type=video"
        api_now = (api_now + 1) % len(YOUTUBE_API_KEY) #apiを1つずらす
        aaa = requests.get(api_link)
        v_data = json.loads(aaa.text)
        try:
            for item in v_data['items']:#各配信予定動画データに関して
                broadcast_data[item['id']['videoId']] = {'channelId':item['snippet']['channelId']} #channelIDを格納
            for video in broadcast_data:
                try:
                    a = broadcast_data[video]['starttime'] #既にbroadcast_dataにstarttimeがあるかチェック
                except KeyError:#なかったら
                    aaaa = requests.get("https://www.googleapis.com/youtube/v3/videos?part=liveStreamingDetails&id=" + video + "&key=" + YOUTUBE_API_KEY[api_now])
                    api_now = (api_now + 1) % len(YOUTUBE_API_KEY) #apiを1つずらす
                    vd = json.loads(aaaa.text)
                    print(vd)
                    broadcast_data[video]['starttime'] = vd['items'][0]['liveStreamingDetails']['scheduledStartTime']
        except KeyError: #配信予定がなくて403が出た
            continue
    for vi in broadcast_data:
        if(not(vi in tmp)):
            print(broadcast_data[vi])
            try:
                post_broadcast_schedule(broadcast_data[vi]['channelId'], vi, broadcast_data[vi]['starttime'])
            except KeyError:
                continue

def check_schedule(now_time, broadcast_data):
    for bd in list(broadcast_data):
        try:
            sd_time = dataformat_for_python(broadcast_data[bd]['starttime']) #配信スタート時間をdatetime型で保管
            sd_time += timedelta(hours=9)
            if(now_time >= sd_time):#今の方が配信開始時刻よりも後だったら
                post_to_discord(broadcast_data[bd]['channelId'], bd) #ツイート
        except KeyError:
            continue

def post_broadcast_schedule(userId, videoId, starttime):
    st = starttime.replace('T', ' ')
    sst = st.replace('Z', '')
    ssst = replace_JST(sst)
    haishin_url = "https://www.youtube.com/watch?v=" + videoId #配信URL
    content = ssst + "に配信予定！\n" + haishin_url #Discordに投稿される文章
    main_content = {
        "username": Hololive[userId][0], #配信者名
        "avatar_url": Hololive[userId][1], #アイコン
        "content": content #文章
    }
    requests.post(webhook_url_Hololive_yotei, main_content) #Discordに送信

while True:
    now_time = datetime.now() + timedelta(hours=9)
    if(((now_time.year > 2020) or ((now_time.year == 2020) and (now_time.month >= 6) and (now_time.day >= 22))) and (now_time.minute == 0) and (now_time.hour % 2 == 0)):
        get_information()
    check_schedule(now_time, broadcast_data)
    time.sleep(60)                                        

    
    
    
    
    
bot.run(token)
