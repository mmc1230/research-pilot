import os

from dotenv import load_dotenv
from openai import OpenAI


def main() -> None:
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL", "deepseek-v4-pro")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Put your DeepSeek API key in .env.")
    if not base_url:
        raise RuntimeError("OPENAI_BASE_URL is not set. For DeepSeek, use https://api.deepseek.com.")

    client = OpenAI(api_key=api_key, base_url=base_url)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "请回复：DeepSeek API 测试成功"}],
    )
    print(resp.choices[0].message.content)


if __name__ == "__main__":
    main()
