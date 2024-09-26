# P5D - Pixiv Post Processor of Powerful Pixiv Downloader
[Powerful Pixiv Downloader](https://github.com/xuejianxianzun/PixivBatchDownloader) 的後處理腳本。
解決 Powerful Pixiv Downloader 下載資料夾需要手動整理的問題。把作品依照分類的檔案再細分成各個標籤，比如 `原神` 和 `崩鐵` 分為兩個資料夾儲存，再依據 `人物` 進行分類，此外還附加一些小功能。

## 特色
📁 分類：根據角色分類到不同資料夾  
🔄 同步：上傳到 NAS  
🔍 搜尋：到 danbooru 搜尋並且下載遺失的作品  
📊 檢視：作品標籤比例  
🌐 跨平台：Windows/Mac/Linux 全平台支援！  
🐳 Docker：現在也可以在 Docker 上運行！

## 安裝和執行
安裝分成 Python 安裝和 Docker 安裝，如果電腦已經配置好 Docker 再用 Docker 安裝會比較輕鬆，否則選擇 Python 安裝。

### Python
需求：[Python](https://liaoxuefeng.com/books/python/install/) 和 [rsync](https://formulae.brew.sh/formula/rsync)，安裝完成後使用以下指令安裝腳本：
```sh
git clone -q https://github.com/ZhenShuo2021/P5D    # 或是直接下載 repo
cd P5D                                              # 進入資料夾
python -m venv .venv                                # 創建虛擬環境，下一步是進入虛擬環境
source .venv/bin/activate                           # Windows指令: .venv\Scripts\activate
pip install -r requirements.txt                     # 安裝依賴套件
python3 run.py                                      # 執行腳本
```

<details>
<summary> Windows 安裝 rsync </summary>

有使用指令或者圖形介面兩種方式
1. 指令：用系統管理員身分執行 PowerShell
```sh
# 下載 cwrsync
$zipUrl = "https://itefix.net/download/free/cwrsync_6.3.1_x64_free.zip"
$zipPath = "C:\app\cwrsync.zip"
$newPath = "C:\app\cwrsync\bin"
Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath

# 建立資料夾並且解壓縮
New-Item -Path "C:\app" -ItemType Directory -Force
Expand-Archive -Path $zipPath -DestinationPath "C:\app\cwrsync"
Remove-Item -Path $zipPath

[System.Environment]::SetEnvironmentVariable("PATH", "$([System.Environment]::GetEnvironmentVariable("PATH", [System.EnvironmentVariableTarget]::Machine));$newPath", [System.EnvironmentVariableTarget]::Machine)
```

2. 圖形介面：在 https://itefix.net/cwrsync/client/downloads 下載完成後解壓縮，重新命名資料夾為 cwrsync，放到 C:\app 資料夾中，執行 `sysdm.cpl`，點擊 `進階` > `環境變數` > 系統變數中找到 `PATH` > 點擊新增輸入 `C:\app\cwrsync\bin` > 點選兩個確認以及關閉 cmd 刷新。
</details>

### Docker
需求：[Docker Desktop](https://www.docker.com/products/docker-desktop/)，安裝完成後使用以下指令安裝腳本：
```sh
git clone -q https://github.com/ZhenShuo2021/P5D    # 或是直接下載 repo
cd P5D                                              # 進入資料夾
docker build -t p5d .                               # 建立鏡像
docker run -v /path/to/local:/mnt/local_path \      # 執行，冒號左邊設定資料夾位置
-v /path/to/remote:/mnt/remote_path \
-v /path/to/output:/app/data -it p5d
```

## 基礎設定

使用前先在 config 資料夾設定：
1. BASE_PATHS: 本地及遠端資料夾路徑
2. categories: 分類，對應 Pixiv Downloader 中設定的[標籤](https://xuejianxianzun.github.io/PBDWiki/#/zh-tw/%E8%A8%AD%E5%AE%9A%E9%81%B8%E9%A0%85?id=%e4%bd%bf%e7%94%a8%e7%ac%ac%e4%b8%80%e5%80%8b%e5%8c%b9%e9%85%8d%e7%9a%84-tag-%e5%bb%ba%e7%ab%8b%e8%b3%87%e6%96%99%e5%a4%be)
3. tags: 細分分類，設定標籤及其翻譯對應，進一步依照標籤分類檔案，如果標籤有多種別名可以全部綁定到同一個資料夾
4. children: 用於作品有多個分支。children 的檔案會全部移動到該分類的資料夾
5. tag_delimiter: 設定第一個標籤和標籤之間的分隔符號，依照[命名規則](https://xuejianxianzun.github.io/PBDWiki/#/zh-tw/%E4%BE%BF%E6%8D%B7%E5%8A%9F%E8%83%BD?id=%e5%84%b2%e5%ad%98%e5%92%8c%e8%bc%89%e5%85%a5%e5%91%bd%e5%90%8d%e8%a6%8f%e5%89%87)設定

> [!CAUTION]
> 資料夾第一層副檔名為 `file_type` 的檔案會被放進 others 資料夾。

## 使用範例
Powerful Pixiv Downloader 下載完成後執行 `run.py`，預設執行除了下載以外的所有功能
```sh
source .venv/bin/activate && python3 run.py
```

參數：
```sh
options:
  -h, --help               show this help message and exit
  --no-categorize          關閉分類功能
  --no-sync                關閉同步功能
  --no-retrieve            關閉尋找遺失作品功能
  --no-view                關閉統計標籤功能
  --no-archive             關閉日誌功能
  --download               尋回遺失作品後自動下載
  --direct_sync            跳過本地分類直接映射到遠端目錄
  --stats_dir              統計檔案的工作目錄
  -q, --quiet              安靜模式
  -v, --verbose            偵錯模式
  -o, --options key=value  其他選項
                           rsync: rsync 參數
                           local: local_path 路徑
                           remote: remote_path 路徑
                           category: 處理指定分類
```

使用範例：不統計標籤，下載遺失作品，啟用 direct_sync，修改 local 和 remote 路徑，只處理指定分類的檔案，rsync使用"--remove-source-files -a"參數。
```sh
python3 run.py --no-view --download --direct-sync -o local=/Users/leo/Pictures/downloads拷貝 remote=/Users/leo/Downloads/TestInput category="Marin, IdolMaster, Others"  rsync="--remove-source-files -a"
```

> [!NOTE]
> 搜尋遺失作品方法：Powerful Pixiv Downloader 下載後不要關閉，複製頁面最上方狀態欄的結果到 `data/retrieve/id.txt`。


> [!NOTE]
> 預設不下載遺失作品因為 [gallery-dl](https://github.com/mikf/gallery-dl) 功能更完善。使用 `gallery-dl -I id_retrieve.txt` 可以一鍵下載。

## 進階設定
- 分類：可以在 `categorizer.py` 修改 `CustomPathResolver` 和 `ResolverAdapter` 自訂分類方式。  
- 同步：rsync 參數可參考[這裡](https://ysc.goalsoft.com.tw/blog-detail.php?target=back&no=49)。  
- 搜尋：根據文件尋找 danbooru 是否有對應作品，如果有其他可依據 pixiv id 搜尋作品的網站也歡迎提供，目前只有找到 danbooru 有提供 API。  
- 檢視：檢視作品標籤比例，在 data 資料夾生成 tag_stats.jpg 和 tag_stats.txt，可以看你平常都看了啥。  
- 作為一般標籤分類使用：設定 `-o category="Others"` 可當作一般檔名分類器使用。  

# TroubleShooting
- ImportError: DLL load failed while importing _cext: 找不到指定的模組。  
安裝 [MSVC](https://learn.microsoft.com/zh-tw/cpp/windows/latest-supported-vc-redist?view=msvc-170)
- Failed to load configuration: Reserved escape sequence used  
toml 中 `BASE_PATHS` 括弧改成單括弧 `'`
- rsync warning: some files vanished before they could be transferred (code 24)    
路徑長度超過系統限制，在 win10 22h2 19045.3803 實測網路上修改路徑長度限制也沒用，別想了   
- 檔案沒有成功分類  
重新複製實際下載資料夾名稱到 config 中，問題原因是 `ブルーアーカイブ` 和 `ブルーアーカイブ` 看起來一樣編碼卻不同。


### Roadmap
- [x] unittest
- [x] 優化遠端同步流程
- [x] retriever 支援 `gallery-dl` 一鍵下載
- [x] 同步功能支援 Windows ([cwrsync](https://www.cnblogs.com/michael9/p/11820919.html))
- [ ] 整合 `magick`, `imageoptim` 後處理
- [ ] 整合檔案自動識別標籤
- [x] 支援 Docker 安裝