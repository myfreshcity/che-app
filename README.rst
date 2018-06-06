virtualenvs 配置：
 virtualenv -p /usr/local/bin/python3 venv

激活 virtualenvs：
 source venv/bin/activate

退出 virtualenvs：
 deactivate


启动程序
 python manage.py runserver -H localhost

初始化/升级数据模型
python manage.py deploy

创建Roles和admin用户，赋于superuser角色
python manage.py initrole


生产环境的启动
 venv/bin/uwsgi --ini uwsgi.ini | tail -f uwsgi.log

 程序终止：
 kill -HUP `cat uwsgi.pid`
 venv/bin/uwsgi --reload uwsgi.pid | tail -f uwsgi.log

 安装依赖
pip install -r requirements.txt


安装
  pip install jupyter
调试工具
   jupyter notebook