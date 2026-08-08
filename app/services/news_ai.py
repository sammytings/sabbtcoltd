import requests
from django.conf import settings


class NewsAIService:
    """
    Groq AI service for SABBTCo Logistics news generation.

    Groq returns normal text, NOT JSON.
    """

    DEFAULT_MODEL = "llama-3.3-70b-versatile"

    @classmethod
    def get_api_key(cls):
        return getattr(settings, "GROQ_API_KEY", None)

    @classmethod
    def get_api_url(cls):
        return getattr(
            settings,
            "GROQ_API_URL",
            "https://api.groq.com/openai/v1/chat/completions",
        )

    @classmethod
    def get_model(cls):
        return getattr(
            settings,
            "GROQ_MODEL",
            cls.DEFAULT_MODEL,
        )

    @classmethod
    def call_groq(cls, prompt):
        """
        Send a normal text request to Groq.
        No JSON response mode is used.
        """

        api_key = cls.get_api_key()

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is missing from Django settings."
            )

        url = cls.get_api_url()

        system_prompt = """
You are the professional news writer for SABBTCo Logistics.

Write professional, factual and SEO-friendly news content.

IMPORTANT:

Return normal readable text.

DO NOT return JSON.

DO NOT use markdown code blocks.

DO NOT use Python dictionaries.

DO NOT explain your reasoning.

DO NOT mention that you are an AI.

Do not invent statistics, prices, dates, customer numbers,
government decisions, awards, partnerships or achievements
that were not provided.

Write naturally as a professional logistics news article.

The article should contain:

TITLE:
A professional news headline.

DESCRIPTION:
A professional news article of approximately 100-180 words.

IMAGE ALT:
A short descriptive sentence suitable for an image alt attribute.

FOCUS KEYWORD:
One primary SEO keyword or phrase.

SEO KEYWORDS:
Five to ten related keywords separated by commas.

META TITLE:
An SEO title of 60 characters or fewer.

META DESCRIPTION:
An SEO description of 155 characters or fewer.

Present the result exactly in this readable format:

TITLE:
[headline]

DESCRIPTION:
[article]

IMAGE ALT:
[image description]

FOCUS KEYWORD:
[primary keyword]

SEO KEYWORDS:
[keyword one, keyword two, keyword three]

META TITLE:
[meta title]

META DESCRIPTION:
[meta description]

Do not return anything else.
"""

        payload = {
            "model": cls.get_model(),
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.3,
            "max_tokens": 1800,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=90,
            )

        except requests.RequestException as exc:
            raise ValueError(
                f"Could not connect to Groq API: {exc}"
            ) from exc

        if response.status_code != 200:
            try:
                error_data = response.json()
            except Exception:
                error_data = response.text

            raise ValueError(
                f"Groq API returned HTTP "
                f"{response.status_code}: {error_data}"
            )

        try:
            data = response.json()
        except Exception as exc:
            raise ValueError(
                "Groq returned an invalid API response."
            ) from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(
                f"Groq response did not contain message content: {data}"
            ) from exc

        if not content:
            raise ValueError(
                "Groq returned an empty response."
            )

        return str(content).strip()

    @classmethod
    def parse_response(cls, text):
        """
        Convert Groq's normal text response into a Python dictionary.

        Groq itself never has to generate JSON.
        """

        if not text:
            return {
                "title": "",
                "description": "",
                "image_alt": "",
                "focus_keyword": "",
                "seo_keywords": "",
                "meta_title": "",
                "meta_description": "",
                "seo_score": 0,
            }

        result = {
            "title": "",
            "description": "",
            "image_alt": "",
            "focus_keyword": "",
            "seo_keywords": "",
            "meta_title": "",
            "meta_description": "",
        }

        sections = {
            "TITLE:": "title",
            "DESCRIPTION:": "description",
            "IMAGE ALT:": "image_alt",
            "FOCUS KEYWORD:": "focus_keyword",
            "SEO KEYWORDS:": "seo_keywords",
            "META TITLE:": "meta_title",
            "META DESCRIPTION:": "meta_description",
        }

        current_field = None
        collected = []

        lines = text.splitlines()

        for line in lines:
            stripped = line.strip()

            upper = stripped.upper()

            matched = False

            for marker, field in sections.items():
                if upper == marker or upper.startswith(marker):
                    if current_field is not None:
                        value = "\n".join(
                            collected
                        ).strip()

                        result[current_field] = value

                    current_field = field

                    remainder = stripped[len(marker):].strip()

                    collected = []

                    if remainder:
                        collected.append(remainder)

                    matched = True
                    break

            if not matched and current_field is not None:
                collected.append(stripped)

        if current_field is not None:
            result[current_field] = "\n".join(
                collected
            ).strip()

        result["seo_score"] = cls.calculate_seo_score(result)

        return result

    @classmethod
    def calculate_seo_score(cls, result):
        """
        Calculate SEO score locally.
        """

        score = 100

        if not result.get("title"):
            score -= 15

        if not result.get("description"):
            score -= 20

        if not result.get("image_alt"):
            score -= 10

        if not result.get("focus_keyword"):
            score -= 15

        if not result.get("seo_keywords"):
            score -= 10

        if not result.get("meta_title"):
            score -= 10

        if not result.get("meta_description"):
            score -= 10

        meta_title = result.get("meta_title", "")

        meta_description = result.get(
            "meta_description",
            "",
        )

        if len(meta_title) > 60:
            score -= 5

        if len(meta_description) > 155:
            score -= 5

        keyword = result.get(
            "focus_keyword",
            "",
        ).strip().lower()

        title = result.get(
            "title",
            "",
        ).lower()

        description = result.get(
            "description",
            "",
        ).lower()

        if keyword:
            if keyword not in title:
                score -= 5

            if keyword not in description:
                score -= 5

        description_words = len(
            description.split()
        )

        if description_words < 50:
            score -= 5

        if description_words > 250:
            score -= 5

        return max(
            0,
            min(100, score),
        )

    @classmethod
    def generate(
        cls,
        prompt,
        focus_keyword="",
        seo_keywords="",
        image_description="",
    ):
        """
        Generate news content.
        """

        if not prompt:
            raise ValueError(
                "Please provide an AI prompt."
            )

        prompt = str(prompt).strip()

        extra_information = []

        if focus_keyword:
            extra_information.append(
                f"Focus keyword: {focus_keyword}"
            )

        if seo_keywords:
            extra_information.append(
                f"SEO keywords: {seo_keywords}"
            )

        if image_description:
            extra_information.append(
                f"Image description: {image_description}"
            )

        additional_context = "\n".join(
            extra_information
        )

        final_prompt = f"""
Create a professional news article for SABBTCo Logistics.

USER REQUEST:
{prompt}

ADDITIONAL INFORMATION:
{additional_context}

Write the article using only the information provided.

The response must be normal readable text using these headings:

TITLE:
DESCRIPTION:
IMAGE ALT:
FOCUS KEYWORD:
SEO KEYWORDS:
META TITLE:
META DESCRIPTION:

Do not return JSON.
Do not return a Python dictionary.
Do not use markdown code blocks.
"""

        raw_response = cls.call_groq(
            final_prompt
        )

        return cls.parse_response(
            raw_response
        )

    @classmethod
    def generate_from_prompt(
        cls,
        prompt,
        focus_keyword="",
        seo_keywords="",
    ):
        """
        Generate news content directly from an admin prompt.
        """

        if prompt is None:
            raise ValueError(
                "Prompt cannot be None."
            )

        return cls.generate(
            prompt=str(prompt).strip(),
            focus_keyword=focus_keyword,
            seo_keywords=seo_keywords,
        )

    @classmethod
    def generate_from_image(
        cls,
        image_description,
        prompt="",
        focus_keyword="",
        seo_keywords="",
    ):
        """
        Generate news content from an image description.
        """

        if not image_description:
            raise ValueError(
                "Image description is required."
            )

        image_description = str(
            image_description
        ).strip()

        if not prompt:
            prompt = (
                "Create a professional news article "
                "based on the uploaded image."
            )

        combined_prompt = f"""
{prompt}

IMAGE INFORMATION:
{image_description}

Use the image information to help create the article.

Do not invent facts that are not supported by
the supplied information.
"""

        return cls.generate(
            prompt=combined_prompt,
            focus_keyword=focus_keyword,
            seo_keywords=seo_keywords,
            image_description=image_description,
        )