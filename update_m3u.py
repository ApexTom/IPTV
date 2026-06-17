import requests
import re

# 原始直播源 URL
SOURCES = [
    "https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/GNTV.m3u",
    "https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/Global.m3u"
]

# 全面扩充后的台标自定义映射表（覆盖国内地方、港台、国际、欧美轮播台）
LOGO_MAP = {
    # ==========================================
    # 1. 港台、国际大台与欧美影视电影 (image_10, 11, 14, 15)
    # ==========================================
    "HBO喜剧": "https://epg.pw/logo/hbo_comedy.png",
    "HBO精选": "https://epg.pw/logo/hbo_signature.png",
    "HBO王牌": "https://epg.pw/logo/hbo_hits.png",
    "Cinemax精选": "https://epg.pw/logo/cinemax.png",
    "LMN": "https://epg.pw/logo/lifetime_movies.png",
    "Universal Monsters": "https://epg.pw/logo/universal_monsters.png",
    "Action Movies": "https://epg.pw/logo/pluto_tv_action_movies.png",
    "Comedy Movies": "https://epg.pw/logo/pluto_tv_comedy_movies.png",
    "Drama Movies": "https://epg.pw/logo/pluto_tv_drama_movies.png",
    "Romance Movies": "https://epg.pw/logo/pluto_tv_romance_movies.png",
    "Sci-Fi": "https://epg.pw/logo/pluto_tv_sci_fi.png",
    "Thrillers": "https://epg.pw/logo/pluto_tv_thrillers.png",
    "Top Movies": "https://epg.pw/logo/pluto_tv_movies.png",
    "MovieSphere": "https://epg.pw/logo/moviesphere.png",
    "Action Hollywood": "https://epg.pw/logo/hollywood_action_movies.png",
    "Mytime Movie": "https://epg.pw/logo/mytime_movie_network.png",
    
    # ==========================================
    # 2. 国际综合、纪实与新闻频道 (image_10, 11, 12, 13)
    # ==========================================
    "GoUSA TV": "https://epg.pw/logo/gousa_tv.png",
    "Inside Outside": "https://epg.pw/logo/inside_outside.png",
    "SBS Drama": "https://epg.pw/logo/sbs_drama.png",
    "New Kmovies": "https://epg.pw/logo/new_kmovies.png",
    "Great British Menu": "https://epg.pw/logo/great_british_menu.png",
    "Icon Film Channel": "https://epg.pw/logo/icon_film_channel.png",
    "Popflix": "https://epg.pw/logo/popflix.png",
    "LG 1 Film": "https://epg.pw/logo/lg_channels.png",
    "LG 1 Spotlight": "https://epg.pw/logo/lg_channels.png",
    "LG 1": "https://epg.pw/logo/lg_channels.png",
    "Universal Action": "https://epg.pw/logo/universal_action.png",
    "Universal Western": "https://epg.pw/logo/universal_westerns.png",
    "Universal Crime": "https://epg.pw/logo/universal_crime.png",
    "Universal Movies": "https://epg.pw/logo/universal_movies.png",
    "Sony One FAVES": "https://epg.pw/logo/sony_one.png",
    "Sony One Dragons": "https://epg.pw/logo/sony_one.png",
    "Sony One Action": "https://epg.pw/logo/sony_one.png",
    "Sony One Comedy": "https://epg.pw/logo/sony_one.png",
    "ION Plus": "https://epg.pw/logo/ion_plus.png",
    "History Hit": "https://epg.pw/logo/history_hit.png",
    "Kartoon Channel": "https://epg.pw/logo/kartoon_channel.png",
    "WION": "https://epg.pw/logo/wion.png",
    "Newsy": "https://epg.pw/logo/scripps_news.png",
    "Redbull": "https://epg.pw/logo/red_bull_tv.png",
    "HollyWire": "https://epg.pw/logo/hollywire.png",
    "Wild Earth": "https://epg.pw/logo/wildearth.png",
    "Global News": "https://epg.pw/logo/global_news.png",
    "NBC News Now": "https://epg.pw/logo/nbc_news_now.png",
    "One American News": "https://epg.pw/logo/oan.png",
    "Big Ten Network": "https://epg.pw/logo/btn.png",
    "GB News": "https://epg.pw/logo/gb_news.png",
    "RT News": "https://epg.pw/logo/rt.png",
    "NEWSMAX": "https://epg.pw/logo/newsmax.png",

    # ==========================================
    # 3. 国内地方频道精准修复 (image_12, 13, 14, 15)
    # ==========================================
    "宁夏文旅": "https://epg.pw/logo/ningxiatv.png",
    "梨园频道": "https://epg.pw/logo/liyuan.png",
    "武术频道": "https://epg.pw/logo/wushu.png",
    "河南曲艺": "https://epg.pw/logo/henantv.png",
    "教科影院": "https://epg.pw/logo/chinasat.png",
    "民生休闲": "https://epg.pw/logo/zhejiangtv.png",
    "浙江新闻": "https://epg.pw/logo/zhejiangtv.png",
    "少儿频道": "https://epg.pw/logo/chinasat.png",  # 地方通用少儿
    "经济生活": "https://epg.pw/logo/chinasat.png",  # 地方通用经济
    "苏州娱乐": "https://epg.pw/logo/suzhoutv.png",
    "南京少儿": "https://epg.pw/logo/nanjingtv.png",
    "南宁新闻": "https://epg.pw/logo/nanningtv.png",
    "南宁文旅": "https://epg.pw/logo/nanningtv.png",
    "南宁娱乐": "https://epg.pw/logo/nanningtv.png",
    "河北4K": "https://epg.pw/logo/hebeitv.png",
    "看东方4K": "https://epg.pw/logo/dfws.png",
    "苏州4K": "https://epg.pw/logo/suzhoutv.png",
}



def fetch_and_merge():
    merged_channels = []
    seen_urls = set()  # 用于根据播放链接去重

    for url in SOURCES:
        try:
            print(f"正在下载源: {url}")
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                continue
            
            lines = response.text.splitlines()
            current_extinf = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("#EXTM3U"):
                    continue
                
                if line.startswith("#EXTINF:"):
                    current_extinf = line
                elif current_extinf and (line.startswith("http://") or line.startswith("https://") or line.startswith("rtmp://")):
                    if line not in seen_urls:
                        seen_urls.add(line)
                        merged_channels.append((current_extinf, line))
                    current_extinf = None
        except Exception as e:
            print(f"下载/解析源失败 {url}: {e}")
            
    return merged_channels

def process_and_save(channels, output_file="YueChan.m3u"):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for extinf, url in channels:
            logo_url = None
            
            # --- 1. 正则匹配 CCTV 系列，去除短横线、规范化显示名称并赋台标 ---
            cctv_match = re.search(r'CCTV[-_ ]*(\d+[\s\+\w\u4e00-\u9fa5]*)', extinf, re.IGNORECASE)
            if cctv_match:
                raw_num = re.search(r'\d+\+?', cctv_match.group(1))
                if raw_num:
                    num_str = raw_num.group(0)
                    cctv_num = num_str.replace('+', 'plus')
                    logo_url = f'https://epg.pw/logo/cctv{cctv_num}.png'
                    
                    # 清洗频道显示名称，把 "CCTV-1综合" 规范化为 "CCTV1"
                    extinf = re.sub(r',CCTV[-_ ]*\d+.*$', f',CCTV{num_str}', extinf, flags=re.IGNORECASE)

            # --- 2. 匹配境外/特殊频道的 LOGO_MAP ---
            if not logo_url:
                for keyword, l_url in LOGO_MAP.items():
                    if keyword in extinf:
                        logo_url = l_url
                        break
            
            # --- 3. 注入 tvg-logo ---
            if logo_url:
                extinf = re.sub(r'tvg-logo="[^"]*"', '', extinf)
                extinf = extinf.replace('#EXTINF:-1', f'#EXTINF:-1 tvg-logo="{logo_url}"')
                extinf = re.sub(r'\s+', ' ', extinf).replace(' ,', ',')
            
            f.write(f"{extinf}\n{url}\n")
            
    print(f"合并完成！已成功保存至 {output_file}，共 {len(channels)} 个频道。")

if __name__ == "__main__":
    channels = fetch_and_merge()
    if channels:
        process_and_save(channels)
    else:
        print("未获取到任何有效的直播源数据。")
