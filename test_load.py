#!/usr/bin/env python3
"""Скрипт для проверки загруженных данных"""
import asyncio
from database import Database

async def check_data():
    db = Database()
    
    all_chars = await db.get_all()
    
    print("\n" + "="*70)
    print("📊 VERIFICATION OF LOADED DATA")
    print("="*70)
    
    if not all_chars:
        print("❌ No data found! Run main.py first.")
        return
    
    print(f"\n✅ Total characters in DB: {len(all_chars)}\n")
    
    print("First 5 characters:")
    print("-"*70)
    
    for i, row in enumerate(all_chars[:5]):
        print(f"\n{i+1}. {row[2]} (ID: {row[1]})")
        print(f"   👁️  Eye color: {row[4]}")
        print(f"   🧬 Gender: {row[5]}")
        print(f"   💇 Hair color: {row[6]}")
        print(f"   🌍 Homeworld: {row[7]}")  # Должно быть название!
        print(f"   🎬 Films: {row[11]}")
    
    await db.close()

if __name__ == "__main__":
    asyncio.run(check_data())
