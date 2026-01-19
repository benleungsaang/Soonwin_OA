import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app import create_app
from extensions import db
from app.models.totp_user import TotpUser

app = create_app()
with app.app_context():
    user = TotpUser.query.filter_by(emp_id='admin').first()
    if user:
        print(f'TOTP密钥: {user.totp_secret}')
    else:
        print('未找到管理员用户')