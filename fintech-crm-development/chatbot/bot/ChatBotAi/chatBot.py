import asyncio
import logging
import os
from dotenv import load_dotenv
import openai

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

cma_template = f"Information about the tax services that we offer:\
        Zerokar:-\
            Tax planning and filing done quickly using our Ai chat bot,- Harnessing AI-driven expertise, we elevate individuals, small businesses, and MSMEs to new heights by maximizing tax returns with effortless finesse.\
                Services:-\
                    - Personal Tax filing.\
                    - Small Business tax filing,\
                    - Tax planning, strategies and coaching\
                    - Financial Coaching\
        CMA:-\
            Credit Monitoring Arrangement (CMA) data is a very important area to understand by a person dealing with finance in an organisation.\
            It is a critical analysis of current & projected financial statements of a loan applicant by the banker.\
            The scientific analysis of a company’s existing and projected profit-generating capacity helps balance their sheet and portray a complete picture of their financial position.\
                Services:-\
                    Packages :-\
                        Essential-\
                            - Preparation of CMA Report for working capital limit upto INR 5 Lakh\
                            - Two responses to bank queries\
                            - Price- Rs. 999\
                        Enhanced-\
                            - Preparation of CMA Report for working capital limit upto INR 10 Lakh\
                            - Upto Three responses to bank queries\
                            - Price - 1499\
                        Ultimate-\
                            - Preparation of CMA Report for working capital limit upto INR 25 Lakh\
                            - Upto Four responses to bank queries\
                            - Price - 2499.>"
openai.api_key = OPENAI_API_KEY


async def get_AI_response(input:str, model="gpt-3.5-turbo"):
    prompt = f"""
        You are a Whatsapp chatBot specialized in tax-related inquiries for services that we offer. \
        
        Summarize the tax services that we offer described below, delimited by double
        backticks, and return response for userinput in under 25-30 words.

        tax services: ``{cma_template}``
        userinput: ```{input}```

        If userinput is not releated to tax services then return response 
        'Hello! I'm a Whatsapp chatbot🤖 specialized in tax-related inquiries.If your question is not related to taxes, I'm afraid I won't be able to assist you.'. \
        """
    messages = [{"role": "user", "content": prompt}]
    try:
        task = openai.ChatCompletion.acreate(
            model=model,
            messages=messages,
            temperature=0, # this is the degree of randomness of the model's output
        )
        response = await asyncio.wait_for(task, timeout=10)
        return response.choices[0].message["content"]
    except asyncio.TimeoutError:
        logging.error("Request timed out.")
        return "🤖 Apologies, it seems that I'm taking longer to respond. Please Start Again."

    except Exception as e:
        logging.error("Get message failed" + str(e))