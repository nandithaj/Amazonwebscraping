import requests
from bs4 import BeautifulSoup
import psycopg2

# Database connection
try:
    conn = psycopg2.connect(
        dbname="scraper_db",
        user="postgres",
        password="123456",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    print("Database connection successful!")
except Exception as e:
    print(f"Error connecting to the database: {e}")
    exit()

# Scraping setup
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
    
    for index, product in enumerate(products, start=1):  # Enumerate to track ranking

        ranking = index
        try:
            # Extract brandname
            brandname = product.find("h2", class_="a-size-base-plus")
            brandname = brandname.text.strip() if brandname else "N/A"
            brandname=brandname.split(' ')[0] if brandname else "N/A"
            
            # Extract price
            price_element = product.find("span", class_="a-price-whole")

            if price_element:
                try:
                    # Extract and clean the price
                    price = int(price_element.text.strip().replace(",", ""))
                except ValueError:
                    # Handle cases where the price cannot be converted
                    print(f"Price parsing error: {price_element.text.strip()}")
                    price = None  # Or assign a default value, e.g., 0
            else:
                # Handle missing price
                price = None
            
            # Extract rating
            rating = product.find("span", class_="a-icon-alt")
            rating = rating.text.strip() if rating else "N/A"
            # Extract numeric part and convert to float
            rating = float(rating.split(' ')[0] if rating != "N/A" else 0.0)
            
            # Extract rating count
            ratingcount_element = product.find("span", class_="a-size-base")

            if ratingcount_element:
                # Extract the text and filter out digits
                ratingcount_text = ratingcount_element.text.strip()
                # Check if there are digits in the extracted text
                if any(char.isdigit() for char in ratingcount_text):
                    # Extract only digits and convert to integer
                    ratingcount = int(''.join(filter(str.isdigit, ratingcount_text)))
                else:
                    # Assign 0 if no digits are found
                    ratingcount = 0
            else:
                # Assign 0 if the element is missing
                ratingcount = 0

            # Debugging
            print(f"Extracted rating count: {ratingcount}")

            # Extract URL
            product_url = product.find("a", class_="a-link-normal")
            product_url = f"https://www.amazon.in{product_url['href']}" if product_url else "N/A"
            
            # Insert data into database
            cursor.execute(
                """
            INSERT INTO products (brandname, price, rating, ratingcount, ranking, url)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (brandname, price, rating, ratingcount,ranking, product_url)
            )
            conn.commit()
            
                # Print product details
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

# Close database connection
cursor.close()
conn.close()
print("Database connection closed!")
