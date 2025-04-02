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
st.set_page_config(page_title="Image Search App", layout="wide")
st.title("Image Search Application")

# Create a directory to save images if it doesn't exist
if not os.path.exists("downloaded_images"):
    os.makedirs("downloaded_images")

# Setup Chrome options
@st.cache_resource
def get_webdriver_options():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36")
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
        
        # Find image elements
        img_elements = driver.find_elements(By.CSS_SELECTOR, ".image_list img")
        
        image_urls = []
        for img in img_elements:
            src = img.get_attribute("src")
            if src and src.startswith("https://"):
                # For Pixabay, try to get higher resolution images
                # Replace the preview URL with the larger image URL
                image_urls.append(src)
        
        return image_urls[:20]  # Limit to 20 images
    
    except Exception as e:
        st.error(f"Error scraping images: {e}")
        return []
    
    finally:
        # Make sure to close the driver
        if 'driver' in locals():
            driver.quit()

def download_image(url):
    """Download an image from a URL and return a PIL Image object"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        return img
    except Exception as e:
        st.warning(f"Couldn't download image from {url}: {e}")
        return None

# User input
search_query = st.text_input("Enter search terms (e.g., mountains with sunset)")

# Search button
if st.button("Search Images") and search_query:
    with st.spinner(f"Searching for images related to '{search_query}'..."):
        # Get image URLs
        image_urls = search_pixabay(search_query)
        
        if not image_urls:
            st.warning("No images found. Try a different search term.")
        else:
            st.success(f"Found {len(image_urls)} images")
            
            # Display images in a grid
            cols = st.columns(3)  # 3 columns for desktop view
            
            for i, img_url in enumerate(image_urls):
                # Add a small delay between requests to be respectful
                time.sleep(0.2 + random.random() * 0.5)
                
                with cols[i % 3]:
                    try:
                        img = download_image(img_url)
                        if img:
                            # Display the image
                            st.image(img, use_column_width=True)
                            
                            # Add a button to save the image
                            save_key = f"save_{i}"
                            if st.button(f"Save Image {i+1}", key=save_key):
                                # Create a valid filename
                                filename = f"{search_query.replace(' ', '_')}_{i+1}.jpg"
                                save_path = os.path.join("downloaded_images", filename)
                                
                                # Save the image
                                img.save(save_path)
                                st.success(f"Image saved to {save_path}")
                    except Exception as e:
                        st.error(f"Error with image {i+1}: {e}")

# Add information and disclaimers
st.markdown("---")
st.markdown("""
### Instructions:
1. Enter your search terms in the text box
2. Click "Search Images" to find relevant images
3. Click "Save Image" under any image you want to download

### Notes:
- This app is for educational purposes only
- Please respect copyright and usage rights of images
- Images are saved to a 'downloaded_images' folder in your current directory
""")