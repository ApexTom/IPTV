import requests
import re
import os

# 原始直播源 URL
SOURCES = [
    "https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/GNTV.m3u",
    "https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/Global.m3u"
]

# 统一使用你自己的 Jack123liang/iptv-proxy 仓库的 jsDelivr CDN 加速直链
# 彻底废弃所有无法访问的 epg.pw 链接
LOGO_MAP = {
    # === 境外核心频道 (使用你本地重命名规范化后的图标) ===
    "Astro AOD": "https://cdn.jsdelivr.net/gh/Jack123liang/iptv-proxy@main/logos/Astro_AOD.png",
    "tvN": "https://cdn.jsdelivr.net/gh/Jack123liang/iptv-proxy@main/logos/tvN.png",
    "HBO喜剧": "https://cdn.jsdelivr.net/gh/Jack123liang/iptv-proxy@main/logos/HBO_Comedy.png",
    "CH5": "https://cdn.jsdelivr.net/gh/Jack123liang/iptv-proxy@main/logos/logos/CH5.png",
    "CH8": "https://cdn.jsdelivr.net/gh/Jack123liang/iptv-proxy@main/logos/logos/CH8.png",
    # 如果后续有其他频道需要，只需在下方 sync_logos 里添加映射，并在这一步对齐本地标准命名即可,
}

def fetch_and_merge():
    merged_channels = []
    seen_urls = set()

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
            
            # --- 1. 正则匹配 CCTV 系列（如需要分配本地台标，可后续将 cctv 改为你自己的本地库路径） ---
            cctv_match = re.search(r'CCTV[-_ ]*(\d+[\s\+\w\u4e00-\u9fa5]*)', extinf, re.IGNORECASE)
            if cctv_match:
                raw_num = re.search(r'\d+\+?', cctv_match.group(1))
                if raw_num:
                    num_str = raw_num.group(0)
                    cctv_num = num_str.replace('+', 'plus')
                    # 如果 epg.pw 完全挂了，这里可以暂时先保留，或者后续有需要也放进本地 logos 目录
                    logo_url = f'https://epg.pw/logo/cctv{cctv_num}.png'
                    extinf = re.sub(r',CCTV[-_ ]*\d+.*$', f',CCTV{num_str}', extinf, flags=re.IGNORECASE)

            # --- 2. 匹配自定义频道的 LOGO_MAP ---
            if not logo_url:
                for keyword, l_url in LOGO_MAP.items():
                    if keyword.lower() in extinf.lower():
                        logo_url = l_url
                        break
            
            # --- 3. 注入 tvg-logo ---
            if logo_url:
                extinf = re.sub(r'tvg-logo="[^"]*"', '', extinf)
                extinf = extinf.replace('#EXTINF:-1', f'#EXTINF:-1 tvg-logo="{logo_url}"')
                extinf = re.sub(r'\s+', ' ', extinf).replace(' ,', ',')
            
            f.write(f"{extinf}\n{url}\n")
            
    print(f"合并完成！已成功保存至 {output_file}，共 {len(channels)} 个频道。")

# --- 4. 自动化下载：把对方乱七八糟的命名，在下载时规范化为你自己的标准名字 ---
def sync_logos():
    os.makedirs("logos", exist_ok=True)

    LOGOS_TO_DOWNLOAD = {
        "logos/Astro_AOD.png": "https://tvlogo-282.pages.dev/logos/astro/AstroAOD_2024.png",
        "logos/tvN.png": "https://tvlogo-282.pages.dev/logos/astro/tvN_2021.png",
        "logos/HBO_Comedy.png": "https://tvlogo-282.pages.dev/logos/Singtel/2466716e-1aef-4367-82cc-6b795c1ce870.png",
        "logos/CH5.png": "https://tvlogo-282.pages.dev/logos/starhub/102_1920x1080_HTV.png"
        "logos/CH8.png": "https://tvlogo-282.pages.dev/logos/starhub/103_1920x1080_HTV.png"
    }

    for local_path, remote_url in LOGOS_TO_DOWNLOAD.items():
        try:
            print(f"正在尝试同步远程台标: {remote_url}")
            
            # 发起请求
            r = requests.get(remote_url, timeout=10)
            
            # 🌟 关键核心防护：只有状态码明确为 200（代表图片真实存在且下载成功）时，才覆盖本地文件
            if r.status_code == 200:
                with open(local_path, "wb") as f:
                    f.write(r.content)
                print(f"【成功】台标已同步并安全覆盖: {local_path}")
            else:
                # 🌟 如果对方换了链接返回 404，或者服务器崩了，触发此保护机制
                print(f"【⚠️警告】远程台标失效或更名（状态码: {r.status_code}）！")
                if os.path.exists(local_path):
                    print(f"保护机制生效：已拒绝覆盖，完美保留仓库原有的历史图标：{local_path}")
                else:
                    print(f"本地暂无此图标备份，请检查远程链接是否正确。")
                    
        except Exception as e:
            # 网络超时、断网等极端情况，同样完好保留本地原有文件
            print(f"【⚠️错误】网络请求失败: {e}。保护机制生效，保留本地原有图标。")


if __name__ == "__main__":
    channels = fetch_and_merge()
    if channels:
        process_and_save(channels)
        sync_logos()
    else:
        print("未获取到任何有效的直播源数据。")
