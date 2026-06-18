import requests
import re
import time

# 原始直播源 URL
SOURCES = [
    "https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/GNTV.m3u",
    "https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/Global.m3u"
]

# 统一使用 Jack123liang/iptv-proxy 仓库的 raw.githubusercontent.com 直链
# （已评估 jsDelivr：存在最长 7 天的边缘缓存，台标更新后无法及时生效；
#  考虑到台标图片对实时性要求不高、客户端会本地缓存，直接用 raw 更省事，
#  代价是国内访问偶尔会慢，但容错率高，不影响播放本身）
LOGO_MAP = {
    # === 央视 CCTV 系列（CCTV5+ 必须排在 CCTV5 之前，否则会被 CCTV5 提前命中）===
    "CCTV5+": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV5plus.png",
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
    "体育赛事": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CCTV5plus.png",
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
    "Cinemax精选": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/cinemax-classics-us.png?",
    "NBC News Now": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/NBC_NEW_NOW.png",
    "Big Ten Network": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/big-ten-network-us.png",
    # 后续新增频道，只需在此处添加映射，并在 sync_logos.py 里补上对应的远程下载源即可
}


def _keyword_matches(keyword, text):
    """LOGO_MAP 关键词匹配：只把 ASCII 字母/数字/下划线当作"词字符"来判断边界，
    汉字、空格、符号（包括 "+"）一律视为边界。这一条规则同时解决两类问题：

    - "CH5" 不会误匹配 "CH52"（5 后面紧跟数字 2，仍是词字符，不构成边界，不匹配）
    - "CCTV2" 能匹配 "CCTV2财经"（2 后面紧跟汉字，汉字不算 ASCII 词字符，构成边界，匹配成功）
    - "HBO喜剧" 能匹配 "HBO喜剧高清"（剧后面紧跟"高"，同理构成边界，匹配成功）
    - "CCTV5" 不会抢先匹配 "CCTV5+体育赛事" 里的内容，只要 "CCTV5+" 在字典里排在
      "CCTV5" 前面，循环会先命中更精确的 "CCTV5+"
    """
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
                    seen_urls.add(line)
                    merged_channels.append((current_extinf, line))
                current_extinf = None

    return merged_channels


def process_and_save(channels, output_file="YueChan.m3u"):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for extinf, url in channels:
            logo_url = None

            # --- 1. 匹配 LOGO_MAP（含 CCTV 系列 + 境外频道，统一逻辑）---
            # 只在频道名称字段（最后一个逗号后面的部分）里匹配
            channel_name = extinf.split(',')[-1] if ',' in extinf else extinf
            for keyword, l_url in LOGO_MAP.items():
                if _keyword_matches(keyword, channel_name):
                    logo_url = l_url
                    break

            # --- 2. 注入 tvg-logo ---
            # 用正则匹配 #EXTINF: 后面的数字（不管是 -1 还是 0 或其他），
            # 不再硬编码 "#EXTINF:-1"，避免源格式不同时静默注入失败
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


# 注：台标下载已分离到独立的 sync_logos.py，需要更新台标时手动运行该脚本，
# 不再随每日自动合并任务一起执行，避免远程台标源的变动影响日常稳定运行。


if __name__ == "__main__":
    channels = fetch_and_merge()
    if channels:
        process_and_save(channels)
    else:
        print("未获取到任何有效的直播源数据。")
