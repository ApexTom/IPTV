import requests
import re

# 原始直播源 URL
SOURCES = [
    "https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/GNTV.m3u",
    "https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/Global.m3u"
]

LOGO_MAP = {
    # === 地方/特色/4K频道 精准修复 ===
    "宁夏文旅": "https://epg.pw/logo/ningxiatv.png",
    "武术频道": "https://epg.pw/logo/wushu.png",
    "河南曲艺": "https://epg.pw/logo/henantv.png",
    "梨园频道": "https://epg.pw/logo/liyuan.png",
    "教科影院": "https://epg.pw/logo/chinasat.png",
    "少儿频道": "https://epg.pw/logo/chinasat.png",
    "经济生活": "https://epg.pw/logo/chinasat.png",
    "苏州娱乐": "https://epg.pw/logo/suzhoutv.png",
    "南京少儿": "https://epg.pw/logo/nanjingtv.png",
    "南宁新闻": "https://epg.pw/logo/nanningtv.png",
    "南宁文旅": "https://epg.pw/logo/nanningtv.png",
    "南宁娱乐": "https://epg.pw/logo/nanningtv.png",
    "河北4K": "https://epg.pw/logo/hebeitv.png",
    "看东方4K": "https://epg.pw/logo/dfws.png",
    "苏州4K": "https://epg.pw/logo/suzhoutv.png",

    # === 港台大台与境外电影/纪实 (HBO / Cinemax / LMN 等) ===
    "Astro AEC": "https://epg.pw/logo/astro_aec.png",
    "无线新闻": "https://epg.pw/logo/tvb_news.png",
    "TVBS亚洲": "https://epg.pw/logo/tvbs_asia.png",
    "NOW新闻": "https://epg.pw/logo/now_news.png",
    "CH5": "https://epg.pw/logo/mediacorp_ch5.png",
    "CH8": "https://epg.pw/logo/mediacorp_ch8.png",
    "CHU": "https://epg.pw/logo/channel_u.png",
    "HBO喜剧": "https://epg.pw/logo/hbo_comedy.png",
    "HBO精选": "https://epg.pw/logo/hbo_signature.png",
    "HBO王牌": "https://epg.pw/logo/hbo_hits.png",
    "Cinemax精选": "https://epg.pw/logo/cinemax.png",
    "LMN": "https://epg.pw/logo/lifetime_movies.png",

    # === 国际 FAST 影视频道 (image_4, 15, 16 对应) ===
    "Romance Movies": "https://epg.pw/logo/pluto_tv_romance_movies.png",
    "Drama Movies": "https://epg.pw/logo/pluto_tv_drama_movies.png",
    "Thriller TV": "https://epg.pw/logo/pluto_tv_thriller.png",
    "Comedy TV": "https://epg.pw/logo/comedy_central.png",
    "Action Movies": "https://epg.pw/logo/pluto_tv_action_movies.png",
    "Comedy Movies": "https://epg.pw/logo/pluto_tv_comedy_movies.png",
    "Thrillers": "https://epg.pw/logo/pluto_tv_thrillers.png",
    "Sci-Fi": "https://epg.pw/logo/pluto_tv_sci_fi.png",
    "Top Movies": "https://epg.pw/logo/pluto_tv_movies.png",
    "MovieSphere": "https://epg.pw/logo/moviesphere.png",
    "Action Hollywood": "https://epg.pw/logo/hollywood_action_movies.png",
    "Mytime Movie": "https://epg.pw/logo/mytime_movie_network.png",
    "Sony One FAVES": "https://epg.pw/logo/sony_one.png",
    "Sony One Dragons' Den": "https://epg.pw/logo/sony_one.png",
    "Sony One Action HITS": "https://epg.pw/logo/sony_one.png",
    "Sony One Comedy HITS": "https://epg.pw/logo/sony_one.png",
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
    "Universal Monsters": "https://epg.pw/logo/universal_monsters.png",

    # === 国际新闻与综合综合 ===
    "GoUSA TV": "https://epg.pw/logo/gousa_tv.png",
    "Inside Outside": "https://epg.pw/logo/inside_outside.png",
    "SBS Drama": "https://epg.pw/logo/sbs_drama.png",
    "New Kmovies": "https://epg.pw/logo/new_kmovies.png",
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
