# P5D - Pixiv Post Processor of Powerful Pixiv Downloader
[Powerful Pixiv Downloader](https://github.com/xuejianxianzun/PixivBatchDownloader) 的後處理腳本。
解決 Powerful Pixiv Downloader 下載資料夾混亂，需要手動整理的問題。把作品依照分類的檔案再細分成各個標籤，比如 `原神` 和 `崩鐵` 分為兩個資料夾儲存，再依據 `人物` 進行分類，此外還附加一些小功能。

## 特色
📁 分類：根據角色分類到不同資料夾  
🔄 同步：上傳到 NAS  
🔍 搜尋：到 danbooru 搜尋遺失的作品  
📊 檢視：作品標籤比例  
🌐 跨平台：Windows/Mac/Linux 全平台支援！  

## 安裝
需求：[Python](https://liaoxuefeng.com/books/python/install/) 和 [rsync](https://formulae.brew.sh/formula/rsync)。Windows 沒有 rsync，要用替代的 [cwrsync](https://itefix.net/cwrsync/client/downloads)。

<details>
<summary> cwrsync 設定 </summary>
下載完成後解壓縮重新命名資料夾成 cwrsync，放到 `C:\app`，有兩種方法設定：

1. 用系統管理員身分執行 PowerShell，輸入
```sh
$newPath = "C:\app\cwrsync\bin"

[System.Environment]::SetEnvironmentVariable("PATH", "$([System.Environment]::GetEnvironmentVariable("PATH", [System.EnvironmentVariableTarget]::Machine));$newPath", [System.EnvironmentVariableTarget]::Machine)
```

2. 執行 `sysdm.cpl`，點擊 `進階` > `環境變數` > 系統變數中找到 `PATH` > 點擊新增輸入 `C:\app\cwrsync\bin` > 點選兩個確認以及關閉 cmd 刷新。
</details>

安裝完成後使用以下指令安裝腳本：
```sh
git clone -q https://github.com/ZhenShuo2021/P5D    # 或是直接下載 repo
cd P5D                                              # 進入資料夾
python -m venv .venv                                # 創建虛擬環境，下一步是進入虛擬環境
source .venv/bin/activate                           # Windows指令: .venv\Scripts\activate
pip install -r requirements.txt                     # 安裝依賴套件
```

## 基礎設定

使用前先在 config 資料夾設定：
1. BASE_PATHS: 本地及遠端資料夾路徑
2. categories: 分類，對應 Pixiv Downloader 中設定的[標籤](https://xuejianxianzun.github.io/PBDWiki/#/zh-tw/%E8%A8%AD%E5%AE%9A%E9%81%B8%E9%A0%85?id=%e4%bd%bf%e7%94%a8%e7%ac%ac%e4%b8%80%e5%80%8b%e5%8c%b9%e9%85%8d%e7%9a%84-tag-%e5%bb%ba%e7%ab%8b%e8%b3%87%e6%96%99%e5%a4%be)
3. tags: 細分分類，設定標籤及其翻譯對應，進一步依照標籤分類檔案，如果標籤有多種別名可以全部綁定到同一個資料夾
4. children: 用於作品有多個分支。children 的檔案會全部移動到該分類的資料夾
5. tag_delimiter: 設定第一個標籤和標籤之間的分隔符號，依照[命名規則](https://xuejianxianzun.github.io/PBDWiki/#/zh-tw/%E4%BE%BF%E6%8D%B7%E5%8A%9F%E8%83%BD?id=%e5%84%b2%e5%ad%98%e5%92%8c%e8%bc%89%e5%85%a5%e5%91%bd%e5%90%8d%e8%a6%8f%e5%89%87)設定

py 和 toml 是相同的，喜歡哪種就用哪種。

> [!CAUTION]
> 下載資料夾中第一層的檔案會全部被視為其他作品放進 others 資料夾。

## 使用
Powerful Pixiv Downloader 下載完成後執行 `run.py`
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
  -q, --quiet              安靜模式
  -v, --verbose            偵錯模式
  -o, --options key=value  其他選項
                           rsync: rsync 參數
                           local: local_path 路徑
                           remote: remote_path 路徑
                           category: 處理指定分類
```

使用範例：不統計標籤，不尋找遺失作品，修改 local 和 remote 路徑，只處理指定分類的檔案，rsync使用"--remove-source-files -a"參數。
```sh
python3 run.py --no-view --no-retrieve -o local=/Users/leo/Pictures/downloads拷貝3 remote=/Users/leo/Downloads/TestInput category="Marin, IdolMaster, Others"  rsync="--remove-source-files -a"
```

> [!NOTE]
> 搜尋遺失作品方法：Powerful Pixiv Downloader 下載後不要關閉，右鍵檢查>右鍵class="beautify_scrollbar logContent">Copy>Copy outerHTML，把內容儲存為 `data/pixiv.html`，處理完成後結果會輸出在 data/pixiv_retrieve.txt

## 進階設定
- 分類：可以在 `categorizer.py` 修改 `CustomCategorizer` 和 `get_categorizer` 自訂分類方式。  
- 同步：rsync 參數可參考[這裡](https://ysc.goalsoft.com.tw/blog-detail.php?target=back&no=49)。  
- 搜尋：根據文件尋找 danbooru 是否有對應作品，如果有其他可依據 pixiv id 搜尋作品的網站也歡迎提供，目前只有找到 danbooru 有提供 API。  
- 檢視：檢視作品標籤比例，在 data 資料夾生成 tag_stats.jpg 和 tag_stats.txt，可以看你平常都看了啥。  

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
- [ ] 優化遠端同步流程
- [ ] retriever 自動擷取 HTML
- [ ] retriever 支援無結構文件
- [ ] retriever 支援 `gallery-dl` 一鍵下載
- [x] 同步功能支援 Windows ([cwrsync](https://www.cnblogs.com/michael9/p/11820919.html))
- [ ] 整合 `magick`, `imageoptim` 後處理
- [ ] 整合檔案自動識別標籤


### 架構
```sh
P5D/
├── run.py                     # 入口程式
├── README.md                  # 說明文件
├── requirements.txt           # 需求套件
├── config
│   └── config.toml            # 使用者定義設置
├── data/
│   ├── pixiv.html             # 下載記錄，用於尋回檔案
│   ├── pixiv_retrieve.txt     # 檔案取回結果
│   ├── rsync_log.log          # 同步日誌
│   ├── system.log             # 系統日誌
│   ├── tag_stats.jpg          # 標籤統計圓餅圖
│   └── tag_stats.txt          # 標籤統計結果
├── src/
│   ├── __init__.py
│   ├── __main__.py
│   ├── categorizer.py         # 檔案分類
│   ├── config.py              # 系統參數
│   ├── custom_logger.py       # 系統日誌
│   ├── option.py              # 設置選項處理
│   ├── retriever.py           # 搜尋遺失作品
│   ├── synchronizer.py        # 同步到遠端儲存裝置
│   ├── utils/
│   │   ├── file_utils.py      # 檔案工具
│   │   └── string_utils.py    # 字串工具
│   └── viewer.py              # 標籤統計
└── test/
    ├── __init__.py
    └── test_categorizer.py    # 檔案分類測試
```