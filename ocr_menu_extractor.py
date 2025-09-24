import os
import requests
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_community.document_loaders import AzureAIDocumentIntelligenceLoader
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser


class MenuExtraction(BaseModel):
    """점심 메뉴 정보 추출 모델"""
    is_lunch_menu: bool = Field(description="이미지가 점심 메뉴판인지 여부")
    menu_items: List[str] = Field(default=[], description="메뉴 항목 리스트 (메뉴가 없으면 빈 리스트)")


class OCRMenuExtractor:
    def __init__(self):
        self.endpoint = os.environ.get('AZURE_COGNITIVE_API_ENDPOINT')
        self.key = os.environ.get('AZURE_COGNITIVE_API_KEY')
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        
        if not self.endpoint or not self.key:
            raise ValueError("Azure Document Intelligence API 자격 증명이 설정되지 않았습니다.")
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
            
        self.llm = ChatOpenAI(
            temperature=1,
            model_name="gpt-4o",
            openai_api_key=self.openai_api_key
        )
    
    def download_image(self, image_url: str) -> str:
        """이미지 URL을 다운로드하여 임시 파일로 저장"""
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            
            # 임시 파일명 생성
            temp_filename = f"/tmp/temp_image_{hash(image_url)}.jpg"
            
            with open(temp_filename, 'wb') as f:
                f.write(response.content)
            
            return temp_filename
        except Exception as e:
            print(f"이미지 다운로드 실패 {image_url}: {e}")
            return None
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Azure Document Intelligence를 사용하여 이미지에서 텍스트 추출"""
        try:
            # Azure Document Intelligence 로더 생성
            loader = AzureAIDocumentIntelligenceLoader(
                api_endpoint=self.endpoint,
                api_key=self.key,
                file_path=image_path,
                api_model="prebuilt-read"
            )
            
            # 문서 로드 및 텍스트 추출
            documents = loader.load()
            
            if documents:
                return documents[0].page_content
            return ""
            
        except Exception as e:
            print(f"OCR 처리 실패: {e}")
            return ""
    
    def extract_menu_info(self, text: str) -> MenuExtraction:
        """추출된 텍스트에서 메뉴 정보 추출"""
        if not text:
            return MenuExtraction(is_lunch_menu=False, menu_items=[])
        
        # Pydantic 출력 파서 생성
        parser = PydanticOutputParser(pydantic_object=MenuExtraction)
        
        # 프롬프트 템플릿 생성
        prompt = PromptTemplate(
            template="""다음 텍스트를 분석하여 점심 메뉴 정보를 추출하세요.

텍스트:
{text}

점심 메뉴판인지 판단하고, 메뉴 항목들을 추출하세요.
메뉴판이 아니거나 메뉴가 없으면 빈 리스트를 반환하세요.

{format_instructions}""",
            input_variables=["text"],
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        
        # LLM 체인 실행
        try:
            chain = prompt | self.llm | parser
            response = chain.invoke({"text" : text})
            
            # 응답 파싱
            return response
            
        except Exception as e:
            print(f"메뉴 추출 실패: {e}")
            return MenuExtraction(is_lunch_menu=False, menu_items=[])
    
    def process_image_url(self, image_url: str) -> MenuExtraction:
        """이미지 URL을 처리하여 메뉴 정보 추출"""
        # 이미지 다운로드
        temp_image_path = self.download_image(image_url)
        if not temp_image_path:
            return MenuExtraction(is_lunch_menu=False, menu_items=[])
        
        try:
            # OCR 수행
            extracted_text = self.extract_text_from_image(temp_image_path)
            
            # 메뉴 정보 추출
            menu_info = self.extract_menu_info(extracted_text)
            
            return menu_info
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
    
    def process_multiple_images(self, image_urls: List[str]) -> Optional[MenuExtraction]:
        """여러 이미지를 처리하여 메뉴 정보 추출 (첫 번째 메뉴판 반환)"""
        for image_url in image_urls:
            print(f"이미지 처리 중: {image_url}")
            menu_info = self.process_image_url(image_url)
            
            if menu_info.is_lunch_menu and menu_info.menu_items:
                print(f"메뉴판 발견! {len(menu_info.menu_items)}개 메뉴 항목")
                return menu_info
        
        return None
    
    def generate_menu_comment(self, menu_items: List[str]) -> str:
        """메뉴에 대한 맛있고 재미있는 코멘트 생성"""
        if not menu_items:
            return ""
        
        menu_text = ", ".join(menu_items)
        
        prompt = PromptTemplate(
            template="""당신은 '맛잘알'이라는 닉네임의 음식 비평가입니다.
오늘의 점심 메뉴를 보고 짧고 위트 있는 코멘트를 작성해주세요. 그리고 오늘은 늦어서 죄송하다고 사과도 해줘.

오늘의 메뉴: {menu_text}

맛잘알의 한줄평:""",
            input_variables=["menu_text"]
        )
        
        chain = prompt | self.llm | StrOutputParser()
        try:
            response = chain.invoke({"menu_text" : menu_text})
            return response
        except Exception as e:
            print(f"코멘트 생성 실패: {e}")
            return "🍴 오늘도 맛있게 드세요!"