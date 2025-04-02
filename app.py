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
    # Use a more recent user agent
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
        
        # Debug to see what's on the page
        st.write("Page title:", driver.title)
        
        # Try multiple selector patterns to find images
        selectors = [
            "div.container--wYO8e div.images--0AI\\+S a img",  # First selector you provided
            "div.container--wYO8e div.results--mB75j div a img",  # Second selector you provided
            ".flex-grid a picture img",  # Another possible pattern
            "img.photo-result__image",   # Another possible pattern
            "a[href*='/images/'] img",   # All images within links to image pages
            "img[src*='pixabay.com']",   # All images from pixabay domain
            "img"                         # Fallback: all images
        ]
        
        image_urls = []
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                st.write(f"Found {len(elements)} elements with selector: {selector}")
                
                if elements:
                    for img in elements:
                        src = img.get_attribute("src")
                        if src and src.startswith("https://") and "pixabay.com" in src:
                            if src not in image_urls:  # Avoid duplicates
                                image_urls.append(src)
                    
                    if image_urls:  # If we found images with this selector, stop trying others
                        break
            except Exception as e:
                st.warning(f"Error with selector {selector}: {e}")
        
        # Take a screenshot to debug
        screenshot_path = "page_screenshot.png"
        driver.save_screenshot(screenshot_path)
        
        if os.path.exists(screenshot_path):
            st.image(screenshot_path, caption="Screenshot of the search page")
        
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://pixabay.com/"
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
            st.write("This could be because Pixabay is detecting and blocking the scraper.")
            st.write("As an alternative, let's try a different approach.")
            
            # Suggest alternatives
            st.info("""
            **Alternatives:**
            1. Try using the Pixabay API instead (requires registration but has a free tier)
            2. Try using a different scraping method with request headers that better mimic a browser
            3. Consider searching for images on a different site
            """)
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
- Web scraping may not always work due to website anti-scraping measures
- Please respect copyright and usage rights of images
""")