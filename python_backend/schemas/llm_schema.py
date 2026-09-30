"""
llm_schema.py
─────────────
AI/LLM統合用の Pydantic モデル定義。

主要なモデル:
  - ChatMessage / ChatRequest : チャットメッセージ
  - ChatResponse / ChatStreamResponse : LLMレスポンス
  - DesignInstruction : デザイン指示の構造化
  - SessionManagement : チャットセッション管理
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, AsyncIterator
from enum import Enum


class MessageRole(str, Enum):
    """チャットメッセージの役割"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """チャットメッセージ"""
    role: MessageRole = Field(..., description="メッセージの役割")
    content: str = Field(..., min_length=1, description="メッセージ内容")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="メタデータ")

    class Config:
        example = {
            "role": "user",
            "content": "Make the font bolder",
        }


class ChatHistoryEntry(BaseModel):
    """チャット履歴エントリ"""
    id: str = Field(..., description="メッセージID")
    session_id: str = Field(..., description="セッションID")
    message: ChatMessage = Field(..., description="メッセージ")
    created_at: str = Field(..., description="作成日時（ISO 8601）")


class ChatRequest(BaseModel):
    """LLM チャットリクエスト（通常）"""
    session_id: str = Field(..., description="セッションID")
    project_id: Optional[str] = Field(default=None, description="プロジェクトID（コンテキスト用）")
    message: str = Field(..., min_length=1, description="ユーザーメッセージ")
    temperature: float = Field(default=0.7, description="温度（0.0-1.0）", ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(default=None, description="最大トークン数", ge=1)

    class Config:
        example = {
            "session_id": "sess-abc123",
            "project_id": "proj-xyz789",
            "message": "Can you make this font more geometric?",
            "temperature": 0.7,
        }


class ChatStreamRequest(BaseModel):
    """LLM チャットリクエスト（ストリーミング）"""
    session_id: str = Field(..., description="セッションID")
    project_id: Optional[str] = Field(default=None, description="プロジェクトID")
    message: str = Field(..., min_length=1, description="ユーザーメッセージ")
    temperature: float = Field(default=0.7, description="温度", ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(default=None, description="最大トークン数")
    stream: bool = Field(default=True, description="ストリーミングするか")


class ChatResponse(BaseModel):
    """LLM チャットレスポンス"""
    message_id: str = Field(..., description="メッセージID")
    session_id: str = Field(..., description="セッションID")
    role: MessageRole = Field(default=MessageRole.ASSISTANT, description="役割")
    content: str = Field(..., description="レスポンス内容")
    tokens_used: Optional[int] = Field(default=None, description="使用トークン数")
    model: str = Field(..., description="使用モデル")
    created_at: str = Field(..., description="作成日時")

    class Config:
        example = {
            "message_id": "msg-def456",
            "session_id": "sess-abc123",
            "role": "assistant",
            "content": "I'll make the font more geometric by increasing the corner angles...",
            "tokens_used": 150,
            "model": "gpt-4o",
            "created_at": "2026-05-14T12:34:56Z",
        }


class ChatStreamResponse(BaseModel):
    """LLM ストリーミングレスポンス（チャンク）"""
    message_id: str = Field(..., description="メッセージID")
    delta: str = Field(..., description="増分テキスト")
    finish_reason: Optional[str] = Field(default=None, description="終了理由（stop | length など）")


class DesignInstruction(BaseModel):
    """デザイン指示（自然言語）"""
    raw_instruction: str = Field(..., description="ユーザーからの自然言語指示")
    target_element: str = Field(..., description="ターゲット（font | glyph | stroke | metrics）")
    action: str = Field(..., description="アクション（make_bolder | make_rounder など）")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="パラメータ")
    confidence: float = Field(default=0.0, description="解析信頼度（0.0-1.0）", ge=0.0, le=1.0)


class DesignInstructionParsedResponse(BaseModel):
    """デザイン指示の解析結果"""
    original_instruction: str = Field(..., description="元の指示")
    parsed_instructions: List[DesignInstruction] = Field(
        ...,
        description="解析されたデザイン指示リスト"
    )
    suggested_actions: List[str] = Field(..., description="提案されるアクション")
    estimated_complexity: str = Field(..., description="推定複雑度（simple | medium | complex）")
    needs_clarification: bool = Field(default=False, description="明確化が必要か")
    clarification_questions: List[str] = Field(
        default_factory=list,
        description="明確化用の質問"
    )


class PromptContext(BaseModel):
    """LLM プロンプト用コンテキスト"""
    project_id: Optional[str] = Field(default=None, description="プロジェクトコンテキスト")
    font_id: Optional[str] = Field(default=None, description="フォントコンテキスト")
    current_metrics: Optional[Dict[str, Any]] = Field(default=None, description="現在のメトリクス")
    design_goals: Optional[str] = Field(default=None, description="デザイン目標")
    user_preferences: Optional[Dict[str, Any]] = Field(default=None, description="ユーザー設定")
    previous_suggestions: List[str] = Field(default_factory=list, description="前回の提案")


class PromptBuilderRequest(BaseModel):
    """動的プロンプト生成リクエスト"""
    template_name: str = Field(..., description="プロンプトテンプレート名")
    context: PromptContext = Field(..., description="コンテキスト情報")
    variables: Dict[str, Any] = Field(default_factory=dict, description="テンプレート変数")


class SessionCreateRequest(BaseModel):
    """チャットセッション作成リクエスト"""
    project_id: str = Field(..., description="プロジェクトID")
    title: Optional[str] = Field(default=None, description="セッションタイトル")
    initial_context: Optional[PromptContext] = Field(default=None, description="初期コンテキスト")


class SessionResponse(BaseModel):
    """チャットセッション情報"""
    id: str = Field(..., description="セッションID")
    project_id: str = Field(..., description="プロジェクトID")
    title: Optional[str] = Field(default=None, description="セッションタイトル")
    message_count: int = Field(default=0, description="メッセージ数", ge=0)
    created_at: str = Field(..., description="作成日時")
    updated_at: str = Field(..., description="更新日時")
    last_activity: str = Field(..., description="最後のアクティビティ")


class LLMProviderConfig(BaseModel):
    """LLMプロバイダー設定"""
    provider_name: str = Field(..., description="プロバイダー名（openai | anthropic）")
    model_name: str = Field(..., description="モデル名")
    api_key: Optional[str] = Field(default=None, description="APIキー（送信時は含まない）")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=2000, ge=1)
    timeout_seconds: int = Field(default=60, ge=1)
    retry_count: int = Field(default=3, ge=0)


class LLMProvidersResponse(BaseModel):
    """利用可能なLLMプロバイダー一覧"""
    providers: List[LLMProviderConfig] = Field(..., description="設定済みプロバイダー")
    active_provider: Optional[str] = Field(default=None, description="現在の有効プロバイダー")
