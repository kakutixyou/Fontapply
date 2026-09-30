from typing import List, Dict, Any
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime

class OperationType(str, Enum):
    """操作の種類"""
    INSERT_GLYPH = "insert_glyph"           # グリフ追加
    DELETE_GLYPH = "delete_glyph"           # グリフ削除
    MODIFY_METRICS = "modify_metrics"       # メトリクス変更
    MODIFY_STROKE = "modify_stroke"         # ストロークプロパティ変更
    MOVE_POINT = "move_point"               # グリフポイント移動
    ADD_POINT = "add_point"                 # グリフポイント追加
    DELETE_POINT = "delete_point"           # グリフポイント削除
    MODIFY_COLOR = "modify_color"           # 色変更


@dataclass
class Operation:
    """ユーザーの編集操作"""
    id: str
    type: OperationType
    user_id: str
    session_id: str
    project_id: str
    glyph_id: str
    timestamp: float
    content: Dict[str, Any]           # 操作内容（変更内容）
    client_version: int                # クライアント側の操作番号
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['type'] = self.type.value
        return data


@dataclass
class OperationContext:
    """各クライアントの操作コンテキスト"""
    user_id: str
    session_id: str
    server_version: int = 0            # サーバーが確認した操作数
    client_version: int = 0            # クライアントが実行した操作数
    pending_operations: List[Operation] = None
    
    def __post_init__(self):
        if self.pending_operations is None:
            self.pending_operations = []


class OperationTransformEngine:
    """Operational Transform: 競合操作の自動統合"""
    
    def __init__(self):
        # {project_id: {glyph_id: [operation...]}}
        self.operation_history: Dict[str, Dict[str, List[Operation]]] = {}
        # {project_id: {session_id: OperationContext}}
        self.contexts: Dict[str, Dict[str, OperationContext]] = {}
    
    def apply_operation(self, op: Operation) -> tuple[bool, str]:
        """
        操作をプロジェクトの履歴に追加
        Returns: (success, message)
        """
        project_id = op.project_id
        glyph_id = op.glyph_id
        
        if project_id not in self.operation_history:
            self.operation_history[project_id] = {}
        if glyph_id not in self.operation_history[project_id]:
            self.operation_history[project_id][glyph_id] = []
        
        # 操作を履歴に追加
        self.operation_history[project_id][glyph_id].append(op)
        return True, "Operation applied successfully"
    
    def transform(self, op_a: Operation, op_b: Operation) -> tuple[Operation, Operation]:
        """
        2つの競合操作を変換して統合
        op_a: サーバーで先に確認した操作
        op_b: 後から到着した操作
        
        Returns: (transformed_op_a, transformed_op_b)
        """
        
        # 同じグリフへの操作でなければ競合なし
        if op_a.glyph_id != op_b.glyph_id:
            return op_a, op_b
        
        # Case 1: 両方とも異なる操作タイプ → 順序に影響しない
        if op_a.type != op_b.type:
            return op_a, op_b
        
        # Case 2: 同じメトリクス項目への変更 → 最後の変更を優先
        if op_a.type == OperationType.MODIFY_METRICS:
            return self._transform_metrics_conflict(op_a, op_b)
        
        # Case 3: ポイント移動 → 独立した操作なので競合なし
        if op_a.type == OperationType.MOVE_POINT:
            point_a = op_a.content.get("point_id")
            point_b = op_b.content.get("point_id")
            if point_a != point_b:
                return op_a, op_b
            # 同じポイントへの同時移動 → 最後の移動を優先
            return op_a, op_b  # op_b は無視
        
        return op_a, op_b
    
    def _transform_metrics_conflict(self, op_a: Operation, op_b: Operation) -> tuple[Operation, Operation]:
        """メトリクス競合を解決"""
        # 同じフィールドへの変更？
        field_a = op_a.content.get("field")
        field_b = op_b.content.get("field")
        
        if field_a != field_b:
            # 異なるフィールド → 衝突なし
            return op_a, op_b
        
        # 同じフィールド → 最後の変更（タイムスタンプが新しい方）を採用
        if op_b.timestamp > op_a.timestamp:
            # op_a を op_b のために空操作に変更
            op_a.content["skipped"] = True
            return op_a, op_b
        else:
            op_b.content["skipped"] = True
            return op_a, op_b
    
    def get_history(self, project_id: str, glyph_id: str) -> List[Operation]:
        """グリフの操作履歴を取得"""
        return self.operation_history.get(project_id, {}).get(glyph_id, [])
    
    def get_all_operations(self, project_id: str, since_version: int = 0) -> List[Operation]:
        """プロジェクト全体の操作を取得（バージョン以降）"""
        all_ops = []
        for glyph_ops in self.operation_history.get(project_id, {}).values():
            all_ops.extend(glyph_ops)
        
        # タイムスタンプでソート
        all_ops.sort(key=lambda op: op.timestamp)
        return all_ops[since_version:]


# グローバルインスタンス
transform_engine = OperationTransformEngine()
