import requests
from bs4 import BeautifulSoup
import psycopg2

try:
    conn = psycopg2.connect(
        dbname="your_database_name",
        user="uour_username",
        password="your_secret_password",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    print("Database connection successful!")
except Exception as e:
    print(f"Error connecting to the database: {e}")
    exit()

base_url = "https://www.amazon.in/s?k=smart+lock&page="

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.amazon.in/"
}


for page in range(1, 21): 
    print(f"Scraping page {page}...")
    url = f"{base_url}{page}"
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch page {page} (Status Code: {response.status_code})")
        continue 
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    products = soup.find_all("div", {"data-component-type": "s-search-result"})
    
    if not products:
        print(f"No products found on page {page}. Skipping.")
        continue
    
    for index, product in enumerate(products, start=1):  

        ranking = index
        try:
            
            brandname = product.find("h2", class_="a-size-base-plus")
            brandname = brandname.text.strip() if brandname else "N/A"
            brandname=brandname.split(' ')[0] if brandname else "N/A"
            
            
            price_element = product.find("span", class_="a-price-whole")

            if price_element:
                try:
                    price = int(price_element.text.strip().replace(",", ""))
                except ValueError:
                    print(f"Price parsing error: {price_element.text.strip()}")
                    price = None  
            else:
                price = None
            
            rating = product.find("span", class_="a-icon-alt")
            rating = rating.text.strip() if rating else "N/A"
            rating = float(rating.split(' ')[0] if rating != "N/A" else 0.0)

            ratingcount_element = product.find("span", class_="a-size-base")

            if ratingcount_element:
                ratingcount_text = ratingcount_element.text.strip()
                if any(char.isdigit() for char in ratingcount_text):
                    ratingcount = int(''.join(filter(str.isdigit, ratingcount_text)))
                else:
                    ratingcount = 0
            else:
                ratingcount = 0

            
            print(f"Extracted rating count: {ratingcount}")

            product_url = product.find("a", class_="a-link-normal")
            product_url = f"https://www.amazon.in{product_url['href']}" if product_url else "N/A"
            
            cursor.execute(
                """
            INSERT INTO products (brandname, price, rating, ratingcount, ranking, url)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (brandname, price, rating, ratingcount,ranking, product_url)
            )
            conn.commit()
            
            print(f"Brandname: {brandname}")
            print(f"Price: {price}")
            print(f"Rating: {rating}")
            print(f"Rating Count: {ratingcount}")
            print(f"Ranking: {ranking}")
            print(f"URL: {product_url}")
            print("-" * 40)
        except Exception as e:
            print(f"Error parsing product: {e}")
    
    print(f"Finished scraping page {page}.\n")

cursor.close()
conn.close()
print("Database connection closed!")
