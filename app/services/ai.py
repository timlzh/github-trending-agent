from openai import AsyncOpenAI

from app.config import settings
from app.models import Developer, Repository


class AISummaryService:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.ai.OPENAI_API_KEY, base_url=settings.ai.OPENAI_API_BASE
        )

    async def generate_summary(
        self, data: Repository | Developer, language: str = "简体中文"
    ) -> str:
        system_prompt = f"""<instruction>
<task_description>
Generate a concise, informative, and RSS-friendly summary for a GitHub trending repository using provided structured data. Focus on clarity, technical relevance, and brevity.
</task_description>

<examples>
<example>
Input:
{{ "username": "openai", "repository_name": "gpt-4", "description": "Next-gen AI model", "language": "Python", "stars_since": 2500 }}

Output:
"🤖 OpenAI's GPT-4 is a next-gen AI model gaining traction, trending with 2.5k new stars recently. Ideal for developers exploring advanced NLP capabilities."
</example>

<example>
Input:
{{ "username": "GoogleCloudPlatform", "repository_name": "kubectl-ai", "description": "AI powered Kubernetes Assistant", "language": "C", "stars_since": 1518 }}

Output (in 简体中文):
"🚀 <strong>kubectl-ai</strong> 是一款 AI 驱动的 Kubernetes 辅助工具，近期新增 1.5k 颗 Star，支持开发运维团队高效管理容器化应用与云原生环境，通过智能命令推荐和集群诊断提升 DevOps 工作流效率。"
</example>
</examples>

<instructions>
1. Generate a summary for a GitHub trending repository.
2. Structure summaries in 1-2 sentences using plain text in {language}.
3. Prioritize technical context: state the project's purpose, stack, and trending drivers.
4. For repositories: Highlight language, star growth (if available), and primary use cases.
5. Avoid markdown/formatting. Use natural language suitable for RSS feeds.
6. Ensure summaries are self-contained and require no external context.
7. You can use some emojis to make it more attractive.
8. You can ONLY use the following html tags:
    - <br/> for line breaks
    - <strong>{{text}}</strong> for bold text
    - <em>{{text}}</em> for italic text
9. DO NOT include any other html tags, markdown, or styling.
</instructions>"""
        prompt = f"""Generate an summary for this GitHub trending entry. Follow these steps:
1. Extract critical fields (e.g., description, language, stars_since).
2. Compress information while retaining technical essence.
3. Output only the final summary text.
4. MAKE SURE TO OUTPUT IN {language}.

Input data:
{data.model_dump_json()}
        """

        response = await self.client.chat.completions.create(
            model=settings.ai.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content
        if content is None:
            return ""

        if content.startswith("<think>"):
            content = content.split("</think>", 1)[-1].strip()
        return content

    async def generate_tags(
        self, data: Repository | Developer, language: str = "简体中文"
    ) -> list[str]:
        system_prompt = """<instruction>
<task_description>
Generate 1-3 concise, descriptive and RSS-friendly tags for a GitHub trending repository using provided structured data. Focus on clarity and technical relevance.
</task_description>

<examples>
<example>
Input:
{{ "username": "openai", "repository_name": "gpt-4", "description": "Next-gen AI model", "language": "Python", "stars_since": 2500 }}

Output:
AI model,Machine Learning,OpenAI
</example>

<example>
Input:
{{ "username": "GoogleCloudPlatform", "repository_name": "kubectl-ai", "description": "AI powered Kubernetes Assistant", "language": "C", "stars_since": 1518 }}

Output (in 简体中文):
Kubernetes,AI 助手,云计算,DevOps
</example>
</examples>

<instructions>
1. Identify key technical elements from name/description
2. Prioritize specific technologies over generic terms
3. Output 1-3 comma-separated values
4. Avoid markdown/styling
5. DO NOT include programming languages like Python, Java, etc. We already have a field for that.
6. Technical terms should be in English (e.g. DevOps, Kubernetes, etc.), while the rest can be in user specified Languag.
</instructions>"""
        prompt = f"""Generate tags for this trending entry:
1. Extract core technologies/domains
2. Format as comma-separated values
3. MAKE SURE TO OUTPUT IN {language}.
4. DO NOT include programming languages like Python, Java, etc. We already have a field for that.

Input data:
{data.model_dump_json()}
        """

        response = await self.client.chat.completions.create(
            model=settings.ai.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content
        if content is None:
            return []
        content = content.split("</think>")[-1].strip()

        # Process the response content to extract tags
        tags = []
        for line in content.split("\n"):
            line = line.strip()
            for tag in line.replace("，", ",").split(","):
                tag = tag.strip()
                if tag:
                    tags.append(tag)
        tags = list(set(tags))  # Remove duplicates
        if len(tags) > 3:
            tags = tags[:3]
        return tags
