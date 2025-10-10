"""
ai operations module
"""

import datetime
import os
import re
from time import sleep
from typing import Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from data.database_repository import DatabaseRepository


def get_database_repository():
    """
    dependency to get the DatabaseRepository instance.
    This allows for easy testing and mocking of the repository.
    """

    return DatabaseRepository()


def get_llm_client() -> ChatGoogleGenerativeAI:
    """
    create llm client using langchain
    """

    load_dotenv()

    # langchain setup
    client = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
    return client


class AIService:
    """
    AI service class for handling AI and LLM operations
    """

    def __init__(self):
        self.llm_client = get_llm_client()
        self.database_repository = get_database_repository()
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/127.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
            "DNT": "1",  # Do Not Track
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

        # Request session for better performance
        self.session = requests.Session()

        # Common "about us" page patterns
        self.about_patterns = [
            "about",
            "about-us",
            "about_us",
            "company",
            "who-we-are",
            "our-story",
            "our-company",
            "team",
            "mission",
            "vision",
        ]

        # cache rate limiter for llm calls
        self.llm_rate_limiter = {
            "calls": 0,
            "max_calls": 10,
            "reset_time": 60000,  # 1 min in ms
            "last_call_time": 0,  # timestamp of last call
        }

        self.parser = JsonOutputParser()

    def scrape_website(self, url: str, timeout: int = 10):
        """
        Scrape website content using BeautifulSoup. Returns only the body from the HTML content.
        """
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url

            response = self.session.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            return soup
        except Exception as e:
            print(f"Error scraping website {url}: {e}")
            return None

    async def find_about_page_with_llm(
        self, html_content: str, base_url: str
    ) -> Optional[str]:
        """
        Use LangChain with Google Gemini 2.0 Flash to find the "About Us" page link from the HTML content.
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that extracts the 'About Us' page link from a website's HTML content."
                        "The 'About Us' page typically contains information about the company, its mission, values, and team."
                        "Look for common patterns in the URLs such as 'about', 'about-us', 'about_us', 'company', 'our-company', 'who-we-are', 'our-story', 'team', 'mission', 'vision', 'contact', 'contact-us' etc. "
                        "The link may not always have the exact keywords aforementioned but they may be accompanied by text before, inside, after or somewhere around the HTML anchor tag. "
                        "For example: <a href='http://example.com/page2'>Contact Us</a>."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Here is the HTML content of a website:\n\n{html_content}\n\n"
                        "Please identify and return the full URL of the 'About Us' page."
                        "If no such page exists or the URL found returns or contains 404 or 'page can't be found' type of message in its content, try to find the closest alternative that could serve a similar purpose. "
                        "Do not try to guess or fabricate URLs. Only return URLs that are explicitly present in the HTML content provided and that might lead to an 'About Us' page or similar. "
                        "If no similar alternatives are found, respond with 'None' and no additional text. "
                        "If the URL is found, return the URL and how you found it in a JSON object with the key 'about_page'. and the reasoning on how you found it with the key 'reasoning'. "
                        "Your entire response must be a single JSON object, and you will NOT wrap it within JSON markdown markers or any other formatting. "
                        'Example of acceptable JSON response format: {"about_page": "http://example.com/about", "reasoning": "Found in the footer section of the HTML content, inside an <a> tag."}. '
                        'Example of not acceptable JSON response format: ```json {"about_page": "http://example.com/about", "reasoning": "Found in the footer section of the HTML content, inside an <a> tag."} ```.'
                    ),
                },
            ]
            ai_response = self.llm_client.invoke(messages)
            if not ai_response or not ai_response.content:
                return None

            print(
                f"LLM response type: {type(ai_response.content)} | content: {ai_response.content}"
            )
            # convert response content from string to dict
            about_page_path = self.parser.parse(ai_response.content)

            # Normalize content type
            if isinstance(about_page_path, dict):  # if model returned JSON
                # Try common key names
                about_page_path = (
                    about_page_path.get("about_page")
                    or about_page_path.get("url")
                    or about_page_path.get("link")
                )
            elif isinstance(about_page_path, (list, tuple)):
                about_page_path = about_page_path[0]

            if not about_page_path:
                return None

            about_page_path = str(about_page_path).strip()

            if about_page_path.lower() == "none":
                return None

            # If it's already a full URL
            if about_page_path.startswith(("http://", "https://")):
                return about_page_path

            # Otherwise, resolve relative to base_url
            if base_url.endswith("/") and about_page_path.startswith("/"):
                return base_url[:-1] + about_page_path
            elif not base_url.endswith("/") and not about_page_path.startswith("/"):
                return base_url + "/" + about_page_path
            else:
                return base_url + about_page_path
        except Exception as e:
            print(f"Error finding about page with LLM: {e}")
            return None

    async def generate_summary_with_llm(self, html_content: str) -> Optional[str]:
        """
        Use LangChain with Google Gemini 2.0 Flash to generate a summary from the HTML content.
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that generates concise summaries of 'About Us' pages. "
                        "Avoid meta-language such as 'This page provides...' or 'The website says...'. "
                        "Focus only on the mission, values, and key activities. "
                        "Keep the summary to 3–4 sentences, neutral, and to the point. "
                        "Avoid using third-person pronouns like 'they' or 'them'. "
                        "Keep the summary brief, factual, and to the point. "
                        "Write in a neutral, descriptive tone, as if summarizing the core content of the page itself."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Here is the HTML content of a company's 'About Us' page:\n\n{html_content}\n\n"
                        "Please generate a concise 3–4 sentence summary that captures the organization's mission, focus areas, and key activities. "
                        "Do not include references to contact forms, donation buttons, QR codes, or maps."
                    ),
                },
            ]
            ai_response = self.llm_client.invoke(messages)
            if ai_response and ai_response.content:
                return ai_response.content.strip()
            return None
        except Exception as e:
            print(f"Error generating summary with LLM: {e}")
            return None

    async def generate_hashtags_with_llm(self, about_text: str) -> Optional[str]:
        """
        Use LangChain with Google Gemini 2.0 Flash to generate hashtags from the about text.
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that generates relevant hashtags based on the provided text. "
                        "Extract key themes, topics, and concepts from the text and convert them into concise hashtags. "
                        "Each hashtag should be a single word or a short phrase without spaces, prefixed with the '#' symbol, all lowercase."
                        "Avoid using special characters or punctuation in the hashtags. "
                        "Generate a random number of hashtags between 1 to 4 that best represent the content of the text."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Here is the about text:\n\n{about_text}\n\n"
                        "Please generate a random number of relevant hashtags between 1 to 4 that capture the main themes and topics of this text."
                    ),
                },
            ]
            ai_response = self.llm_client.invoke(messages)
            if ai_response and ai_response.content:
                # Extract hashtags from response content
                hashtags = re.findall(r"#\w+", ai_response.content)
                return " ".join(hashtags) if hashtags else None
            return None
        except Exception as e:
            print(f"Error generating hashtags with LLM: {e}")
            return None

    def write_to_text_file(self, filename: str, content: str):
        """
        write content to text file
        """
        try:
            with open(filename, "w") as file:
                file.write(content)
            print(f"Successfully wrote content to {filename}")
        except Exception as e:  # pylint: disable=broad-except
            print(f"Error writing to file {filename}: {e}")

    async def generate_entity_summary(self):
        """
        generate about summary using llm for all entities in the database based on their website
        """
        try:
            entities = await self.database_repository.get_entities(
                page_number=1, page_size=-1
            )
            if not entities:
                print(f"Error getting all entities: {entities}")
                return None

            for entity in entities:
                if entity["about"]:
                    print(
                        f"Entity id: {entity['id']} - {entity['name']} already has an about summary. Skipping."
                    )
                    continue
                else:
                    if (
                        self.llm_rate_limiter["calls"]
                        >= self.llm_rate_limiter["max_calls"]
                    ):
                        print(
                            "LLM rate limit reached. Please wait before making more requests."
                        )
                        sleep(60)
                        self.llm_rate_limiter["calls"] = 0
                        self.llm_rate_limiter["last_call_time"] = 0
                    if not self.llm_rate_limiter["last_call_time"]:
                        self.llm_rate_limiter["last_call_time"] = (
                            datetime.datetime.now().timestamp()
                        )
                    if (
                        datetime.datetime.now().timestamp()
                        - self.llm_rate_limiter["last_call_time"]
                    ) * 1000 > self.llm_rate_limiter["reset_time"]:
                        self.llm_rate_limiter["calls"] = 0
                        self.llm_rate_limiter["last_call_time"] = (
                            datetime.datetime.now().timestamp()
                        )

                    if entity["about_page"]:
                        print(
                            f"About page found: {entity['about_page']} for entity id: {entity['id']} - {entity['name']}"
                        )
                        # call llm to generate summary based on about page
                        ai_about_summary = await self.generate_summary_with_llm(
                            str(self.scrape_website(entity["about_page"]))
                        )
                        self.llm_rate_limiter["calls"] += 1
                        if not ai_about_summary:
                            print(
                                f"Failed to generate summary for entity id: {entity['id']}"
                            )
                            continue
                        # save summary in entities "about" column
                        await self.database_repository.update_entity_by_id(
                            entity["id"], {"about": ai_about_summary}
                        )
                        print(
                            f"Successfully generated summary using llm for entity id: {entity['id']} | Summary: {ai_about_summary}"
                        )
                    elif entity["website"]:
                        print(
                            f"Website found: {entity['website']} for entity id: {entity['id']} - {entity['name']}"
                        )
                        # 1. use beautifulsoup to scrape website
                        soup = self.scrape_website(entity["website"])
                        if not soup:
                            print(
                                f"Failed to scrape website for entity id: {entity['id']} - {entity['name']}"
                            )
                            continue
                        print(f"Scrapped website content: {str(soup)[:500]}...")
                        self.write_to_text_file(
                            f"entity_{entity['id']}_website.html", str(soup)
                        )
                        # remove everything from the entity website except for the hostname, domain, www and the first trailing slash
                        base_url = re.match(
                            r"^(https?://[^/]+)", entity["website"]
                        ).group(1)
                        print(f"Base URL: {base_url}")
                        # 2. find about page link
                        about_page_url = await self.find_about_page_with_llm(
                            str(soup), base_url
                        )
                        self.llm_rate_limiter["calls"] += 1
                        # 2. save about page in entities "about_page" column
                        if not about_page_url:
                            print(
                                f"No about page found for entity id: {entity['id']} - {entity['name']}"
                            )
                            continue
                        await self.database_repository.update_entity_by_id(
                            entity["id"], {"about_page": about_page_url}
                        )
                        print("Successfully scraped about page")
                        print(
                            f"About page URL: {about_page_url} for entity id: {entity['id']} - {entity['name']}"
                        )
                        # 3. call llm to generate summary based on about page
                        about_page_soup = self.scrape_website(about_page_url)
                        if not about_page_soup:
                            print(
                                f"Failed to scrape about page for entity id: {entity['id']} - {entity['name']}"
                            )
                            continue
                        ai_about_summary = await self.generate_summary_with_llm(
                            str(about_page_soup)
                        )
                        self.llm_rate_limiter["calls"] += 1
                        if not ai_about_summary:
                            print(
                                f"Failed to generate summary for entity id: {entity['id']} - {entity['name']}"
                            )
                            continue
                        # 4. save summary in entities "about" column
                        await self.database_repository.update_entity_by_id(
                            entity["id"], {"about": ai_about_summary}
                        )
                        print(
                            f"Successfully generated summary for entity id: {entity['id']} - {entity['name']} | Summary: {ai_about_summary}"
                        )
                    else:
                        print(
                            f"No website or about page found for entity id: {entity['id']} - {entity['name']}. Skipping."
                        )

            # reset llm rate limiter after processing
            self.llm_rate_limiter["calls"] = 0
            self.llm_rate_limiter["last_call_time"] = 0
        except Exception as e:  # pylint: disable=broad-except:
            print(f"Error generating entity summaries: {e}")
            return None

    async def generate_experts_summary(self):
        """
        generate about summary using llm for all experts in the database based on their bio
        """
        try:
            experts = await self.database_repository.get_experts(
                page_number=1, page_size=-1
            )
            if not experts:
                print(f"Error getting all experts: {experts}")
                return None

            print(f"Total experts to process: {len(experts)}")
            for expert in experts:
                if expert["about"]:
                    print(
                        f"Expert id: {expert['id']} - {expert['first_name']} already has an about summary. Skipping."
                    )
                    continue
                elif expert["faculty_page"]:
                    if (
                        self.llm_rate_limiter["calls"]
                        >= self.llm_rate_limiter["max_calls"]
                    ):
                        print(
                            "LLM rate limit reached. Please wait before making more requests."
                        )
                        sleep(60)
                        self.llm_rate_limiter["calls"] = 0
                        self.llm_rate_limiter["last_call_time"] = 0
                    if not self.llm_rate_limiter["last_call_time"]:
                        self.llm_rate_limiter["last_call_time"] = (
                            datetime.datetime.now().timestamp()
                        )
                    if (
                        datetime.datetime.now().timestamp()
                        - self.llm_rate_limiter["last_call_time"]
                    ) * 1000 > self.llm_rate_limiter["reset_time"]:
                        self.llm_rate_limiter["calls"] = 0
                        self.llm_rate_limiter["last_call_time"] = (
                            datetime.datetime.now().timestamp()
                        )

                    # call llm to generate summary based on bio
                    ai_about_summary = await self.generate_summary_with_llm(
                        expert["faculty_page"]
                    )
                    self.llm_rate_limiter["calls"] += 1
                    if not ai_about_summary:
                        print(
                            f"Failed to generate summary for expert id: {expert['id']}"
                        )
                        continue
                    # save summary in experts "about" column
                    await self.database_repository.update_expert_by_id(
                        expert["id"], {"about": ai_about_summary}
                    )
                    print(
                        f"Successfully generated summary using llm for expert id: {expert['id']} | Summary: {ai_about_summary}"
                    )
                else:
                    print(
                        f"No bio found for expert id: {expert['id']} - {expert['first_name']}. Skipping."
                    )

            # reset llm rate limiter after processing
            self.llm_rate_limiter["calls"] = 0
            self.llm_rate_limiter["last_call_time"] = 0
        except Exception as e:  # pylint: disable=broad-except:
            print(f"Error generating expert summaries: {e}")
            return None

    async def generate_entities_hashtag(self):
        """
        generate hashtags using llm for all entities in the database based on their about summary
        """
        try:
            entities = await self.database_repository.get_entities(
                page_number=1, page_size=-1
            )
            if not entities:
                print(f"Error getting all entities: {entities}")
                return None

            for entity in entities:
                if entity["tags"]:
                    print(
                        f"Entity id: {entity['id']} - {entity['name']} already has hashtags. Skipping."
                    )
                    continue
                elif entity["about"]:
                    if (
                        self.llm_rate_limiter["calls"]
                        >= self.llm_rate_limiter["max_calls"]
                    ):
                        print(
                            "LLM rate limit reached. Please wait before making more requests."
                        )
                        sleep(60)
                        self.llm_rate_limiter["calls"] = 0
                        self.llm_rate_limiter["last_call_time"] = 0
                    if not self.llm_rate_limiter["last_call_time"]:
                        self.llm_rate_limiter["last_call_time"] = (
                            datetime.datetime.now().timestamp()
                        )
                    if (
                        datetime.datetime.now().timestamp()
                        - self.llm_rate_limiter["last_call_time"]
                    ) * 1000 > self.llm_rate_limiter["reset_time"]:
                        self.llm_rate_limiter["calls"] = 0
                        self.llm_rate_limiter["last_call_time"] = (
                            datetime.datetime.now().timestamp()
                        )

                    # call llm to generate hashtags based on about summary
                    ai_hashtags = await self.generate_hashtags_with_llm(entity["about"])
                    self.llm_rate_limiter["calls"] += 1
                    if not ai_hashtags:
                        print(
                            f"Failed to generate hashtags for entity id: {entity['id']}"
                        )
                        continue
                    # convert llm string response to an array of hashtags
                    ai_hashtags = ai_hashtags.split()

                    if not ai_hashtags:
                        print(
                            f"No valid hashtags generated for entity id: {entity['id']}"
                        )
                        continue
                    # save hashtags in entities "hashtags" column
                    await self.database_repository.update_entity_by_id(
                        entity["id"], {"tags": ai_hashtags}
                    )
                    print(
                        f"Successfully generated hashtags using llm for entity id: {entity['id']} | Hashtags: {ai_hashtags} | type: {type(ai_hashtags)}"
                    )
                else:
                    print(
                        f"No about summary found for entity id: {entity['id']} - {entity['name']}. Skipping."
                    )

            # reset llm rate limiter
            self.llm_rate_limiter["calls"] = 0
            self.llm_rate_limiter["last_call_time"] = 0
        except Exception as e:  # pylint: disable=broad-except:
            print(f"Error generating entity hashtags: {e}")
            return None
