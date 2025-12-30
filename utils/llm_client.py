"""
OpenAI ChatGPT API 클라이언트
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """ChatGPT API 클라이언트 싱글톤"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.temperature = float(os.getenv('LLM_TEMPERATURE', '0.3'))  # 더 일관된 응답
        self.max_tokens = int(os.getenv('LLM_MAX_TOKENS', '2000'))  # 더 긴 응답 허용

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. "
                "Please create .env file with your API key. "
                "See .env.example for reference."
            )

        self.client = OpenAI(api_key=self.api_key)
        self._initialized = True

    def generate_response(self, system_prompt, user_message, temperature=None):
        """
        ChatGPT로 응답 생성

        Args:
            system_prompt: 시스템 프롬프트 (역할 정의)
            user_message: 사용자 메시지 (상황 설명)
            temperature: 창의성 수준 (0.0~2.0, 기본값은 설정값 사용)

        Returns:
            생성된 응답 문자열
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=self.max_tokens
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"[LLM Error] {str(e)}")
            return f"[LLM 응답 생성 실패: {str(e)}]"

    def generate_with_context(self, system_prompt, messages, temperature=None):
        """
        대화 컨텍스트를 포함하여 응답 생성

        Args:
            system_prompt: 시스템 프롬프트
            messages: 대화 이력 리스트 [{"role": "user/assistant", "content": "..."}]
            temperature: 창의성 수준

        Returns:
            생성된 응답 문자열
        """
        try:
            full_messages = [{"role": "system", "content": system_prompt}] + messages

            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=temperature if temperature is not None else self.temperature,
                max_tokens=self.max_tokens
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"[LLM Error] {str(e)}")
            return f"[LLM 응답 생성 실패: {str(e)}]"
