import requests
import re

# 原始直播源 URL
SOURCES = [
    "https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/GNTV.m3u",
    "https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/Global.m3u"
]

# 扩展后的境外/特色频道/港台频道 台标自定义映射表
LOGO_MAP = {
    # === [港台与东南亚频道] ===
    "无线新闻": "https://epg.pw/logo/tvb_news.png",
    "TVBS亚洲": "https://epg.pw/logo/tvbs_asia.png",
    "NOW新闻": "https://epg.pw/logo/now_news.png",
    "Astro AEC": "https://epg.pw/logo/astro_aec.png",
    "CH5": "https://epg.pw/logo/mediacorp_ch5.png",
    "CH8": "https://epg.pw/logo/mediacorp_ch8.png",
    "CHU": "https://epg.pw/logo/channel_u.png",

    # === [HBO 与 经典电影/纪录片] ===
    "HBO喜剧": "https://epg.pw/logo/hbo_comedy.png",
    "HBO Comedy": "https://epg.pw/logo/hbo_comedy.png",
    "HBO": "https://epg.pw/logo/hbo.png",
    "国家地理": "https://epg.pw/logo/national_geographic.png",
    "Discovery": "https://epg.pw/logo/discovery.png",
    "探索频道": "https://epg.pw/logo/discovery.png",
    
    # === [国际 FAST / 影视轮播台 (image_5 对应)] ===
    "Romance Movies": "https://epg.pw/logo/pluto_tv_romance_movies.png",
    "Drama Movies": "https://epg.pw/logo/pluto_tv_drama_movies.png",
    "Thriller TV": "https://epg.pw/logo/pluto_tv_thriller.png",
    "Comedy TV": "https://epg.pw/logo/comedy_central.png",
    "Sony One FAVES": "https://epg.pw/logo/sony_one.png",
    "Sony One Dragons": "https://epg.pw/logo/sony_one.png", # 兼容 Sony One Dragons' Den
    "Great British Menu": "https://epg.pw/logo/great_british_menu.png",
    "Icon Film": "https://epg.pw/logo/icon_film_channel.png",
    "Popflix": "https://epg.pw/logo/popflix.png",
    "LG 1 Film": "https://epg.pw/logo/lg_channels.png",
    "LG 1 Spotlight": "https://epg.pw/logo/lg_channels.png",
    "LG 1": "https://epg.pw/logo/lg_channels.png",
    "GoUSA TV": "https://epg.pw/logo/gousa_tv.png",
    "Inside Outside": "https://epg.pw/logo/inside_outside.png",
    "SBS Drama": "https://epg.pw/logo/sbs_drama.png",
    "New Kmovies": "https://epg.pw/logo/new_kmovies.png",

    # === [CGTN 系列] ===
    "CGTN俄语": "https://epg.pw/logo/cgtnrussian.png",
    "CGTN阿语": "https://epg.pw/logo/cgtnarabic.png",
    "CGTN阿拉伯语": "https://epg.pw/logo/cgtnarabic.png",
    "CGTN": "https://epg.pw/logo/cgtn.png",
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
