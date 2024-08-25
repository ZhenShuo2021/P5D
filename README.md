# Pixiv 後處理腳本
[Powerful Pixiv Downloader](https://github.com/xuejianxianzun/PixivBatchDownloader) 下載後的檔案處理腳本。  
後處理 Powerful Pixiv Downloader 標籤，把依照作品分類的檔案再細分成各個角色，比如 `原神` 和 `崩鐵` 分為兩個資料夾儲存，再依據 `人物` 進行分類，此外還附加一些小功能。

## 功能
📁 分類：將指定作品（如 IM BA）根據角色分類到不同資料夾  
🔄 同步：上傳到 NAS  
🔍 搜尋：到 danbooru 搜尋遺失的作品  
📊 檢視：作品標籤比例  

## 安裝
安裝好 [Python](https://liaoxuefeng.com/books/python/install/) 後安裝此腳本
```sh
git clone -q https://github.com/ZhenShuo2021/P5D && cd P5D && python3 -m venv .venv && source .venv/bin/activate && pip3 install -r requirements.txt
``` 

使用 Powerful Pixiv Downloader 下載完成後執行 `main.py`  
```sh
source .venv/bin/activate && python3 main.py
```


## 基礎設定

`config.toml` 設定：
1. BASE_PATHS: 本地資料夾以及遠端儲存資料夾位置
2. categories: 分類，也就是 Pixiv Downloader 中設定的[標籤](https://xuejianxianzun.github.io/PBDWiki/#/zh-tw/%E8%A8%AD%E5%AE%9A%E9%81%B8%E9%A0%85?id=%e4%bd%bf%e7%94%a8%e7%ac%ac%e4%b8%80%e5%80%8b%e5%8c%b9%e9%85%8d%e7%9a%84-tag-%e5%bb%ba%e7%ab%8b%e8%b3%87%e6%96%99%e5%a4%be)
3. children: 用於作品有多個分支，會把 children 的檔案全部移動到相同資料夾
4. tags: 設定標籤及其翻譯對應，進一步依照標籤分類檔案，如果標籤有多種別名可以全部綁定到同一個資料夾
5. tag_delimiter: 設定第一個標籤和標籤之間的分隔符號，依照[命名規則](https://xuejianxianzun.github.io/PBDWiki/#/zh-tw/%E4%BE%BF%E6%8D%B7%E5%8A%9F%E8%83%BD?id=%e5%84%b2%e5%ad%98%e5%92%8c%e8%bc%89%e5%85%a5%e5%91%bd%e5%90%8d%e8%a6%8f%e5%89%87)設定

> [!CAUTION]  
> 下載資料夾中未指定的子資料夾不會處理，但是檔案會全部被視為其他作品放進 others 資料夾。

## 進階設定
進入資料夾後使用 `python3 -m src.xxx` 可獨立執行每個模組
- 分類：可以在 `categorizer.py` 修改 `CustomCategorizer` 和 `get_categorizer` 自訂分類方式。
- 同步：`_run_rsync` 中修改 rsync 參數，參數可參考[這裡](https://ysc.goalsoft.com.tw/blog-detail.php?target=back&no=49)。
- 搜尋：根據文件尋找 danbooru 是否有對應作品。 
- 檢視：檢視作品標籤比例，在 data 資料夾生成 tag_stats.jpg 和 tag_stats.txt，可以看你平常都看了啥。  

> [!NOTE]  
> 搜尋的使用方法：Powerful Pixiv Downloader 下載後不要關閉，右鍵檢查>右鍵class="beautify_scrollbar logContent">Copy>Copy outerHTML，把內容儲存為 `data/pixiv.html`，處理完成後結果會輸出在 data/pixiv_retrieve.txt

### Roadmap
- [ ] unittest
- [ ] 優化遠端同步流程
- [ ] retriever 自動擷取 HTML
- [ ] retriever 支援無結構文件
- [ ] retriever 支援 `gallery-dl` 一鍵下載
- [ ] 整合 `magick`, `imageoptim` 後處理
- [ ] 整合檔案自動識別標籤


### 架構
```
.
├── README.md
├── requirements.txt
├── config
│   └── config.toml
├── data
│   ├── pixiv.log              # 系統日誌
│   ├── pixiv.html             # 下載記錄，用於取回檔案
│   ├── pixiv_retrieve.txt     # 檔案取回結果
│   ├── rsync_log.log          # 同步日誌
│   ├── tag_stats.jpg          # 標籤統計圓餅圖
│   └── tag_stats.txt          # 標籤統計結果
├── src
│   ├── categorizer.py         # 檔案分類
│   ├── logger.py              # 日誌
│   ├── main.py                # 主程式
│   ├── retriever.py           # 搜尋遺失作品
│   ├── synchronizer.py        # 同步到遠端儲存裝置
│   └── viewer.py              # 標籤統計
└── utils
    ├── file_utils.py          # 檔案移動工具
    └── string_utils.py        # 字串檢查工具
```