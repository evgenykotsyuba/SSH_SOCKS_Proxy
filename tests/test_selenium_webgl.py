from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys
import os
import logging
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Получение абсолютного пути к корню проекта
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

# Добавление корня проекта и директории src в Python path
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

from chrome_webgl_fingerprinting_protection import modify_webgl_vendor_renderer, modify_webgl_textures


def setup_driver():
    """Настройка и запуск WebDriver с дополнительными параметрами."""
    chrome_options = Options()
    chrome_options.add_argument("--disable-web-security")  # Для тестирования кросс-доменных запросов
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Скрываем автоматизацию
    chrome_options.add_argument("--no-sandbox")  # Для работы в контейнерах
    chrome_options.add_argument("--disable-dev-shm-usage")  # Для ограниченных ресурсов
    chrome_options.add_argument("--headless")  # Запуск в фоновом режиме (опционально)

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def get_webgl_info(driver):
    """Получение информации о WebGL через JavaScript."""
    test_script = """
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');

    if (!gl) {
        return { error: 'WebGL not supported' };
    }

    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    const parameters = {
        VENDOR: gl.getParameter(37445),
        RENDERER: gl.getParameter(37446),
        VERSION: gl.getParameter(37447),
        MAX_TEXTURE_SIZE: gl.getParameter(3379),
        UNMASKED_VENDOR: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'N/A',
        UNMASKED_RENDERER: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'N/A',
        SHADING_LANGUAGE_VERSION: gl.getParameter(35724),
        SUPPORTED_EXTENSIONS: gl.getSupportedExtensions()
    };

    return parameters;
    """
    return driver.execute_script(test_script)


def test_webgl_spoofing():
    """Основной тест для проверки подмены WebGL."""
    driver = setup_driver()
    driver = modify_webgl_vendor_renderer(driver)

    try:
        driver.get("about:blank")
        webgl_info = get_webgl_info(driver)

        if "error" in webgl_info:
            logger.error(webgl_info["error"])
            return

        logger.info("WebGL информация после подмены:")
        logger.info(json.dumps(webgl_info, indent=4))

        # Проверка ожидаемых значений
        expected_vendor = "NVIDIA Corporation"
        expected_renderer = "NVIDIA GeForce GTX 1080 Ti/PCIe/SSE2"

        assert webgl_info["VENDOR"] == expected_vendor, f"Vendor mismatch: {webgl_info['VENDOR']}"
        assert webgl_info["RENDERER"] == expected_renderer, f"Renderer mismatch: {webgl_info['RENDERER']}"
        assert webgl_info["UNMASKED_VENDOR"] == expected_vendor, f"Unmasked Vendor mismatch: {webgl_info['UNMASKED_VENDOR']}"
        assert webgl_info["UNMASKED_RENDERER"] == expected_renderer, f"Unmasked Renderer mismatch: {webgl_info['UNMASKED_RENDERER']}"

        logger.info("Все проверки пройдены успешно!")
    except AssertionError as e:
        logger.error(f"Ошибка проверки: {e}")
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    test_webgl_spoofing()
