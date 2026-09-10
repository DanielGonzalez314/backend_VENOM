import logging

logger = logging.getLogger("VenomEngine")

async def generate_chat_title(query: str, groq_client) -> str:
    try:
        resp = await groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": f"Título máximo 5 palabras: {query}"}],
            max_tokens=15,
            temperature=0.5
        )
        title = resp.choices[0].message.content.strip().strip('"')
        return title[:50]
    except Exception:
        return query[:30]