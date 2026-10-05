"""
Developer Utilities and AI Assistant examples using StdAPI (safone style).
Demonstrates Temp-Mail, QR Code generation, IP Geolocation, and AI chat.
"""
import asyncio
from stdapi import tools, ai, search


async def main():
    print("=" * 60)
    print("1. IP Geolocation Lookup")
    print("=" * 60)
    try:
        ip_info = await tools.ip()
        print(f"IP: {ip_info.get('ip')}")
        print(f"Location: {ip_info.get('city')}, {ip_info.get('country')}")
        print(f"Organization: {ip_info.get('org')}")
    except Exception as e:
        print(f"IP Lookup Error: {e}")

    print("\n" + "=" * 60)
    print("2. Disposable Temp-Mail Generation")
    print("=" * 60)
    try:
        mail = await tools.temp_mail()
        print(f"Generated Email: {mail.get('email')}")
        print(f"Login: {mail.get('login')}, Domain: {mail.get('domain')}")
    except Exception as e:
        print(f"Temp Mail Error: {e}")

    print("\n" + "=" * 60)
    print("3. QR Code Generator")
    print("=" * 60)
    try:
        qr = await tools.qr("https://github.com/STD-DEEPANSHU/StdAPI")
        print(f"QR Code Data URI: {qr.get('qr_image', '')[:60]}... (truncated)")
    except Exception as e:
        print(f"QR Error: {e}")

    print("\n" + "=" * 60)
    print("4. AI Intelligence Chat")
    print("=" * 60)
    try:
        ai_resp = await ai.chat("What are the key benefits of MTProto in Telegram?")
        print(f"AI Response: {ai_resp.get('response', '')[:200]}...")
    except Exception as e:
        print(f"AI Chat Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
