import json
import datetime
import cloudscraper
from bs4 import BeautifulSoup

def scrape_marvel_snap_zone():
    scraper = cloudscraper.create_scraper()
    url = "https://marvelsnapzone.com/cards/"
    
    print(f"正在連線並繞過 Cloudflare 獲取 {url}...")
    response = scraper.get(url)
    
    if response.status_code != 200:
        print(f"連線失敗，狀態碼: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    card_elements = soup.find_all('a', class_='msz-ct')
    print(f"成功找到 {len(card_elements)} 張卡牌區塊，開始提取資料與 DefId...")
    
    cards_list = []
    
    for el in card_elements:
        data_src = el.get('data-src', '').lower()
        
        # 濾掉 data-src 為 "none" 的未分類/無效卡牌
        if data_src == "none" or not data_src:
            continue
            
        # 取得遊戲官方唯一識別碼 (例如 MultipleMan)
        def_id = el.get('data-defid', '').strip()
        
        name = el.get('data-n', '').strip().title()
        if not name:
            name_span = el.find('span', class_='msz-ct__name')
            name = name_span.get_text(strip=True) if name_span else "Unknown"
            
        cost = el.get('data-c', '0')
        power = el.get('data-p', '0')
        
        img_tag = el.find('img', class_='msz-cardimg')
        img_url = img_tag.get('src', '') if img_tag else ""
        
        # Series 分類邏輯
        if "series-5" in data_src or "s5" in data_src:
            series = "Series 5"
        elif "series-4" in data_src or "s4" in data_src:
            series = "Series 4"
        else:
            series = "Series 1~3"
            
        cards_list.append({
            "def_id": def_id,  # 新增：官方代號（用於本地對比）
            "name": name,      # 網頁顯示名稱
            "cost": int(cost) if cost.isdigit() else 0,
            "power": power,
            "series": series,
            "image_url": img_url
        })
        
    return cards_list

if __name__ == "__main__":
    raw_cards = scrape_marvel_snap_zone()
    
    if raw_cards:
        database = {
            "last_updated": datetime.datetime.utcnow().isoformat() + "Z",
            "total_count": len(raw_cards),
            "series_groups": {
                "Series 1~3": [],
                "Series 4": [],
                "Series 5": []
            }
        }
        
        for card in raw_cards:
            s = card["series"]
            if s not in database["series_groups"]:
                s = "Series 1~3"
            database["series_groups"][s].append({
                "def_id": card["def_id"],  # 寫入 JSON
                "name": card["name"],
                "cost": card["cost"],
                "power": card["power"],
                "image_url": card["image_url"]
            })
            
        output_file = "marvel_snap_cards.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(database, f, ensure_ascii=False, indent=4)
            
        print(f"成功！已將 {len(raw_cards)} 張卡牌（含 def_id 標記）存入 {output_file}！")
    else:
        print("未能成功擷取卡牌資料。")