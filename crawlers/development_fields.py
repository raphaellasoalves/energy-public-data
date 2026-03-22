# -*- coding: utf-8 -*-
# @Author: Raphaella Alves

"""
Crawler — ANP: Development Fields Panel (Campos em Desenvolvimento)
--------------------------------------------------------------------
Source : ANP Power BI public dashboard
Output : output/anp_development_fields.xlsx
"""

import sys
import time
import re
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

sys.stdout.reconfigure(encoding='utf-8')

URL = "https://app.powerbi.com/view?r=eyJrIjoiNDEyMThjYjgtYjc1ZC00ZmFjLWI4YTYtZmI3ZDI2ZjVjMjI4IiwidCI6IjQ0OTlmNGZmLTI0YTYtNGI0Mi1iN2VmLTEyNGFmY2FkYzkxMyJ9"

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
OUTPUT_EXCEL = os.path.join(OUTPUT_DIR, "anp_development_fields.xlsx")

LEFT_TOLERANCE = 2.0
MAX_HORIZONTAL_STEPS = 10
HORIZONTAL_DRAG_OFFSET = 200

COL_ORDER = list(range(2, 21))
COL_NAMES = [
    "field", "acronym", "basin", "state", "operator", "environment",
    "round", "contract_name", "contract_number", "water_depth_m",
    "status", "signature_date", "terminal_fase_date",
    "production_start_date", "production_end_date",
    "marginal_field", "mature_field", "small_medium_field",
    "extension_production_fase",
]


def parse_left(style_str: str) -> float:
    if not style_str:
        return 0.0
    m = re.search(r"left:\s*([\-0-9\.]+)px", style_str)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return 0.0
    return 0.0


def get_container_left(scroll_host) -> float:
    try:
        container = scroll_host.find_element(By.CSS_SELECTOR, "div.scrollable-cells-container")
        style = container.get_attribute("style") or ""
        return parse_left(style)
    except Exception:
        return 0.0


def coletar_celulas(scroll_host):
    resultados = []
    try:
        rows = scroll_host.find_elements(By.CSS_SELECTOR, "div[role='row']")
        for r in rows:
            try:
                row_idx = r.get_attribute("aria-rowindex")
                if not row_idx:
                    continue
                row_idx = int(row_idx)
                cells = r.find_elements(By.CSS_SELECTOR, "div[role='gridcell']")
                for c in cells:
                    classes = c.get_attribute("class") or ""
                    if "prefix-cell" in classes:
                        continue
                    col_idx = c.get_attribute("aria-colindex")
                    if not col_idx:
                        continue
                    col_idx = int(col_idx)
                    txt = c.text.strip()
                    resultados.append((row_idx, col_idx, txt))
            except StaleElementReferenceException:
                continue
    except Exception:
        pass
    return resultados


def varrer_vertical(driver, scroll_host, celulas_total):
    driver.execute_script("arguments[0].scrollTop = 0;", scroll_host)
    time.sleep(0.3)
    viewport_height = driver.execute_script("return arguments[0].clientHeight;", scroll_host)
    scroll_step_v = int(viewport_height * 0.85)
    pos_v_anterior = -1.0
    sem_mudanca_v = 0
    while True:
        novas = coletar_celulas(scroll_host)
        for r_idx, c_idx, txt in novas:
            key = (r_idx, c_idx)
            if key not in celulas_total or (txt and not celulas_total[key]):
                celulas_total[key] = txt
        driver.execute_script("arguments[0].scrollTop += arguments[1];", scroll_host, scroll_step_v)
        time.sleep(0.4)
        pos_v_atual = float(driver.execute_script("return arguments[0].scrollTop;", scroll_host))
        if abs(pos_v_atual - pos_v_anterior) < 1e-2:
            sem_mudanca_v += 1
            if sem_mudanca_v >= 2:
                break
        else:
            sem_mudanca_v = 0
        pos_v_anterior = pos_v_atual


def encontrar_barra_horizontal(driver):
    scroll_bars = driver.find_elements(By.CSS_SELECTOR, "div.scroll-bar-div div.scroll-bar-part-bar")
    if not scroll_bars:
        return None
    for bar in scroll_bars:
        style = bar.get_attribute("style") or ""
        if "height: 9px" in style:
            return bar
    return scroll_bars[0]


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--headless=new")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 40)
    celulas_total = {}

    try:
        driver.get(URL)
        time.sleep(8)

        next_btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button[aria-label='Next Page']")
        ))
        next_btn.click()
        time.sleep(2)

        primeira_celula = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div[role='gridcell'].cell-interactive.main-cell")
        ))
        driver.execute_script("arguments[0].click();", primeira_celula)
        time.sleep(1)

        focus_btn = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "button[data-testid='focus-mode-btn']")
        ))
        driver.execute_script("arguments[0].click();", focus_btn)
        time.sleep(5)

        scroll_host = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.mid-viewport")))
        horizontal_bar = encontrar_barra_horizontal(driver)
        if not horizontal_bar:
            return

        actions = ActionChains(driver)
        horizontal_step = 0
        left_atual = get_container_left(scroll_host)

        while horizontal_step < MAX_HORIZONTAL_STEPS:
            horizontal_step += 1
            varrer_vertical(driver, scroll_host, celulas_total)
            driver.execute_script("arguments[0].scrollTop = 0;", scroll_host)
            time.sleep(0.3)

            try:
                focus_cell = scroll_host.find_element(
                    By.CSS_SELECTOR, "div[role='gridcell'].cell-interactive.main-cell"
                )
                driver.execute_script("arguments[0].click();", focus_cell)
                time.sleep(0.2)
            except Exception:
                break

            try:
                actions.click_and_hold(horizontal_bar).move_by_offset(HORIZONTAL_DRAG_OFFSET, 0).release().perform()
            except StaleElementReferenceException:
                horizontal_bar = encontrar_barra_horizontal(driver)
                if not horizontal_bar:
                    break
                actions = ActionChains(driver)
                actions.click_and_hold(horizontal_bar).move_by_offset(HORIZONTAL_DRAG_OFFSET, 0).release().perform()

            time.sleep(1.0)
            left_novo = get_container_left(scroll_host)
            if abs(left_novo - left_atual) < LEFT_TOLERANCE:
                break
            left_atual = left_novo

        if not celulas_total:
            return

        registros = [{"row_idx": r, "col_idx": c, "value": txt} for (r, c), txt in celulas_total.items()]
        df_cells = pd.DataFrame(registros)
        tabela = df_cells.pivot(index="row_idx", columns="col_idx", values="value")
        tabela = tabela.reindex(columns=COL_ORDER).sort_index()
        tabela.columns = COL_NAMES
        tabela = tabela.reset_index(drop=True)
        tabela.to_excel(OUTPUT_EXCEL, index=False)
        print(f"Arquivo salvo em: {OUTPUT_EXCEL}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
