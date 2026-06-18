import requests
import re
import time

# 原始直播源 URL
SOURCES = [
    "https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/GNTV.m3u",
    "https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/Global.m3u"
]

# === 🌟 全局黑名单配置（在此处直接增删你想过滤的频道） ===
# 只要频道名称包含以下关键词（忽略大小写），就会在合并时被自动过滤掉
BLACKLIST = {
    "CCTV-18",      # 举例：不存在的测试台
    "香港面包",      # 举例：购物台
    "南宁新闻",         # 过滤带有"测试"字样的频道
    "南宁公共",
    "南宁文旅",
    "南宁娱乐",
    "宁夏文旅",
    "宁夏娱乐",
    "宁夏公共",
    
    "TEST",
    # 后续不想看的频道，直接在这里追加字符串，记得用逗号隔开即可
}

# 统一使用 Jack123liang/iptv-proxy 仓库的 raw.githubusercontent.com 直链
# （已评估 jsDelivr：存在最长 7 天的边缘缓存，台标更新后无法及时生效；
#  考虑到台标图片对实时性要求不高、客户端会本地缓存，直接用 raw 更省事，
#  代价是国内访问偶尔会慢，但容错率高，不影响播放本身）
LOGO_MAP = {
    # === 央视 CCTV 系列（CCTV5+ 必须排在 CCTV5 之前，否则会被 CCTV5 提前命中）===
    #"体育赛事": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV5plus.png",
    "CCTV5+": "https://static.tv.darwinchow.com/logo/CCTV5+.png",
    "CCTV-1": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV1.png",
    "CCTV-2": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV2.png",
    "CCTV-3": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV3.png",
    "CCTV-4": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV4.png",
    "CCTV-5": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV5.png",
    "CCTV-6": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV6.png",
    "CCTV-7": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV7.png",
    "CCTV-8": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV8.png",
    "CCTV-9": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV9.png",
    "CCTV-10": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV10.png",
    "CCTV-11": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV11.png",
    "CCTV-12": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV12.png",
    "CCTV-13": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV13.png",
    "CCTV-14": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV14.png",
    "CCTV-15": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV15.png",
    "CCTV-16": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV16.png",
    "CCTV-17": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV17.png",
    "看东方4K": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/东方卫视4K.png",
    # === 境外核心频道（本地重命名规范化后的图标）===
    "Astro AOD": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/Astro_AOD.png",
    "tvN": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/tvN.png",
    "HBO喜剧": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/HBO_Comedy.png",
    "CH5": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CH5.png",
    "CHU": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CHU.png",
    "CH8": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CH8.png",
    "八度空间": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/8TV.png",
    "澳门体育": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/澳门体育.png",
    "澳门综艺": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/澳门综艺.png",
    "TVB武侠": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/TVB功夫.png",
    "天映频道": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/天映.png",
    "Astro AEC": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/Astro_AEC.png",
    "ASTRO爱奇艺": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/IQIYI.png",
    "HOY77": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/HOY.png",
    "HOY78": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/HOY.png",
    "HBO精选": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/HBO_Comedy.png",
    "HBO王牌": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/HBO王牌.png",
    "NBC News Now": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/NBC_NEW_NOW.png",
    "Big Ten Network": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/big-ten-network-us.png",
    "TRT World": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/TRT_World.png",
    "Redbull": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/Redbull.png",
    "Cinemax精选": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/Cinemax.png",
    "Movie Sphere": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/Movie_Sphere.png",
    "LMN": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/LMN.png",
    "Sony One Comedy HITS": "https://d1biytugnv36sr.cloudfront.net/resize?width=400&height=200&url=https://static.frequency.com/studio/sony/channels/EN_LG_FAST_ComedyHits_ChannelLogo_Horizontal.png",
    "Sony One Action HITS": "https://d1biytugnv36sr.cloudfront.net/resize?width=400&height=200&url=https://static.frequency.com/studio/sony/channels/EN_LG_FAST_ActionHits_ChannelLogo_Horizontal.png",
    #后续新增频道，只需在此处添加映射，并在 sync_logos.py 里补上对应的远程下载源即可
}


def _keyword_matches(keyword, text):
    """LOGO_MAP 和 黑名单 关键词匹配：只把 ASCII 字母/数字/下划线当作"词字符"来判断边界，
    汉字、空格、符号（包括 "+"）一律视为边界。"""
    pattern = r'(?<![A-Za-z0-9_])' + re.escape(keyword) + r'(?![A-Za-z0-9_])'
    return re.search(pattern, text, re.IGNORECASE) is not None


def fetch_with_retry(url, retries=2, timeout=30):
    """简单重试封装：源站偶尔抽风时避免直接整批跳过"""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 200:
                return resp
            last_err = f"HTTP {resp.status_code}"
        except Exception as e:
            last_err = str(e)
        if attempt < retries:
            time.sleep(2)
    print(f"请求失败（已重试 {retries} 次）: {url} -> {last_err}")
    return None


def fetch_and_merge():
    merged_channels = []
    seen_urls = set()

    for url in SOURCES:
        print(f"正在下载源: {url}")
        response = fetch_with_retry(url)
        if response is None:
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
                    
                    # 🌟 核心拦截修改点：提取名字并跑黑名单检测
                    channel_name = current_extinf.split(',')[-1] if ',' in current_extinf else current_extinf
                    
                    is_blacklisted = False
                    for black_word in BLACKLIST:
                        if _keyword_matches(black_word, channel_name):
                            is_blacklisted = True
                            break
                    
                    if is_blacklisted:
                        print(f"【黑名单拦截】已自动剔除该频道: {channel_name.strip()}")
                        current_extinf = None  # 拦截后重置变量，继续看下一行
                        continue

                    # 没命中黑名单，才允许进入列表
                    seen_urls.add(line)
                    merged_channels.append((current_extinf, line))
                current_extinf = None

    return merged_channels


def process_and_save(channels, output_file="YueChan.m3u"):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for extinf, url in channels:
            logo_url = None
            if "体育赛事" in extinf:
                extinf = '#EXTINF:-1 tvg-name="CCTV5+体育赛事" group-title="央视频道",CCTV5+体育赛事'

            # --- 1. 匹配 LOGO_MAP（含 CCTV 系列 + 境外频道，统一 logic）---
            channel_name = extinf.split(',')[-1] if ',' in extinf else extinf
            for keyword, l_url in LOGO_MAP.items():
                if _keyword_matches(keyword, channel_name):
                    logo_url = l_url
                    break

            # --- 2. 注入 tvg-logo ---
            if logo_url:
                extinf = re.sub(r'tvg-logo="[^"]*"', '', extinf)
                extinf = re.sub(
                    r'^(#EXTINF:[-\d]+)',
                    rf'\1 tvg-logo="{logo_url}"',
                    extinf,
                    count=1
                )
                extinf = re.sub(r'\s+', ' ', extinf).replace(' ,', ',').strip()

            f.write(f"{extinf}\n{url}\n")

    print(f"合并完成！已成功保存至 {output_file}，共 {len(channels)} 个频道。")


if __name__ == "__main__":
    channels = fetch_and_merge()
    if channels:
        process_and_save(channels)
    else:
        print("未获取到任何有效的直播源数据。")
