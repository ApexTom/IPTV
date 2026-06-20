import os
import requests
import base64
import json

CHANNEL_LIST = {
    'JUHD': {
        'name': '翡翠台(超高清)',
        'license': '2c045f5adb26d391cc41cd01f00416fa:fc146771a9b096fc4cb57ffe769861be',
        'logo': 'https://epg.yang-1989.eu.org/logo/翡翠台.png'  
    },
    'J': {
        'name': '翡翠台',
        'license': '0958b9c657622c465a6205eb2252b8ed:2d2fd7b1661b1e28de38268872b48480',
        'logo': 'https://epg.yang-1989.eu.org/logo/翡翠台.png'  
    },
    'P': {
        'name': '明珠台',
        'license': 'e04facdd91354deee318c674993b74c1:8f97a629de680af93a652c3102b65898',
        'logo': 'https://epg.yang-1989.eu.org/logo/明珠台.png'  
    },
    'B': {
        'name': 'TVB Plus',
        'license': '56603b65fa1d7383b6ef0e73b9ae69fa:5d9d8e957d2e45d8189a56fe8665aaaa',
        'logo': 'https://epg.yang-1989.eu.org/logo/TVBPlus.png'  
    },
    'C': {
        'name': '無線新聞台',
        'license': '90a0bd01d9f6cbb39839cd9b68fc26bc:51546d1f2af0547f0e961995b60a32a1',
        'logo': 'https://epg.yang-1989.eu.org/logo/無綫新聞台.png'  
    },
    'C3': {
        'name': '互動窗 1',
        'license': 'f07372db27b162d69adf9aa612ae3364:da1631a2b2a836c5b7a3d044a18a4f16',
        'logo': 'https://epg.yang-1989.eu.org/logo/MytvSuper.png'  
    },
    'C2': {
        'name': '互動窗 2',
        'license': '1ba88eacde780c7567255b8b33026ae5:f7df792aab8992b79d72a8d01987ecb5',
        'logo': 'https://epg.yang-1989.eu.org/logo/MytvSuper.png'  
    },
    'CTVE': {
        'name': '娛樂新聞台',
        'license': '6fa0e47750b5e2fb6adf9b9a0ac431a3:a256220e6c2beaa82f4ca5fba4ec1f95',
        'logo': 'https://epg.yang-1989.eu.org/logo/娛樂新聞.png'  
    },
    'TVG': {
        'name': '黃金翡翠台',
        'license': '8fe3db1a24969694ae3447f26473eb9f:5cce95833568b9e322f17c61387b306f',
        'logo': 'https://epg.yang-1989.eu.org/logo/MytvSuper.png'  
    },
    'CWIN': {
        'name': 'myTV SUPER FREE',
        'license': '0737b75ee8906c00bb7bb8f666da72a0:15f515458cdb5107452f943a111cbe89',
        'logo': 'https://epg.yang-1989.eu.org/logo/MytvSuper.png'  
    },
    'CRE': {
        'name': '創世電視',
        'license': 'adef00c5ba927d01642b1e6f3cedc9fb:b45d912fec43b5bbd418ea7ea1fbcb60',
        'logo': 'https://epg.yang-1989.eu.org/logo/創世電視.png'  
    },
    'PCC': {
        'name': '鳳凰衛視中文台',
        'license': '7bca0771ba9205edb5d467ce2fdf0162:eb19c7e3cea34dc90645e33f983b15ab',
        'logo': 'https://epg.yang-1989.eu.org/logo/凤凰中文.png'  
    },
    'PIN': {
        'name': '鳳凰衛視資訊台',
        'license': '83f7d313adfc0a5b978b9efa0421ce25:ecdc8065a46287bfb58e9f765e4eec2b',
        'logo': 'https://epg.yang-1989.eu.org/logo/凤凰资讯.png'  
    },
    'PHK': {
        'name': '鳳凰衛視香港台',
        'license': 'cde62e1056eb3615dab7a3efd83f5eb4:b8685fbecf772e64154630829cf330a3',
        'logo': 'https://epg.yang-1989.eu.org/logo/凤凰香港.png'  
    },
    'CC1': {
        'name': '中央電視台綜合頻道 (港澳版)',
        'license': 'e50b18fee7cab76b9f2822e2ade8773a:2e2e8602b6d835ccf10ee56a9a7d91a2',
        'logo': 'https://epg.yang-1989.eu.org/logo/CCTV1.png'  
    },
    'CC4': {
        'name': '中國中央電視台中文國際頻道',
        'license': '9b2762e6912e2f37a1cad1df9af6dc6e:f4edc1240a3e852661c0607db463a6dd',
        'logo': 'https://epg.yang-1989.eu.org/logo/CCTV4.png'  
    },
    'CCE': {
        'name': '中國中央電視台娛樂頻道',
        'license': 'e173591f7ab25dbc47f6c05abcbb92c7:21c5e4987d1e255d0e171280ad13d815',
        'logo': 'https://epg.yang-1989.eu.org/logo/CCTV娱乐.png'  
    },
    'CCO': {
        'name': '中國中央電視台戲曲頻道',
        'license': '310ee76e894b8361fefdedf5c7b50983:f113fcca4a982e53ba2fc31e7fbf6e2c',
        'logo': 'https://epg.yang-1989.eu.org/logo/CCTV戏曲.png'  
    },
    'CGD': {
        'name': 'CGTN (中國環球電視網)記錄頻道',
        'license': 'b570ae67cb063428b158eb2f91c6d77c:c573dabca79a17f81755c0d4b33384bc',
        'logo': 'https://epg.yang-1989.eu.org/logo/CGTN纪录.png'  
    },
    'CGE': {
        'name': 'CGTN (中國環球電視網)英語頻道',
        'license': '4331903278b673916cc6940a8b8d9e7e:02a409115819de9acd9e907b053e3aa8',
        'logo': 'https://epg.yang-1989.eu.org/logo/CGTN.png'  
    },
    'YNTV': {
        'name': '雲南瀾湄國際衛視',
        'license': '7ec2be4ec767b0a7b23bb9d665c39dab:738f330e2e319ee51ebcb8f2d0614f0a',
        'logo': 'https://epg.yang-1989.eu.org/logo/澜湄国际.png'  
    },
    'AHTV': {
        'name': '安徽廣播電視台國際頻道',
        'license': '460151d2b91a7504c6e7fcdc2e5b3ccc:a2900973ab6de674a8535fd1627f8cce',
        'logo': 'https://epg.yang-1989.eu.org/logo/安徽卫视.png'  
    },
    'BJTV': {
        'name': '北京電視台國際頻道',
        'license': 'a8965a188153cee562c067ba66b0f0fb:c373bfab2e75b979beefbb6b370bcdc2',
        'logo': 'https://epg.yang-1989.eu.org/logo/北京卫视.png'  
    },
    'FJTV': {
        'name': '福建海峽衛視國際頻道',
        'license': '3d5e3a2fd144c5f196cbcb9d037b417d:7be2fcb0ee5efe52ff95b0866f183abb',
        'logo': 'https://epg.yang-1989.eu.org/logo/海峡卫视.png'  
    },
    'HNTV': {
        'name': '湖南電視台國際頻道',
        'license': 'a43885f5c495e3ce5b1162ecb5c35c03:e506caf7a71025850e8823c07a1b29dc',
        'logo': 'https://epg.yang-1989.eu.org/logo/湖南卫视.png'  
    },
    'JSTV': {
        'name': '江蘇電視台國際頻道',
        'license': '5287fd241995f7b097597c4349bea5b5:23398eb21eee12ddb9a9df1dd6373687',
        'logo': 'https://epg.yang-1989.eu.org/logo/江苏卫视.png'  
    },
    'GBTV': {
        'name': '廣東廣播電視台大灣區衛視頻道',
        'license': '25049a9d742e24329e009d2a8a02b4bd:914a1b9442ba239aaa5a8f63c6e10f83',
        'logo': 'https://epg.yang-1989.eu.org/logo/广东卫视.png'  
    },
    'ZJTV': {
        'name': '浙江電視台國際頻道',
        'license': '8799940a2a97f5eb997753983be48fe5:53c4b68330f10e5507d3c0647703031e',
        'logo': 'https://epg.yang-1989.eu.org/logo/浙江卫视.png'  
    },
    'SZTV': {
        'name': '深圳衛視國際頻道',
        'license': 'a265a47191734322dc32596c771887cc:5d19d055e814b3fcc521afe772ecf110',
        'logo': 'https://epg.yang-1989.eu.org/logo/深圳卫视.png'  
    },
    'DTV': {
        'name': '東方衛視國際頻道',
        'license': '9d6a139158dd1fcd807d1cfc8667e965:f643ba9204ebba7a5ffd3970cfbc794c',
        'logo': 'https://epg.yang-1989.eu.org/logo/东方卫视.png'  
    },
    'SVAR': {
        'name': 'SUPER獎門人',
        'license': '977869c9cd6aa804921a2e20724b9e6c:16f76fa19ae5199c920de5cfc1a6ca1e',
        'logo': 'https://epg.yang-1989.eu.org/logo/MytvSuper.png'  
    },
    'SEYT': {
        'name': 'SUPER EYT',
        'license': 'c83f061a8685a0071fc62c65b6ab7af3:b8cf98951b940dca9174230430faf10d',
        'logo': 'https://epg.yang-1989.eu.org/logo/MytvSuper.png'  
    },
    'SFOO': {
        'name': 'SUPER識食',
        'license': '2370118ce3d6fafe17502b0176abf9ae:357c7b5a9d01c25d8e30e46cc396de08',
        'logo': 'https://epg.yang-1989.eu.org/logo/MytvSuper.png'  
    },
    'STRA': {
        'name': 'SUPER識嘆',
        'license': '206a559933b51efbba226fe939040d68:c671ac5afccd7f2d26839e6d9b91d130',
        'logo': 'https://epg.yang-1989.eu.org/logo/MytvSuper.png'  
    },
    'SMUS': {
        'name': 'SUPER Music',
        'license': '0d321fc47b49372df79500c8b7a5e9fc:0c4be4e8f7ccedced7de0b7434493be4',
        'logo': 'https://epg.yang-1989.eu.org/logo/MytvSuper.png'  
    },
    'SGOL': {
        'name': 'SUPER金曲',
        'license': 'd841bf650caca3bf4441a536ae8580d5:c401a71b63dfa7bab1be378605973c2c',
        'logo': 'https://epg.yang-1989.eu.org/logo/MytvSuper.png'  
    },
    'SSIT': {
        'name': 'SUPER煲劇',
        'license': '203638a2e2fd4786190a58393640de54:97e1ec12dda5ee64561e072d9825e3b0',
        'logo': 'https://epg.yang-1989.eu.org/logo/MytvSuper.png'  
    },
    'STVM': {
        'name': 'SUPER劇場',
        'license': 'b6c020768505fa6c7910726b8ca302f0:4b5cba6d27559e6f28a232791f068824',
        'logo': 'https://epg.yang-1989.eu.org/logo/MytvSuper.png'  
    },
    'SDOC': {
        'name': 'SUPER話當年',
        'license': '248ed59a4671da39b3bb71f860760b91:b0bd7d1495e3df963ae21790551094e1',
        'logo': 'https://epg.yang-1989.eu.org/logo/MytvSuper.png'  
    },
    'SSPT': {
        'name': 'SUPER Sports',
        'license': '0d57dc882191c22a9f8185ab7e9a629b:0d2b2edbea04dde8ff880d20e20261ad',
        'logo': 'https://epg.yang-1989.eu.org/logo/MytvSuper.png'  
    }
}

def get_mytvsuper(channel):
    if channel not in CHANNEL_LIST:
        return '频道代号错误'

    api_token = os.getenv('MYTVSUPER_API_TOKEN')
    if not api_token:
        return 'API token 未设置'

    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + api_token,
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Host': 'user-api.mytvsuper.com',
        'Origin': 'https://www.mytvsuper.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5.2 Safari/605.1.15',
        'Referer': 'https://www.mytvsuper.com/',
        'X-Forwarded-For': '210.6.4.148'  # 香港原生IP  210.6.4.148
    }

    params = {
        'platform': 'android_tv',
        'network_code': channel
    }

    url = 'https://user-api.mytvsuper.com/v1/channel/checkout'
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f'请求失败: {e}'

    response_json = response.json()
    profiles = response_json.get('profiles', [])

    play_url = ''
    for profile in profiles:
        if profile.get('quality') == 'high':
            play_url = profile.get('streaming_path', '')
            break

    if not play_url:
        return '未找到播放地址'

    play_url = play_url.split('&p=')[0]

    license_key = CHANNEL_LIST[channel]['license']
    license_data = encode_keys(license_key)  
    print(f"hexTOBase64：{license_data}")
    channel_name = CHANNEL_LIST[channel]['name']
    channel_logo = CHANNEL_LIST[channel]['logo']
    m3u_content = f"#EXTINF:-1 tvg-id=\"{channel}\" tvg-name=\"{channel_name}\" tvg-logo=\"{channel_logo}\",{channel_name}\n"
    m3u_content += "#KODIPROP:inputstream.adaptive.manifest_type=mpd\n"
    m3u_content += "#KODIPROP:inputstream.adaptive.license_type=clearkey\n"
    m3u_content += f"#KODIPROP:inputstream.adaptive.license_key={license_data}\n"
    m3u_content += f"{play_url}\n"

    return m3u_content

def encode_keys(hex_keyi_key):  
    hex_keyid, hex_key = hex_keyi_key.split(':')  
    bin_keyid = bytes.fromhex(hex_keyid)  
    keyid64 = base64.b64encode(bin_keyid).decode('utf-8').rstrip('=')  
    bin_key = bytes.fromhex(hex_key)  
    key64 = base64.b64encode(bin_key).decode('utf-8').rstrip('=')  
  
    
    keys = [{"kty": "oct", "k": key64, "kid": keyid64}]  
  
    
    license = {"keys": keys, "type": "temporary"}  
  
    
    return json.dumps(license)


# 创建或打开文件用于写入
with open('mytvsuper.m3u', 'w', encoding='utf-8') as m3u_file:
    # 写入 M3U 文件的头部
    m3u_file.write('#EXTM3U url-tvg="https://epg.zsdc.eu.org/t.xml.gz" catchup-time="10800" catchup-type="timeshift"\n')

    # 遍历所有频道并写入每个频道的 M3U 内容
    for channel_code in CHANNEL_LIST.keys():
        m3u_content = get_mytvsuper(channel_code)
        m3u_file.write(m3u_content)

print("所有频道的 M3U 播放列表已生成并保存为 'mytvsuper.m3u'。")

