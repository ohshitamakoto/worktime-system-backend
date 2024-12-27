from flask import Flask, render_template, request,make_response
from flask import request, make_response, jsonify
import json
import datetime
import os

app = Flask(__name__)

def lookahead(iterable):
    it = iter(iterable)
    # ループを一個進めておいて、lastに最初の値を代入
    last = next(it)
    # secondとthirdを取り出す
    for val in it:
        yield last, True
        # lastに代入
        last = val
    # 最後にyield
    yield last, False

def makeDisplayJson(j_str):

        #print(s_str,e_str,name)

    #勤務状態を編集　出社/在宅/出社&在宅/年休　＋　（フレックス）
    state = j_str["state"]["Value"]
    state_org = j_str["state"]["Value"]
    ##部分在宅を"出社/部分在宅"に変更
    #if "部分" in state:
    #    state = "出社/部分在宅"
    if "部分在宅申請" == state:
        #state = "出社/部分在宅有"
        state = "出社/在宅申請"
    if "部分在宅勤務中" == state:
        #state = "在宅勤務中/出社有"
        state = "部分在宅勤務中"
    if "部分在宅終了" == state:
        state = "部分在宅終了"
    if "部分出社" == state:
        #state = "出社/部分在宅有"
        state = "出社(在宅有)"
    ##フレックス有の場合"フレックス"追加
    flex = j_str["flex"]["Value"]
    if flex == "有":
        state = state + "(フレックス)"
    j_str["state"]["Value"] = state


    #時間休の場合、時間を追加
    time_off = j_str["time_off"]["Value"]
    if time_off == "無":
        j_str["time_off"]["Value"] = "-"
    if "時間休" in time_off:
        time = "（" + j_str["time_off_s_time"] + "～" + j_str["time_off_e_time"] + "）"
        s_str = time_off.find("時間休") + 3
        time_str = time_off[:s_str] + time + time_off[s_str:]
        j_str["time_off"]["Value"] = time_str


    #### 勤務時間を編集　フレックス時間を反映（予定は含まない）###
    start_time = "9:00"
    end_time = ""

    ##年休の場合時間は空白
    if state == "年休":
        start_time = ""
        end_time = ""
    ##午前休の場合 開始は13:15に設定
    time_str = j_str["time_off"]["Value"]
    if time_str in "午前休":
        start_time = "13:15"
    ##午後休の場合 終了は12:30に設定
    if time_str in "午後休":
        end_time = "12:30"
    j_str["work_s_time"] = start_time
    j_str["work_e_time"]  = end_time

    #### 勤務時間の設定 ####
    ##フレックス時間があれば、フレックス申請時間に入れ替え
    time_flex_s = j_str["flex_s_time"]
    time_flex_e = j_str["flex_e_time"]

    if time_flex_s != None and ":" in time_flex_s:
        ##不要文字削除
        s_str = time_flex_s.find("：") + 1
        time_flex_s = time_flex_s[s_str:]

        j_str["work_s_time"] = time_flex_s
    if time_flex_e != None and ":" in time_flex_e:
        ##不要文字削除
        s_str = time_flex_e.find("：") + 1
        time_flex_e = time_flex_e[s_str:]

        j_str["work_e_time"]  = time_flex_e
    
    ##部分在宅でなく、時間に"予定"文字が無ければ、在宅勤務時間反映
    state = j_str["state"]["Value"]
    home_s_time = j_str["home_s_time"]
    home_e_time = j_str["home_e_time"]
    if "部分" not in state:
        if home_s_time != None and "予定" not in home_s_time:
            j_str["work_s_time"] = home_s_time
        if home_e_time != None and "予定" not in home_e_time:
            j_str["work_e_time"] = home_e_time
    if home_e_time != None and "部分出社" in state_org:
        j_str["work_e_time"] = home_e_time + "(在宅終了)～"

    #氏名を漢字だけに編集
    name = j_str["name"]["DisplayName"]
    s_str = name.find("(") + 1
    e_str = name.find(")")
    if s_str > 0 and e_str > 0:
        j_str["name"]["DisplayName"] = name[s_str:e_str]
        sp_name = j_str["name"]["DisplayName"]
        if "平野" in sp_name:
            sp_name = sp_name + "  *12課"
            j_str["name"]["DisplayName"] = sp_name
        if "松本 悠佑" in sp_name:
            sp_name = sp_name + "  *ITS"
            j_str["name"]["DisplayName"] = sp_name
        if "鈴木 秀太" in sp_name:
            j_str["state"]["Value"] = "（駐在中）"
            j_str["work_s_time"] = ""
        if "菊地 慧" in sp_name:
            j_str["state"]["Value"] = "（出向中）"
            j_str["work_s_time"] = ""
        if "菊地 和彦" in sp_name:
            j_str["state"]["Value"] = "退勤"
            j_str["work_s_time"] = ""
        if "高橋 寛" in sp_name:
            j_str["state"]["Value"] = "退勤"
            j_str["work_s_time"] = ""
            
    return j_str

@app.route("/39", methods=['GET', "POST"])
def get_work_39():
    if request.method == "GET":
        file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_39.json"
        return get_work(file_json,"39")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        ret = post_kintai_state("39",switch["num"])
        return ret
@app.route("/37", methods=['GET', "POST"])
def get_work_37():
    if request.method == "GET":
        file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_37.json"
        return get_work(file_json,"37")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        ret = post_kintai_state("37",switch["num"])
        return ret
@app.route("/36", methods=['GET', "POST"])
def get_work_36():
    if request.method == "GET":
        file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_36.json"
        return get_work(file_json,"36")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        ret = post_kintai_state("36",switch["num"])
        return ret
@app.route("/35", methods=['GET', "POST"])
def get_work_35():
    if request.method == "GET":
        #file_json = "./time/work_35.json"
        file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_35.json"
        return get_work(file_json,"35")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        ret = post_kintai_state("35",switch["num"])
        return ret

@app.route("/34", methods=['GET', "POST"])
def get_work_34():
    if request.method == "GET":
        file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_34.json"
        return get_work(file_json,"34")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        ret = post_kintai_state("34",switch["num"])
        return ret
@app.route("/33", methods=['GET', "POST"])
def get_work_33():
    if request.method == "GET":
        file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_33.json"
        return get_work(file_json,"33")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        ret = post_kintai_state("33",switch["num"])
        return ret
@app.route("/32", methods=['GET', "POST"])
def get_work_32():
    if request.method == "GET":
        file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_32.json"
        return get_work(file_json,"32")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        ret = post_kintai_state("32",switch["num"])
        return ret
@app.route("/31", methods=['GET', "POST"])
def get_work_31():
    if request.method == "GET":
        file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_31.json"
        return get_work(file_json,"31")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        ret = post_kintai_state("31",switch["num"])
        return ret
@app.route("/30", methods=['GET', "POST"])
def get_work_30():
    if request.method == "GET":
        file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_30.json"
        return get_work(file_json,"30")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        ret = post_kintai_state("30",switch["num"])
        return ret
@app.route("/10", methods=['GET', "POST"])
def get_work_10():
    if request.method == "GET":
        file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_10.json"
        return get_work(file_json,"10")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        ret = post_kintai_state("10",switch["num"])
        return ret
@app.route("/11", methods=['GET', "POST"])
def get_work_11():
    if request.method == "GET":
        file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_11.json"
        return get_work(file_json,"11")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        ret = post_kintai_state("11",switch["num"])
        return ret
@app.route("/14", methods=['GET', "POST"])
def get_work_14():
    if request.method == "GET":
        file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_14.json"
        return get_work(file_json,"14")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        ret = post_kintai_state("14",switch["num"])
        return ret
@app.route("/15", methods=['GET', "POST"])
def get_work_15():
    if request.method == "GET":
        file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_15.json"
        return get_work(file_json,"15")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        ret = post_kintai_state("15",switch["num"])
        return ret
@app.route("/content", methods=['GET'])
def get_work_content():
    #file_json = "./time/work_34.json"
    file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_content.json"
    return get_work_content(file_json)

@app.route("/seat", methods=['GET'])
def get_work_seat():
    file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/s_zaseki.json"
    return get_seat_info(file_json)

environment_info_co = "-"
environment_info_temp = "-"
environment_info_humidity = "-"
@app.route('/environment', methods=['POST'])
def get_environment():
    data = json.loads(request.data)
    print(request)
    print(request.data)
    print(data["point"],data["co"],data["temp"],data["humidity"])
    #
    global environment_info_co
    global environment_info_temp
    global environment_info_humidity

    environment_info_co = data["co"]
    environment_info_temp = data["temp"]
    environment_info_humidity = data["humidity"]
    return jsonify({"result": "ok"})


def post_kintai_state(sect, id):
    #変換用のJSONファイル名設定
    file_json = './WorkData_temp_' + sect + '.json'
    now = datetime.datetime.now() # 現在時刻の取得
    n_time = now.strftime('%H:%M') + '.'
    #print(n_time)

    #表示用のJSONファイル読込
    fp_zaseki = open (file_json,encoding='utf-8')
    json_str = fp_zaseki.read()
    dict_src_json = json.loads(json_str)
    fp_zaseki.close()

    #ファイル読み込み以上処理を追加★

    #idのデータを読み込んで状態を変更
    #対象：出社、出社業務中、退勤
    state = dict_src_json[id]["state"]
    name = dict_src_json[id]["name"]
    time = ""
    if state != "None" and name != "None":
        state = dict_src_json[id]["state"]["Value"]
        name = dict_src_json[id]["name"]["DisplayName"]

        if "出社勤務中" in state:
            new_state = state.replace('出社勤務中','退勤')
            time = n_time
        elif "出社" in state:
            new_state = state.replace('出社','出社勤務中')
        else:
            new_state = state.replace('退勤','出社')

        #print(name,":",state,"->",new_state,time)
        dict_src_json[id]["state"]["Value"] = new_state

        set_time = dict_src_json[id]["work_e_time"]
        #if "(在宅終了)～" in set_time:
        #    if time == "":
        #        print(n_time)
        #        tmp = dict_src_json[id]["work_e_time"]
        #    else:
        #        tmp = dict_src_json[id]["work_e_time"]
        #        tmp = tmp + time
        #    dict_src_json[id]["work_e_time"] = tmp
        if time == "" and "在宅終了" in set_time:
            time = dict_src_json[id]["home_e_time"] + "(在宅終了)～"
            set_time = ""
        if time != "" and "在宅終了" in set_time:
            dict_src_json[id]["work_e_time"] = dict_src_json[id]["work_e_time"] + time
        if set_time == "" or "." in set_time:
            dict_src_json[id]["work_e_time"] = time


        with open(file_json, "w", encoding='utf-8') as f:
            json.dump(dict_src_json, f, indent=4, ensure_ascii=False)

    #更新JSONデータを返却
    fp_zaseki = open (file_json,encoding='utf-8')
    json_str = fp_zaseki.read()
    dict_src_json = json.loads(json_str)

    return make_response(jsonify(dict_src_json))
    
file_update_time2 = [""]
def get_work_content(path):
    #前回からファイルが更新されたか確認
    t = os.path.getmtime(path)
    d = datetime.datetime.fromtimestamp(t)
 
    #ファイル時間更新
    file_update_time2 = str(d)

    #TEAMSのJSONファイル読込
    file_json = path
    fp_in = open (file_json,encoding='utf-8')
    json_str = fp_in.read()
    fp_in.close()

    dict_aa = json.loads(json_str)

    return make_response(jsonify(dict_aa))

#file_update_time3 = [""]
def get_seat_info(path):
    #前回からファイルが更新されたか確認
    #t = os.path.getmtime(path)
    #d = datetime.datetime.fromtimestamp(t)
 
    #ファイル時間更新
    #file_update_time3 = str(d)

    #座席のJSONファイル読込
    file_json = path
    fp_zaseki = open (file_json,encoding='utf-8')
    json_str = fp_zaseki.read()
    dict_src_json = json.loads(json_str)
    fp_zaseki.close()
    #変換用のJSONファイル名設定
    file_name = './SeatData_temp.json'

    #元になる中間ファイル再作成
    file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_30.json"
    get_work(file_json,"30")
    file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_33.json"
    get_work(file_json,"33")
    file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_35.json"
    get_work(file_json,"35")
    file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_36.json"
    get_work(file_json,"36")
    file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_37.json"
    get_work(file_json,"37")
    file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_39.json"
    get_work(file_json,"39")
    file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_10.json"
    get_work(file_json,"10")
    file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_11.json"
    get_work(file_json,"11")
    file_json = R"C:/Users/7003861/OneDrive - Panasonic/share_data/work_15.json"
    get_work(file_json,"15")
    #仙台座席用JSONアップデート
    #33,35,36,37課データから1つのJSONファイル作成
    input_files = ["./WorkData_temp_30.json",
                   "./WorkData_temp_33.json",
                   "./WorkData_temp_35.json",
                   "./WorkData_temp_36.json",
                   "./WorkData_temp_37.json",
                   "./WorkData_temp_39.json",
                   "./WorkData_temp_10.json",
                   "./WorkData_temp_11.json",
                   "./WorkData_temp_15.json"]
    output_file = "./SendaiSeatData.json"
    combine_json_files(input_files, output_file)
    print("OK--------")
    #仙台座席用JSON読み込み
    file_json = output_file
    fp_seat = open (file_json,encoding='utf-8')
    json_kintai_str = fp_seat.read()
    dict_kintai_json = json.loads(json_kintai_str)
    temp_time = dict_kintai_json[0]["get_time"]
    fp_seat.close()

    with open(file_name, 'w',encoding='utf-8') as f:
        f.write('[')    #JSON開始
        for list, has_more in lookahead(dict_src_json):
            #氏名(柱、通路以外）の場合情報を検索
            #座席氏名を設定
            seat_name = list["name"]

            #勤怠JSONから状態を設定
            sate,name,sub = get_kintai_state(seat_name,dict_kintai_json)
            #print(seat_name, sate)
            list["state"] = ""
            if sate != "":
                list["state"] = sate
            if sub != "":
                list["substate"] = sub
            if name != "":
                list["name"] = name
            if seat_name == "通路":
                list["state"] = temp_time
                temp_time = ""
            #jsonデータ書き込み
            json.dump(list, f, indent=2, ensure_ascii=False)
            if has_more:
                f.write(',')
        f.write(']')
    
    fp_seat = open (file_name, encoding='utf-8')
    json_kintai_str = fp_seat.read()
    dict_ret = json.loads(json_kintai_str)

    return make_response(jsonify(dict_ret))

def get_kintai_state(name, find_list):
    #非表示の文字は空を返却
    if "柱" in name:
        return "","",""
    if "通路" in name:
        return "","",""
    if "入口" in name:
        return "","",""
    if "課" in name:
        return "","",""
    if "3F South" in name:
        co = environment_info_co + "ppm"
        temp = environment_info_temp + "℃"
        hum = environment_info_humidity + "%"
        mrg = temp + "/" + hum
        return mrg,"試験中",co
    #座席リストをから対象人物を検索しデータを設定
    for list, has_more in lookahead(find_list):
        kintai_name = list["name"]["DisplayName"]
        kintai_name = kintai_name.replace(' ', '')

        if name in kintai_name:
            kintai_name = kintai_name[:4]
            kintai_satet = list["state"]["Value"]
            kintai_satet = kintai_satet[:4]
            if kintai_satet == "出社勤務":
                kintai_satet = "出社"
            kintai_subsatet = list["time_off"]["Value"]
            kintai_subsatet = kintai_subsatet[:4]
            endstr = kintai_subsatet.find('(')
            if endstr >= 0:
                kintai_subsatet = kintai_subsatet[:kintai_subsatet.find('(')]
                #print(kintai_subsatet,endstr)

            endstr = kintai_subsatet.find('（')
            if endstr >= 0:
                kintai_subsatet = kintai_subsatet[:kintai_subsatet.find('（')]
                #print(kintai_subsatet,endstr)

            return kintai_satet,kintai_name,kintai_subsatet
    return "-","",""


def combine_json_files(input_files, output_file):
    with open(output_file, 'w',encoding='utf-8') as f:
        f.write('[')    #JSON開始
        for i, input in enumerate(input_files):
            file_path = os.path.join("./", input)
            #with open(file_path, 'r', encoding='utf-8') as file:
            fp_in = open (file_path,encoding='utf-8')
            json_str = fp_in.read()
            fp_in.close()
            dict_json = json.loads(json_str)

            first = 0
            for list, has_more in lookahead(dict_json):
                #2回目以降、次Noneじゃない場合。
                #if has_more or i < len(input_files) - 1:
                if first != 0 and list["name"] != "None":
                    f.write(',')
                first = 1
                if list["name"] != "None":
                    make = makeDisplayJson(list)
                    json.dump(make, f, indent=2, ensure_ascii=False)
            if i < len(input_files) - 1:
                f.write(',')

        f.write(']')

def get_value_from_json( parent_data, key_list):
    value = ''
    for key in key_list:
        if type(parent_data) is dict:
            value = parent_data.get(key, '')
        elif type(parent_data) is list and type(key) is int:
            value = parent_data[key] if key < len(parent_data) else ''
        else:
            value = ''
        if value == '':
            break
        parent_data = value
    return value

file_update_time = ["no","no","no","no","no","no","no","no","no","no",
                    "no","no","no","no","no","no","no","no","no","no",
                    "no","no","no","no","no","no","no","no","no","no",
                    "no","no","no","no","no","no","no","no","no","no"]

file_state_reset = ["-","-","-","-","-","-","-","-","-","-",
                    "no","no","-","-","no","no","-","-","-","-",
                    "-","-","-","-","-","-","-","-","-","-",
                    "no","no","no","no","no","no","no","no","-","no"]

### TeamsのJSONファイルを取得し、表示用のJSONファイルに変換して返却
###
def get_work(path,no):
    info_file_state = "no"
    state_reset = "no"

    now = datetime.datetime.now() # 現在時刻の取得
    n_time = now.strftime('%Y/%m/%d')
    #print(n_time)
    
    file_temp = R"C:/Users/7003861/OneDrive - Panasonic/share_data/last_time.txt"
    
    f = open(file_temp,'r')
    last_time = f.read()
    f.close()
    f = open(file_temp,'w')
    f.write(n_time)
    f.close()
    #print(no,file_state_reset)
    if(last_time != n_time):
        for cnt in range(len(file_state_reset)):
            if file_state_reset[ cnt ] == "no":
                file_state_reset[ cnt ] = "reset"
        print("日付更新リセット",last_time,n_time,file_state_reset)

    #前回からファイルが更新されたか確認
    try:
        t = os.path.getmtime(path)
    except OSError as e:
        print("teams JSON ファイル読み込みエラー")
        return "JSON ERROR 01"
    d = datetime.datetime.fromtimestamp(t)

    #変換用のJSONファイル名設定
    file_name = './WorkData_temp_' + no + '.json'
    try:
        t2 = os.path.getmtime(file_name)
    except OSError as e:
        print("勤怠情報保存ファイル読み込みエラー")
        info_file_state = "error"
        d = "9999"  #異常値設定し次のif文を回避
    
    #if(info_file_state != "error"):
    #    d2 = datetime.datetime.fromtimestamp(t2)

    #    last_date = str(d) #ファイル更新日付を取得
    #    last_date = last_date[:10]
    #    now_date = str(d2) #ファイル更新日付を取得
    #    now_date = now_date[:10]

        #if(last_date != now_date):
        #    state_reset = "yes"
    #else:
    #    d = "9999"  #異常値設定し次のif文を回避
    
    #print(d,file_update_time[31-int(no)],last_date,now_date)
    
    #日付が更新された場合はリセット
    if file_state_reset[ int(no) ] == "reset":
        file_state_reset[ int(no) ] = "no"
        state_reset = "yes"

    #ファイルのタイムスタンプに更新が無ければ既存のJSONファイルを返却
    if file_update_time[ int(no) ] in str(d) and state_reset != "yes":
        print(file_update_time[ int(no) ])
        print("No renewal",no)

        fp_old = open (file_name,encoding='utf-8')
        json_old = fp_old.read()
        fp_old.close()
        
        dict_old = json.loads(json_old)

        return make_response(jsonify(dict_old))

    if(info_file_state != "error"):
        #ファイル時間更新
        file_update_time[ int(no)] = str(d)


    #TEAMSのJSONファイル読込
    file_json = path
    fp_in = open (file_json,encoding='utf-8')
    json_str = fp_in.read()
    fp_in.close()
    dict_src_json = json.loads(json_str)
    
    #課、係を7名想定で空白で調整
    list_count = 7      #列の最大数
    new_data = {"name": "None", "state": "None", "team": "None", "flex":"None","time_off":"None","work_s_time":None,"work_e_time":None,"home_s_time":None,"home_e_time":None,"flex_s_time":None,"flex_e_time":None,"time_off_s_time":None,"time_off_e_time":None,"get_time":"None"}
    
    team_list = ["35","1係","2係","3係","4係","5係"]

    if no == "14":
        team_list = ["35","1係","2係","3係","4係","5係","6係"]

    team_count = 0
    team_list[0] = no   #対象課で再初期化

    if(info_file_state != "error"):
        ##作成済みの表示用JSONファイル読み込み
        fp_in = open (file_name,encoding='utf-8')
        json_str = fp_in.read()
        fp_in.close()
        dict_old_json = json.loads(json_str)

    #表示用JSONファイル作成
    f_flg = 0
    json_date = ""
    with open(file_name, 'w',encoding='utf-8') as f:
        f.write('[')    #JSON開始
        for i in range(len(team_list)):     #列数繰り返し
            for list, has_more in lookahead(dict_src_json):
                if f_flg == 0:
                    f_flg = 1
                    json_date = list["get_time"]
                now_str = team_list[team_count]                     #チーム判定用文字列設定
                list_str = list["team"]["Value"]                    #係情報を取得
                list_str = list_str.replace(team_list[0]+"-", '')   #係情報のみに編集

                #表示データ修正
                ## 時刻修正 0700->07:00 09:00->9:00

                ## 現在の状態を判定
                ## 業務前、出社、在宅、在宅終了、午前休、午後休、時間休
                ## 部分在宅中

                #リストの最後まで検索し対象データを設定
                if now_str in list_str:
                    #表示用データに編集
                    make = makeDisplayJson(list)
                    #jsonデータ書き込み
                    json.dump(make, f, indent=2, ensure_ascii=False)
                    f.write(',')
                    #１列の最大数デクリメント
                    list_count = list_count - 1
                    
            #列の残りをブランクで埋める
            for i in range(list_count):
                json.dump(new_data,f, indent=2, ensure_ascii=False)
                if i >= list_count - 1  and team_count >= len(team_list) - 1:
                    f.write(']')
                else:
                    f.write(',')

            team_count = team_count + 1
            list_count = 7

    #作成した表示用JSONファイル読み込み
    fp_out2 = open (file_name,encoding='utf-8')
    json_str2 = fp_out2.read()
    fp_out2.close()
    dict_dst_json2 = json.loads(json_str2)

    #異常処理：日付が変わってもJSONファイルがその日付のものに更新されなかった場合
    json_date = json_date[:10]
    json_update = "ok"
    if json_date != n_time:
        print("JSON日付:",json_date,"現在日付",n_time)
        file_update_time[ int(no)] = "no"
        json_update = "ng"

    #日付が変わったらリセット
    if(state_reset == "no"):
        ##旧作成済みファイルの状態を反映
        cnt = 0
        for list, has_more in lookahead(dict_dst_json2):
            #新表示データ
            state = list['state']
            name = list["name"]
            
            if state != "None" and name != "None":
                state = list["state"]["Value"]
                name = list["name"]["DisplayName"]
                e_time = list["work_e_time"]

                #JSON更新ない場合の異常処理
                if json_update == "ng":
                    if "出社" != state and "出社勤務中" != state and "退勤" != state:
                        list["state"]["Value"] = "出社"
                    list["flex"]["Value"] = "無"
                    list["time_off"]["Value"] = "-"
                    list["work_s_time"] = "9:00"
                    list["work_e_time"] = ""
                    list["home_s_time"] = ""
                    list["home_e_time"] = ""
                    list["flex_s_time"] = ""
                    list["flex_e_time"] = ""
                    list["time_off_s_time"] = ""
                    list["time_off_e_time"] = ""
                    list["get_time"] = "同期データ受信待ち"


                #旧表示データ
                old_name = ""
                old_time = ""
                old_state = ""
                if info_file_state == "no" and len(dict_old_json) > cnt:
                    old_state = dict_old_json[cnt]["state"]["Value"]
                    old_name = dict_old_json[cnt]["name"]["DisplayName"]
                    old_time = dict_old_json[cnt]["work_e_time"]
                #出社状態の場合、旧データを反映
                if "出社" in state and name == old_name and json_update == "ok":
                    if "出社勤務中" in old_state:
                        new_state = state.replace('出社','出社勤務中')
                    elif "退勤" in old_state:
                        new_state = state.replace('出社','退勤')
                    else:
                        new_state = state
                    list["state"]["Value"] = new_state
                #終了時刻が空白の場合、旧データを反映
                if e_time == "":
                    list["work_e_time"] = old_time

            cnt = cnt + 1
        ##状態を更新したファイルに更新
        with open(file_name, "w", encoding='utf-8') as f:
            json.dump(dict_dst_json2, f, indent=4, ensure_ascii=False)
    else:
        print("勤務状態リセット", state_reset)

    return make_response(jsonify(dict_dst_json2))

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response

@app.route("/home")
def home():
    return "This is Home page."

def getRequest():
    if request.method == 'POST':
        return request.form['message']
    else:
        return "GET Method"
    
if __name__ == '__main__':
    app.debug = True
    #app.run()
    app.run(debug=True, host="0.0.0.0", port=5001)