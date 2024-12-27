FROM python:3.9

#ARG project_dir=/usr/src/app

#ADD work_board.py $project_dir

# ファイルをローカルからコンテナ内の指定のパスにコピー
COPY . /app

#WORKDIR $project_dir
WORKDIR /app

# コマンド実行
#RUN pip install --proxy="proxy.mei.co.jp:8080" flask flask-restful flask-cors flask_sqlalchemy
#RUN pip install --proxy="proxy.mei.co.jp:8080" pandas workdays
#RUN pip install --proxy="proxy.mei.co.jp:8080" psycopg2-binary
#RUN pip install --proxy="proxy.mei.co.jp:8080" python-dotenv
RUN pip --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org install flask

# コンテナが接続用にリッスンするポートを指定
EXPOSE 5001

CMD ["python", "work_board.py"]