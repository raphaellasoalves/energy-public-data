# -*- coding: utf-8 -*-
# @Author: Raphaella Alves
# @Date:   2025-12-11 15:09:47
# @Last Modified by:   Raphaella Alves
# @Last Modified time: 2025-12-17 11:52:44

"""
Crawler — ANP: Exploratory Phase Panel (Blocos sob Contrato)
-------------------------------------------------------------
Source : ANP Power BI public dashboard
Output : output/anp_blocks_under_contract.xlsx
"""

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

URL = "https://app.powerbi.com/view?r=eyJrIjoiYTEzY2U5YzItNzY0MC00NTgxLWExYjktODUwZGI0ZjJhNjIzIiwidCI6IjQ0OTlmNGZmLTI0YTYtNGI0Mi1iN2VmLTEyNGFmY2FkYzkxMyJ9"

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
OUTPUT_EXCEL = os.path.join(OUTPUT_DIR, "anp_blocks_under_contract.xlsx")

COL_NAMES = [
    "block", "contract", "operator", "concessionaires", "environment",
    "grouped_basins", "basin", "area_mil_km2", "round",
    "contractual_arrangement", "period", "pad_presence", "signature_date",
    "suspension_start_date", "1st_pe_deadline", "2nd_pe_deadline",
    "3rd_pe_deadline", "last_pad_deadline", "exploratory_phase_expiration",
    "committed_uts", "quantity_drilled_wells", "drilled_wells",
]

LEFT_TOLERANCE = 2.0
DEFAULT_MAX_HORIZONTAL_STEPS = 15


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


def varrer_vertical(driver, scroll_host, celulas_total: dict):
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


def calcular_passo_horizontal(driver, scroll_host, horizontal_bar, max_horizontal_steps):
    try:
        track = horizontal_bar.find_element(By.XPATH, "..")
        track_rect = track.rect
        bar_rect = horizontal_bar.rect
        track_width = track_rect["width"]
        bar_width = bar_rect["width"]
        max_drag = track_width - bar_width
        if max_drag <= 0:
            viewport_width = driver.execute_script("return arguments[0].clientWidth;", scroll_host)
            step_drag = max(viewport_width * 0.5, 100)
        else:
            step_drag = max_drag / float(max_horizontal_steps)
        return step_drag
    except Exception:
        return 200.0


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 40)
    actions = ActionChains(driver)

    try:
        driver.get(URL)
        time.sleep(8)

        hint = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//p[contains(@class,'visualsEnterHint') and contains(normalize-space(),'Blocos sob Contrato')]"
        )))
        visual_container = hint.find_element(By.XPATH, "./ancestor::div[contains(@class,'visualContainer')][1]")
        actions.move_to_element(visual_container).click().perform()

        wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//span[contains(@class,'textRun') and contains(normalize-space(.),'Blocos sob Contrato') and contains(normalize-space(.),'Visão Geral')]"
        )))
        time.sleep(2)

        tabela_container = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//div[contains(@class,'visualContainer') and @role='link' and @tab-order='34000']"
        )))

        rect = tabela_container.rect
        label_cx = rect["x"] + rect["width"] / 2
        label_cy = rect["y"] + rect["height"] / 2
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tabela_container)
        time.sleep(1)

        containers = driver.find_elements(By.XPATH, "//div[contains(@class,'visualContainer') and @role='link']")
        best_elem, best_dist2 = None, None
        for cont in containers:
            r = cont.rect
            cx = r["x"] + r["width"] / 2
            cy = r["y"] + r["height"] / 2
            dist2 = (cx - label_cx) ** 2 + (cy - label_cy) ** 2
            if best_dist2 is None or dist2 < best_dist2:
                best_dist2 = dist2
                best_elem = cont

        if best_elem is None:
            return

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", best_elem)
        time.sleep(1)
        actions.move_to_element(best_elem).click().perform()
        time.sleep(6)

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

        max_horizontal_steps = DEFAULT_MAX_HORIZONTAL_STEPS
        drag_step_px = calcular_passo_horizontal(driver, scroll_host, horizontal_bar, max_horizontal_steps)
        actions = ActionChains(driver)

        celulas_total = {}
        horizontal_step = 0
        left_atual = get_container_left(scroll_host)

        while horizontal_step < max_horizontal_steps:
            horizontal_step += 1
            varrer_vertical(driver, scroll_host, celulas_total)
            driver.execute_script("arguments[0].scrollTop = 0;", scroll_host)
            time.sleep(0.3)
            try:
                focus_cell = scroll_host.find_element(By.CSS_SELECTOR, "div[role='gridcell'].cell-interactive.main-cell")
                driver.execute_script("arguments[0].click();", focus_cell)
                time.sleep(0.2)
            except Exception:
                break
            try:
                actions.click_and_hold(horizontal_bar).move_by_offset(drag_step_px, 0).release().perform()
            except StaleElementReferenceException:
                horizontal_bar = encontrar_barra_horizontal(driver)
                if not horizontal_bar:
                    break
                actions = ActionChains(driver)
                actions.click_and_hold(horizontal_bar).move_by_offset(drag_step_px, 0).release().perform()
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
        valid_cols = sorted(c for c in df_cells["col_idx"].unique() if c is not None and int(c) >= 2)
        if not valid_cols:
            return
        col_order = valid_cols[:len(COL_NAMES)]
        col_names_to_use = COL_NAMES[:len(col_order)]
        tabela = tabela.reindex(columns=col_order).sort_index()
        tabela.columns = col_names_to_use
        tabela = tabela.reset_index(drop=True)
        tabela.to_excel(OUTPUT_EXCEL, index=False)
        print(f"Arquivo salvo em: {OUTPUT_EXCEL}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
