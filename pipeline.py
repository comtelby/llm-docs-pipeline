#!/usr/bin/env python3
"""
CLI entry point for one-shot report generation (no web server).
Usage:
    python pipeline.py [--config CONFIG_DIR] [--inventory INVENTORY_DIR] [--template TEMPLATE_FILE]
"""

import asyncio
import argparse
from pathlib import Path

from src.report import generate_report
from src.config import CONFIGS_DIR, UPLOAD_DIR, SAMPLES_DIR, OUTPUT_DIR
from src.database import init_db, seed_eol_to_inventories


async def main():
    parser = argparse.ArgumentParser(description="iqData Bot CLI — генерация отчёта")
    parser.add_argument("--config", type=str, default=str(CONFIGS_DIR), help="Папка с конфигами")
    parser.add_argument("--inventory", type=str, default=str(UPLOAD_DIR), help="Папка с inventory")
    parser.add_argument("--template", type=str, default="", help="Файл шаблона отчёта")
    parser.add_argument("--prompt", type=str, default="Проанализируй ИТ-инфраструктуру", help="Промпт")
    args = parser.parse_args()

    init_db()
    seed_eol_to_inventories()

    result = await generate_report(args.prompt)
    print(f"\n✅ Отчёт сохранён: {result['path']}")
    print(f"   Устройств: {result['devices']}, EOL critical: {result['eol_critical']}")


if __name__ == "__main__":
    asyncio.run(main())
