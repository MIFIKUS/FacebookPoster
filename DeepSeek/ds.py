from openai import OpenAI

client = OpenAI(
    api_key='sk-a95950ca87be46069aded69e150c74e2',
    base_url="https://api.deepseek.com"
)

def change_text(post_text: str, group_name: str, posts: str, desc: str) -> str:
    """Меняет текст поста с помощью дипсика"""
    with open('DeepSeek\\promt.txt', 'r', encoding='utf-8') as txt:
        promt_raw = txt.read()
    
    promt = promt_raw.format(text=post_text, group_name=group_name, posts=posts, group_desc=desc)
    print(promt)
    return client.chat.completions.create(
        model='deepseek-reasoner',
        messages=[{'role': 'user', 'content': promt}],
        temperature=0.7,
        stream=False
    ).choices[0].message.content


