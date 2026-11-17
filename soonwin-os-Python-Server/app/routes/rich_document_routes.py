import json
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
import bleach
from bleach.css_sanitizer import CSSSanitizer
from bs4 import BeautifulSoup
from flask import Blueprint, abort, jsonify, request, send_file
from sqlalchemy import update
from extensions import db
from app.models.rich_document import RichDocument, RichMedia
from app.utils.auth_utils import require_auth, get_user_id_from_token, is_admin_user

rich_document_bp = Blueprint('rich_document', __name__)
TAGS = ['p','div','span','br','h1','h2','h3','h4','b','strong','i','em','u','s','strike','ul','ol','li','blockquote','table','tbody','thead','tr','th','td','a','img','video','hr','font','sup','sub']
CSS = CSSSanitizer(allowed_css_properties=['color','background-color','font-size','font-family','font-weight','font-style','text-decoration','text-align','line-height','width','height','max-width','max-height','margin','margin-left','margin-right','margin-top','margin-bottom','display','border','border-color','border-width','border-style','padding','vertical-align'])
ATTR = {'*':['style','class'], 'a':['href','title','target','rel'], 'img':['data-media-id','alt','width','height'], 'video':['data-media-id','controls','preload','width','height'], 'td':['colspan','rowspan'], 'th':['colspan','rowspan'], 'font':['size','color','face']}

def root():
    path = os.environ.get('OA_RICH_MEDIA_DIR')
    if not path: abort(503, description='文档媒体目录未配置')
    p = Path(path).resolve(); p.mkdir(parents=True, exist_ok=True); return p

def doc_or_404(doc_id, deleted=False):
    d = db.session.get(RichDocument, doc_id)
    if not d or bool(d.deleted_at) != deleted or (not is_admin_user() and d.owner != get_user_id_from_token()): abort(404)
    return d

def data(d, content=False):
    result = dict(id=d.id, owner=d.owner, title=d.title, version=d.version, created_at=d.created_at.isoformat(), updated_at=d.updated_at.isoformat(), deleted_at=d.deleted_at.isoformat() if d.deleted_at else None)
    if content: result.update(html=d.html, watermark=json.loads(d.watermark))
    return result

def clean_html(value, doc_id):
    if not isinstance(value,str) or len(value)>5_000_000: abort(400, description='文档内容无效或过大')
    cleaned=bleach.clean(value, tags=TAGS, attributes=ATTR, protocols=['http','https','mailto'], css_sanitizer=CSS, strip=True)
    soup=BeautifulSoup(cleaned,'html.parser')
    for node in soup.find_all(['img','video']):
        mid=node.get('data-media-id','')
        media=db.session.get(RichMedia,mid)
        if not media or media.document_id != doc_id: abort(400, description='无效媒体引用')
    return str(soup)

@rich_document_bp.route('/rich-documents', methods=['GET','POST'])
@require_auth
def documents():
    if request.method == 'POST':
        if request.mimetype != 'multipart/form-data':
            abort(400, description='请提交文档内容')
        try:
            payload = json.loads(request.form.get('document', ''))
        except (ValueError, TypeError):
            abort(400, description='文档数据无效')
        if not isinstance(payload, dict):
            abort(400, description='文档数据无效')
        title = payload.get('title')
        html = payload.get('html')
        watermark = payload.get('watermark')
        if not isinstance(title, str) or not title.strip() or len(title.strip()) > 200:
            abort(400, description='文档名称无效')
        if not isinstance(html, str) or len(html) > 5_000_000:
            abort(400, description='文档内容无效或过大')
        if not isinstance(watermark, dict) or len(json.dumps(watermark, ensure_ascii=False)) > 10000:
            abort(400, description='水印设置无效')
        soup = BeautifulSoup(html, 'html.parser')
        mapping = {}
        created_paths = []
        now = datetime.utcnow()
        d = RichDocument(owner=get_user_id_from_token(), title=title.strip(), html='',
                         watermark=json.dumps(watermark, ensure_ascii=False), version=1,
                         created_at=now, updated_at=now)
        try:
            db.session.add(d)
            db.session.flush()
            for node in soup.find_all(['img', 'video']):
                pending_id = node.get('data-media-id', '')
                if not isinstance(pending_id, str) or not pending_id.startswith('pending-') or len(pending_id) != 40:
                    abort(400, description='新文档媒体引用无效')
                try:
                    uuid.UUID(hex=pending_id[8:])
                except ValueError:
                    abort(400, description='新文档媒体引用无效')
                if pending_id not in mapping:
                    file = request.files.get(pending_id)
                    if not file or not (file.mimetype.startswith('image/') or file.mimetype.startswith('video/')) or file.mimetype == 'image/svg+xml':
                        abort(400, description='媒体文件无效')
                    mid = uuid.uuid4().hex
                    path = root() / mid
                    with path.open('xb') as output:
                        created_paths.append(path)
                        shutil.copyfileobj(file.stream, output)
                    db.session.add(RichMedia(id=mid, document_id=d.id,
                        filename=os.path.basename(file.filename or '')[:255], mime=file.mimetype,
                        size=path.stat().st_size))
                    mapping[pending_id] = mid
                node['data-media-id'] = mapping[pending_id]
            db.session.flush()
            d.html = clean_html(str(soup), d.id)
            db.session.commit()
        except Exception:
            db.session.rollback()
            for path in created_paths:
                path.unlink(missing_ok=True)
            raise
        return jsonify(**data(d, True), media_map=mapping), 201
    trash=request.args.get('trash') == '1'
    if trash and not is_admin_user(): abort(403)
    q=RichDocument.query.filter(RichDocument.deleted_at.isnot(None) if trash else RichDocument.deleted_at.is_(None))
    if not is_admin_user(): q=q.filter_by(owner=get_user_id_from_token())
    term=request.args.get('q','').strip()[:200]
    if term: q=q.filter(RichDocument.title.contains(term,autoescape=True))
    return jsonify([data(d) for d in q.order_by(RichDocument.updated_at.desc()).limit(500)])

@rich_document_bp.route('/rich-documents/<int:doc_id>', methods=['GET','PUT','DELETE'])
@require_auth
def document(doc_id):
    d=doc_or_404(doc_id)
    if request.method == 'GET': return jsonify(data(d,True))
    if request.method == 'DELETE':
        d.deleted_at=datetime.utcnow(); d.version+=1; db.session.commit(); return jsonify(ok=True)
    payload=request.get_json(silent=True) or {}; version=payload.get('version')
    if type(version) is not int: abort(400)
    title=str(payload.get('title','')).strip()[:200]
    if not title: abort(400,description='标题不能为空')
    html=clean_html(payload.get('html',''), doc_id)
    wm=payload.get('watermark',{})
    if not isinstance(wm,dict) or len(json.dumps(wm,ensure_ascii=False))>10000: abort(400)
    result=db.session.execute(update(RichDocument).where(RichDocument.id==doc_id, RichDocument.version==version, RichDocument.deleted_at.is_(None)).values(title=title,html=html,watermark=json.dumps(wm,ensure_ascii=False),version=version+1,updated_at=datetime.utcnow()))
    if not result.rowcount: db.session.rollback(); return jsonify(error='文档已被修改，请重新打开后处理'),409
    db.session.commit(); db.session.expire_all(); return jsonify(data(db.session.get(RichDocument,doc_id),True))

@rich_document_bp.route('/rich-documents/<int:doc_id>/copy', methods=['POST'])
@require_auth
def copy_document(doc_id):
    source = doc_or_404(doc_id)
    payload = request.get_json(silent=True) or {}
    title = payload.get('title', '')
    if not isinstance(title, str) or not title.strip() or len(title.strip()) > 200:
        abort(400, description='标题不能为空或过长')
    # The editor may supply its current unsaved content. It must still be
    # based on the latest saved version, and its media must belong to source.
    source_html = source.html
    source_watermark = source.watermark
    if 'html' in payload or 'watermark' in payload or 'version' in payload:
        version = payload.get('version')
        if type(version) is not int or version != source.version:
            return jsonify(error='原文档已被修改，请重新打开后处理'), 409
        source_html = clean_html(payload.get('html'), source.id)
        watermark = payload.get('watermark')
        if not isinstance(watermark, dict) or len(json.dumps(watermark, ensure_ascii=False)) > 10000:
            abort(400, description='水印设置无效')
        source_watermark = json.dumps(watermark, ensure_ascii=False)
    now = datetime.utcnow()
    copied = RichDocument(owner=get_user_id_from_token(), title=title.strip(), html='',
                          watermark=source_watermark, version=1, created_at=now, updated_at=now)
    created_paths = []
    try:
        db.session.add(copied)
        db.session.flush()
        soup = BeautifulSoup(source_html, 'html.parser')
        mapping = {}
        for node in soup.find_all(['img', 'video']):
            old_id = node.get('data-media-id', '')
            if old_id not in mapping:
                original = db.session.get(RichMedia, old_id)
                if not original or original.document_id != source.id:
                    abort(400, description='原文档包含无效媒体')
                new_id = uuid.uuid4().hex
                destination = root() / new_id
                # Exclusive creation prevents overwriting any existing media.
                with (root() / original.id).open('rb') as reader, destination.open('xb') as writer:
                    created_paths.append(destination)
                    shutil.copyfileobj(reader, writer)
                db.session.add(RichMedia(id=new_id, document_id=copied.id, filename=original.filename,
                                         mime=original.mime, size=original.size))
                mapping[old_id] = new_id
            node['data-media-id'] = mapping[old_id]
        copied.html = str(soup)
        db.session.commit()
    except Exception:
        db.session.rollback()
        for path in created_paths:
            path.unlink(missing_ok=True)
        raise
    return jsonify(data(copied, True)), 201

@rich_document_bp.route('/rich-documents/<int:doc_id>/restore', methods=['POST'])
@require_auth
def restore(doc_id):
    if not is_admin_user(): abort(403)
    d=doc_or_404(doc_id,True); d.deleted_at=None; d.version+=1; db.session.commit(); return jsonify(ok=True)

@rich_document_bp.route('/rich-documents/<int:doc_id>/permanent', methods=['DELETE'])
@require_auth
def permanent(doc_id):
    if not is_admin_user(): abort(403)
    d=doc_or_404(doc_id,True); items=RichMedia.query.filter_by(document_id=doc_id).all(); paths=[root()/m.id for m in items]
    for m in items: db.session.delete(m)
    db.session.delete(d); db.session.commit()
    for p in paths:
        try: p.unlink(missing_ok=True)
        except OSError: pass
    return jsonify(ok=True)

@rich_document_bp.route('/rich-documents/<int:doc_id>/media', methods=['POST'])
@require_auth
def upload(doc_id):
    doc_or_404(doc_id); f=request.files.get('file')
    if not f or not (f.mimetype.startswith('image/') or f.mimetype.startswith('video/')) or f.mimetype in ('image/svg+xml','text/html'): abort(400)
    mid=uuid.uuid4().hex; path=root()/mid; f.save(path); size=path.stat().st_size
    try:
        db.session.add(RichMedia(id=mid,document_id=doc_id,filename=os.path.basename(f.filename or '')[:255],mime=f.mimetype,size=size)); db.session.commit()
    except Exception:
        path.unlink(missing_ok=True); raise
    return jsonify(id=mid),201

@rich_document_bp.route('/rich-documents/<int:doc_id>/media/<mid>', methods=['GET'])
@require_auth
def media(doc_id,mid):
    doc_or_404(doc_id); m=db.session.get(RichMedia,mid)
    if not m or m.document_id != doc_id: abort(404)
    path=root()/m.id
    if not path.is_file(): abort(404)
    response=send_file(path,mimetype=m.mime,conditional=True,download_name=m.filename)
    response.headers['Cache-Control']='private, no-store'; response.headers['X-Content-Type-Options']='nosniff'; return response

@rich_document_bp.route('/rich-documents/me', methods=['GET'])
@require_auth
def current_user():
    return jsonify(admin=is_admin_user(), owner=get_user_id_from_token())
