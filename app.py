import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import requests
from PIL import Image
from io import BytesIO
import os

# Set page configuration
st.set_page_config(page_title="Image Search", layout="wide")
st.title("Image Search")

# Create a directory to save images if it doesn't exist
if not os.path.exists("downloaded_images"):
    os.makedirs("downloaded_images")

# Setup Chrome options
@st.cache_resource
def get_webdriver_options():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    return chrome_options

def search_pixabay(query):
    """Search Pixabay for images related to the query"""
    formatted_query = query.replace(" ", "+")
    url = f"https://pixabay.com/images/search/{formatted_query}/"
    
    chrome_options = get_webdriver_options()
    
    try:
        # Initialize the driver with webdriver-manager
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        # Navigate to the search page
        driver.get(url)
        
        # Wait for the page to load
        time.sleep(5)
        
        # Use the working selectors
        selectors = [
            "div.container--wYO8e div.images--0AI\\+S a img",
            "div.container--wYO8e div.results--mB75j div a img",
            "a[href*='/images/'] img",
            "img[src*='pixabay.com']"
        ]
        
        image_urls = []
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if elements:
                    for img in elements:
                        src = img.get_attribute("src")
                        if src and src.startswith("https://") and "pixabay.com" in src:
                            if src not in image_urls:  # Avoid duplicates
                                image_urls.append(src)
                    
                    if image_urls:  # If we found images with this selector, stop trying others
                        break
            except Exception:
                pass
        
        return image_urls[:20]  # Limit to 20 images
    
    except Exception as e:
        st.error(f"Error finding images: {e}")
        return []
    
    finally:
        # Make sure to close the driver
        if 'driver' in locals():
            driver.quit()

def download_image(url):
    """Download an image from a URL and return a PIL Image object"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://pixabay.com/"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        st.warning(f"Couldn't download image: {e}")
        return None

# User input and search button in the same row
col1, col2 = st.columns([3, 1])
with col1:
    search_query = st.text_input("Enter search terms", placeholder="mountains with sunset")
with col2:
    search_button = st.button("Search Images", use_container_width=True)

# Search functionality
if search_button and search_query:
    with st.spinner(f"Searching for '{search_query}'..."):
        # Get image URLs
        image_urls = search_pixabay(search_query)
        
        if not image_urls:
            st.warning("No images found. Try a different search term.")
        else:
            # Display images in a grid
            cols = st.columns(3)  # 3 columns for desktop view
            
            for i, img_url in enumerate(image_urls):
                # Add a small delay between requests
                time.sleep(0.2 + random.random() * 0.3)
                
                with cols[i % 3]:
                    try:
                        img = download_image(img_url)
                        if img:
                            # Display the image
                            st.image(img, use_column_width=True)
                            
                            # Add a clean download button
                            filename = f"{search_query.replace(' ', '_')}_{i+1}.jpg"
                            save_path = os.path.join("downloaded_images", filename)
                            
                            if st.button("Download", key=f"dl_{i}"):
                                img.save(save_path)
                                st.success(f"Saved to {filename}")
                    except Exception:
                        pass