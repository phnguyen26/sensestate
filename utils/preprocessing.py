from utils.data_crawler import Data




class Processed_Data:
    def __init__(self, imgs, title, address, price, price_ext, price_unit, area, area_ext, description, direction, legal, url, embedding = None):
        self.imgs = imgs
        self.title = title
        self.address = address
        self.price = price
        self.price_ext = price_ext
        self.price_unit = price_unit
        self.area = area
        self.area_ext = area_ext
        self.description = description
        self.direction = direction
        self.legal = legal
        self.url = url
        self.embedding = embedding
    
    def synthesis(self):
        new_desc = self.description
        new_desc = new_desc.replace("\\n", " ")
        new_desc = new_desc.replace("+", " ")
        text =  'Mô tả ' + new_desc
        return text
    
    

def preprocessing(data: Data) -> Processed_Data:
    # --- Remove invalid image links ---
    imgs = data.imgs
    new_imgs = []
    for img in imgs:
        if 'file4.batdongsan.com.vn' not in img: continue
        new_imgs.append(img)
    
    # --- Handle price and area---
    price = data.price
    new_price, price_unit = None, None
    if 'tỷ' in price:
        price_unit = 'tỷ'
        new_price = float(price.split('tỷ')[0].strip().replace(',', '.'))
    elif 'triệu' in price:
        price_unit = 'triệu/tháng'
        new_price = float(price.split('triệu')[0].strip().replace(',', '.'))
    else:
        price_unit = 'Thỏa thuận'
        new_price = float(0)
    area = data.area
    area= area.split('m²')
    new_area = float(area[0].strip().replace(',', '.'))
    
    
    #Handle description
    desc = data.description
    new_desc = desc.strip()
    if new_desc[0] == '\\': new_desc = new_desc[2:].strip()
    if new_desc[-2:] == '\\n' :new_desc = new_desc[:-2].strip()
    
    return Processed_Data(new_imgs, data.title, data.address, new_price, data.price_ext, price_unit, new_area, data.area_ext, new_desc, data.direction, data.legal, data.url)

if __name__ == '__main__':
    pass

