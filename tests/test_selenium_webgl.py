from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys
import os


# Get the absolute path to the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Add the project root and src directory to the Python path
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from chrome_webgl_fingerprinting_protection import modify_webgl_vendor_renderer


def test_webgl_spoofing():
    # Set up Chrome
    chrome_options = Options()
    driver = webdriver.Chrome(options=chrome_options)

    # Apply our modification
    driver = modify_webgl_vendor_renderer(driver)

    # Test JavaScript to check the values
    test_script = """
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl');

    const vendor = gl.getParameter(37445);
    const renderer = gl.getParameter(37446);

    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    const unmaskedVendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
    const unmaskedRenderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);

    return {
        vendor,
        renderer,
        unmaskedVendor,
        unmaskedRenderer
    }
    """

    try:
        driver.get("about:blank")
        result = driver.execute_script(test_script)
        print("WebGL information after spoofing:")
        print(f"Vendor: {result['vendor']}")
        print(f"Renderer: {result['renderer']}")
        print(f"Unmasked Vendor: {result['unmaskedVendor']}")
        print(f"Unmasked Renderer: {result['unmaskedRenderer']}")
    finally:
        driver.quit()


if __name__ == '__main__':
    test_webgl_spoofing()
