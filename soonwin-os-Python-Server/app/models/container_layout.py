"""货柜排布方案数据模型"""
from extensions import db
from datetime import datetime
import json


class ContainerLayout(db.Model):
    """货柜装货 3D 排布方案表

    存储用户从 Container.html 操作界面保存的货柜装货布局数据。
    数据内容与 Container.html 的 exportLayout() 输出格式一致：
    {container, cargos[], allowOverflow, interactionMode, colorIndex}
    """
    __tablename__ = 'container_layout'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # 方案名（同一作者下唯一）
    name = db.Column(db.String(100), nullable=False)
    # 完整布局 JSON 字符串（exportLayout() 的输出）
    container_json = db.Column(db.Text, nullable=False)
    # 创建人
    author_id = db.Column(db.String(32), nullable=False, index=True)
    author_name = db.Column(db.String(64), nullable=False)
    # 软删除标志
    is_deleted = db.Column(db.Integer, nullable=False, default=0, index=True)
    # 时间戳
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    def to_dict(self, include_data=False, current_user_id=None):
        """序列化为字典

        Args:
            include_data: 是否包含完整 layout 数据（列表接口不返回，详情接口返回）
            current_user_id: 当前用户 ID，用于生成 is_owner 标记
        """
        data = {
            'id': self.id,
            'name': self.name,
            'author_id': self.author_id,
            'author_name': self.author_name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }

        if include_data:
            parsed = json.loads(self.container_json) if self.container_json else {}
            data['data'] = parsed
            # 提取货柜尺寸用于列表预览（提前在详情中算好，前端列表展示时无需解析 data）
            container = parsed.get('container', {}) or {}
            data['container_name'] = container.get('name', '')
            l, w, h = container.get('l', 0), container.get('w', 0), container.get('h', 0)
            data['container_size'] = f"{l} × {w} × {h} mm"
            data['cargo_count'] = len(parsed.get('cargos', []) or [])

        if current_user_id is not None:
            data['is_owner'] = (self.author_id == current_user_id)

        return data

    def __repr__(self):
        return f'<ContainerLayout id={self.id} name={self.name!r} author={self.author_name!r}>'