import requests
import os
import time

# 台标下载源汇总
LOGOS_TO_DOWNLOAD = {
    # === 央视 CCTV 系列：来自 fanmingming/live 公益台标库 ===
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
