import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_spending_advice(transactions_text):
    prompt = f"""
    You are a personal finance AI. Analyze the following transactions.
    Provide:
    - Overspending categories
    - Spending trends
    - 3–5 actionable saving suggestions
    - A simple summary of the user's financial health

    Transactions:
    {transactions_text}

    Format response in clean bullet points.
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a financial analysis assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )

        return completion.choices[0].message.content

    except Exception as e:
        return f"AI error: {str(e)}"

