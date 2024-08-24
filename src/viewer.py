# Extract tags for downloaded file. Use this to observe your file properties.
# You can remove read_tag_counts and plot_pie_chart if you don't need it

import os
import re
from collections import Counter
import matplotlib.pyplot as plt
from utils.file_utils import ConfigLoader
from utils.string_utils import is_system, color_text, split_tags

# Parameters
# working_dir: 統計標籤的工作目錄
# file_name: 輸出標籤和圖表的檔案名稱
config_loader = ConfigLoader()
work_dir = config_loader.get_base_paths().get("remote")
file_name = 'tag_stats'

# Functions
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def read_tag_counts(file_name):
    file_name = "./data/" + file_name + ".txt"
    tag_counts = Counter()
    with open(file_name, 'r') as file:
        for line in file:
            tag, count = line.strip().split(':')
            tag_counts[tag] = int(count)
    return tag_counts

def plot_pie_chart(tag_counts, top_n=25, skip=2, output_file=file_name, dpi=360):
    output_file = output_file + ".jpg"
    keywords_to_skip = ['users', 'ブルアカ', 'BlueArchive']
    exact_match_to_skip = '閃耀色彩'
    
    filtered_counts = {tag: count for tag, count in tag_counts.items() 
                       if not (any(keyword in tag for keyword in keywords_to_skip) or tag == exact_match_to_skip)}
    
    filtered_tag_counts = Counter(filtered_counts)
    
    most_common = filtered_tag_counts.most_common(top_n + skip)[skip:]
    if not most_common:
       print(color_text("標籤數量不足以製作圓餅圖（可能是目的地沒有檔案導致讀不到標籤/skip值太大）", "red"))
       return
    tags, counts = zip(*most_common)
    
    plt.figure(figsize=(12, 8))
    colors = plt.cm.Paired(range(len(tags)))  # Use a colormap for colors
    wedges, texts, autotexts = plt.pie(counts, labels=tags, autopct='%1.1f%%', startangle=90, colors=colors, wedgeprops={'edgecolor': 'black'})
    
    for text in texts:
        x, y = text.get_position()
        if y > 0.9:
            text.set_horizontalalignment('center')
            text.set_verticalalignment('bottom')
    
    plt.axis('equal')
    plt.savefig(f'./data/{output_file}', dpi=dpi, format='jpg', bbox_inches='tight')
    plt.close()

    print(f"圖表已輸出到{os.getcwd()}/data/{output_file}")
    
# tag
def count_tags(directory, tag_delimiter, recursive=True, output_file='tags'):
    all_tags = []
    total_files = 0

    if recursive:
        for root, _, files in os.walk(directory):
            for filename in files:
                if not is_system(filename):
                    tags = split_tags(filename, tag_delimiter)
                    all_tags.extend(tags)
                    total_files += 1
    else:
        for filename in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, filename)) and not is_system(filename):
                tags = split_tags(filename, tag_delimiter)
                all_tags.extend(tags)
                total_files += 1
    
    tag_counts = Counter(all_tags)
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    
    with open(f'./data/{output_file}.txt', 'w', encoding='utf-8') as f:
        f.write(f"Total files: {total_files}\n")
        for tag, count in sorted_tags:
            f.write(f"{tag}: {count}\n")

    print(f"標籤已輸出到{os.getcwd()}/data/{output_file}.txt")


def viewer_main(config_loader, file_name=file_name):
    base_path = config_loader.get_base_paths()
    tag_delimiter = config_loader.get_delimiters()
    count_tags(base_path["local_path"], tag_delimiter, output_file=file_name)
    tag_counts = read_tag_counts(file_name)
    plot_pie_chart(tag_counts, 15, skip=2)   # skip since the top tags are useless

if __name__ == "__main__":
    viewer_main(config_loader)