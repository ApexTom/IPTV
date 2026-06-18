import requests
import os
import time

# 台标下载源汇总
LOGOS_TO_DOWNLOAD = {
    # === 央视 CCTV 系列：来自 fanmingming/live 公益台标库 ===
    "CCTV1.png": "https://live.fanmingming.com/tv/CCTV1.png",
    "CCTV2.png": "https://live.fanmingming.com/tv/CCTV2.png",
    "CCTV3.png": "https://live.fanmingming.com/tv/CCTV3.png",
    "CCTV4.png": "https://live.fanmingming.com/tv/CCTV4.png",
    "CCTV5.png": "https://live.fanmingming.com/tv/CCTV5.png",
    "CCTV5plus.png": "https://live.fanmingming.com/tv/CCTV5+.png",
    "CCTV6.png": "https://live.fanmingming.com/tv/CCTV6.png",
    "CCTV7.png": "https://live.fanmingming.com/tv/CCTV7.png",
    "CCTV8.png": "https://live.fanmingming.com/tv/CCTV8.png",
    "CCTV9.png": "https://live.fanmingming.com/tv/CCTV9.png",
    "CCTV10.png": "https://live.fanmingming.com/tv/CCTV10.png",
    "CCTV11.png": "https://live.fanmingming.com/tv/CCTV11.png",
    "CCTV12.png": "https://live.fanmingming.com/tv/CCTV12.png",
    "CCTV13.png": "https://live.fanmingming.com/tv/CCTV13.png",
    "CCTV14.png": "https://live.fanmingming.com/tv/CCTV14.png",
    "CCTV15.png": "https://live.fanmingming.com/tv/CCTV15.png",
    "CCTV16.png": "https://live.fanmingming.com/tv/CCTV16.png",
    "CCTV17.png": "https://live.fanmingming.com/tv/CCTV17.png",
    "东方卫视.png": "https://static.tv.darwinchow.com/logo/东方卫视.png",
    "河北卫视.png": "https://static.tv.darwinchow.com/logo/河北卫视.png",
    # === 境外频道 ===
    "Astro_AOD.png": "https://tvlogo-282.pages.dev/logos/astro/AstroAOD_2024.png",
    "Astro_AEC.png": "https://tvlogo-282.pages.dev/logos/astro/AstroAOD_2024.png",
    "tvN.png": "https://tvlogo-282.pages.dev/logos/astro/tvN_2021.png",
    "HBO_Comedy.png": "https://tvlogo-282.pages.dev/logos/starhub/602_1920x1080_HTV.png",
    "8TV.png": "https://gcore.jsdelivr.net/gh/luoluowoaini/666-@iill-logo-mytvsuper/8TV.png",
    "CH5.png": "https://tvlogo-282.pages.dev/logos/starhub/102_1920x1080_HTV.png",
    "CH8.png": "https://tvlogo-282.pages.dev/logos/starhub/103_1920x1080_HTV.png",
    "澳门体育.png": "https://gcore.jsdelivr.net/gh/luoluowoaini/666-@iill-logo-mytvsuper/澳门体育.png",
    "澳门综艺.png": "https://gcore.jsdelivr.net/gh/luoluowoaini/666-@iill-logo-mytvsuper/澳门综艺.png",
    "CHU.png": "https://tvlogo-282.pages.dev/logos/starhub/107_1920x1080_HTV.png",
    "天映.png": "https://gcore.jsdelivr.net/gh/luoluowoaini/smt-logo@main/天映.png",
    "HOY.png": "https://tvlogo-282.pages.dev/logos/HOY/HOY.png",
    "IQIYI.png": "https://tvlogo-282.pages.dev/logos/astro/IQIYI_2022.png",
    "AMC.png": "https://github.com/fanmingming/live/blob/main/tv/AMC.png",
    "HBO王牌.png": "https://tvlogo-282.pages.dev/logos/starhub/603_1920x1080_HTV.png",
    “HBO家庭.png”: "https://tvlogo-282.pages.dev/logos/starhub/604_1920x1080_HTV.png",
    "HBO_Hits.png": "https://tvlogo-282.pages.dev/logos/starhub/605_1920x1080_HTV.png",
    "big-ten-network-us.png": "https://github.com/tv-logo/tv-logos/blob/main/countries/united-states/big-ten-network-us.png?raw=true",
    "NBC_NEW_NOW.png": "https://image-resizer-cloud-cdn.api.cms.amdvids.com/image/14F5D3B6-FA2C-4E41-91AD-CD037209D874/3-1x1.png",
    "TVB功夫.png": "https://gcore.jsdelivr.net/gh/taksssss/tv@main/icon/TVB功夫.png",
}

def fetch_with_retry(url, retries=2, timeout=10):
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

def sync_logos():
    # 🌟 仅创建用于试错、存放原生下载件的备份目录
    BACKUP_DIR = "logos_backup"
    os.makedirs(BACKUP_DIR, exist_ok=True)

    success_count = 0
    skip_count = 0

    for filename, remote_url in LOGOS_TO_DOWNLOAD.items():
        # 🌟 纯粹落盘到备份目录，例如 "logos_backup/CH5.png"
        backup_path = os.path.join(BACKUP_DIR, filename)

        print(f"正在尝试下载远程台标: {remote_url}")
        r = fetch_with_retry(remote_url)

        if r is not None:
            with open(backup_path, "wb") as f:
                f.write(r.content)
            print(f"【下载成功】已保存至试错备份库: {backup_path}")
            success_count += 1
        else:
            print(f"【下载失败】远程源异常或更名，未变动本地文件。")
            skip_count += 1

    print(f"\n下载任务结束：成功 {success_count} 个，失败 {skip_count} 个。")
    print(f"提示：所有下载件已放入 {BACKUP_DIR}/ 文件夹。请根据需要自行手动复制所需台标到 logos/ 目录。")

if __name__ == "__main__":
    sync_logos()
