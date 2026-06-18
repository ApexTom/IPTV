import requests
import re
import os
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
    # === 境外核心频道（本地重命名规范化后的图标）===
    "Astro AOD": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/Astro_AOD.png",
    "tvN": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/tvN.png",
    "HBO喜剧": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/HBO_Comedy.png",
    "CH5": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CH5.png",
    "CH8": "https://raw.githubusercontent.com/Jack123liang/iptv-proxy/main/logos/CH8.png",
    # 后续新增频道，只需在此处添加映射，并在 sync_logos() 里补上对应的远程下载源即可
}


def _keyword_matches(keyword, text):
    """LOGO_MAP 关键词匹配，按关键词是否含中文字符分流：

    - 纯英文/数字关键词（如 "CH5", "tvN"）：用 \\b 词边界，避免误伤
      "CH52" 这种相邻字符拼接成的不同频道名。
    - 含中文字符的关键词（如 "HBO喜剧"）：汉字本身在 Unicode 下也算
      \\w 字符，两个汉字之间不存在词边界，\\b 会失效（例如 "HBO喜剧高清"
      匹配不到 \\bHBO喜剧\\b）。这种情况改用简单包含匹配；误判风险用
      关键词本身写得足够具体来控制（如带上 "HBO" 前缀而不是只写"喜剧"）。
    """
    if re.search(r'[\u4e00-\u9fa5]', keyword):
        return keyword.lower() in text.lower()
    return re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE) is not None


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

            # --- 1. 正则匹配 CCTV 系列 ---
            # 只标准化频道名称写法（"CCTV-5"/"CCTV_5" -> "CCTV5"），不注入 tvg-logo。
            # epg.pw 的台标链接已实测失效（404），不再依赖这个第三方台标源；
            # CCTV 台标改由 APTV 播放器内置台标库按频道名自动识别。
            # 同时主动清空源数据里可能自带的 tvg-logo，避免源里的失效链接
            # 盖过播放器的自动匹配
            cctv_match = re.search(r'CCTV[-_ ]*(\d+\+?)', extinf, re.IGNORECASE)
            if cctv_match:
                num_str = cctv_match.group(1)
                extinf = re.sub(
                    r'CCTV[-_ ]*\d+\+?',
                    f'CCTV{num_str}',
                    extinf,
                    count=1,
                    flags=re.IGNORECASE
                )
                extinf = re.sub(r'tvg-logo="[^"]*"', '', extinf)
                extinf = re.sub(r'\s+', ' ', extinf).replace(' ,', ',').strip()

            # --- 2. 匹配自定义频道的 LOGO_MAP ---
            # 只在频道名称字段（最后一个逗号后面的部分）里匹配
            if not logo_url:
                channel_name = extinf.split(',')[-1] if ',' in extinf else extinf
                for keyword, l_url in LOGO_MAP.items():
                    if _keyword_matches(keyword, channel_name):
                        logo_url = l_url
                        break

            # --- 3. 注入 tvg-logo ---
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


# --- 4. 自动化下载：把对方的命名，下载时规范化为自己的标准名字 ---
def sync_logos():
    os.makedirs("logos", exist_ok=True)

    LOGOS_TO_DOWNLOAD = {
        "logos/Astro_AOD.png": "https://tvlogo-282.pages.dev/logos/astro/AstroAOD_2024.png",
        "logos/tvN.png": "https://tvlogo-282.pages.dev/logos/astro/tvN_2021.png",
        "logos/HBO_Comedy.png": "https://tvlogo-282.pages.dev/logos/starhub/602_1920x1080_HTV.png",
        "logos/CH5.png": "https://tvlogo-282.pages.dev/logos/starhub/102_1920x1080_HTV.png",
        "logos/CH8.png": "https://tvlogo-282.pages.dev/logos/starhub/103_1920x1080_HTV.png",
    }

    for local_path, remote_url in LOGOS_TO_DOWNLOAD.items():
        print(f"正在尝试同步远程台标: {remote_url}")
        r = fetch_with_retry(remote_url, retries=2, timeout=10)

        if r is not None:
            with open(local_path, "wb") as f:
                f.write(r.content)
            print(f"【成功】台标已同步并安全覆盖: {local_path}")
        else:
            # 远程台标失效、改名或网络异常，触发保护机制
            if os.path.exists(local_path):
                print(f"保护机制生效：已拒绝覆盖，保留仓库原有的历史图标：{local_path}")
            else:
                print(f"本地暂无此图标备份，请检查远程链接是否正确：{remote_url}")


if __name__ == "__main__":
    channels = fetch_and_merge()
    if channels:
        process_and_save(channels)
        sync_logos()
    else:
        print("未获取到任何有效的直播源数据。")
