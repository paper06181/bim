"""
LLM 클라이언트 (OpenAI GPT API 사용)
"""

import openai
import os
import json
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()


class LLMClient:
    """LLM 클라이언트"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "500"))

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")

        openai.api_key = self.api_key

    def call(
        self,
        system_prompt: str,
        user_message: str,
        response_format: str = "json"
    ) -> dict:
        """
        LLM API 호출

        Args:
            system_prompt: 시스템 프롬프트
            user_message: 사용자 메시지
            response_format: 응답 형식 ("json" 또는 "text")

        Returns:
            LLM 응답 (dict 또는 str)
        """
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"} if response_format == "json" else None
            )

            content = response.choices[0].message.content

            if response_format == "json":
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # JSON 파싱 실패 시 간단한 구조 반환
                    return {
                        "error": "JSON 파싱 실패",
                        "raw_content": content
                    }
            else:
                return {"content": content}

        except Exception as e:
            print(f"LLM API 호출 오류: {e}")
            # 오류 시 기본값 반환
            return {
                "error": str(e),
                "fallback": True
            }

    def call_with_retry(
        self,
        system_prompt: str,
        user_message: str,
        retries: int = 2
    ) -> dict:
        """재시도 로직 포함 호출"""
        for attempt in range(retries + 1):
            result = self.call(system_prompt, user_message)
            if "error" not in result:
                return result
            if attempt < retries:
                print(f"재시도 {attempt + 1}/{retries}...")
        return result
