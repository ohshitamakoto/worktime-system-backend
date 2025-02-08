from flask import Flask, render_template, request,make_response
from flask import request, make_response, jsonify
import json
from  datetime import datetime, timedelta
import os
import shutil
from dotenv import load_dotenv
load_dotenv()
global_time_s = os.getenv('G_TIME_S')
global_cloud_dir = os.getenv('G_CLOUD_DIR')
global_local_dir = os.getenv('G_LOCAL_DIR')
global_pass = os.getenv('G_PASS')
# 出社勤務(work),出社(office),在宅,出張,年休
chart_list = [
    [0, 0, 0, 0, 0], #仙台3F
    [0, 0, 0, 0, 0], #仙台2F
    [0, 0, 0, 0, 0], #金沢7F 駅側
    [0, 0, 0, 0, 0], #金沢7F 県庁側
    [0, 0, 0, 0, 0], #定禅寺
    [0, 0, 0, 0, 0], #浜松4F
    [0, 0, 0, 0, 0], #浜松5F
    [0, 0, 0, 0, 0], #浜松6F
    [0, 0, 0, 0, 0]  #浜松ダミー
]

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
    if j_str["state"] == None:
        python_obj = {"Value": "出社"}
        j_str["state"] = python_obj
        print("勤務状態エラー",j_str,j_str["name"]["DisplayName"])

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
    start_time = global_time_s
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
        if "宮崎 裕" in sp_name:
            sp_name = sp_name + "　（金沢）"
            j_str["name"]["DisplayName"] = sp_name
        if "横長" in sp_name:
            sp_name = sp_name + "（金沢）"
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
        #if "菊地 和彦" in sp_name:
        #    j_str["state"]["Value"] = "退勤"
        #    j_str["work_s_time"] = ""
        if "高橋 寛" in sp_name:
            j_str["state"]["Value"] = "退勤"
            j_str["work_s_time"] = ""
        if "村松 寿" in sp_name:
            j_str["state"]["Value"] = "（出向中）"
            j_str["work_s_time"] = ""
    return j_str

@app.route("/39", methods=['GET', "POST"])
def get_work_39():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/work_39.json"
        return get_work(file_json,"39")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("39",switch["num"],lstate)
        return ret
@app.route("/37", methods=['GET', "POST"])
def get_work_37():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/new_work_37.json"
        return get_work(file_json,"37")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("37",switch["num"],lstate)
        return ret
@app.route("/36", methods=['GET', "POST"])
def get_work_36():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/new_work_36.json"
        return get_work(file_json,"36")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("36",switch["num"],lstate)
        return ret
    
@app.route("/35", methods=['GET', "POST"])
def get_work_35():
    if request.method == "GET":
        #file_json = "./time/work_35.json"
        file_json = R""+ global_cloud_dir + "share_data/new_work_35.json"
        return get_work(file_json,"35")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("35",switch["num"],lstate)
        return ret

## 定禅寺オフィスメンバ
@app.route("/50", methods=['GET', "POST"])
def get_work_50():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/new_work_35.json"
        get_work(file_json,"35")
        file_json = R""+ global_cloud_dir + "share_data/new_work_36.json"
        get_work(file_json,"36")
        file_json_1 = "./teams_data/WorkData_temp_35.json"
        file_json_2 = "./teams_data/WorkData_temp_36.json"
        combined_json = "./teams_data/WorkData_temp_50.json"
        return combine_sect_json(file_json_1, file_json_2, combined_json)
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        if switch["num"] >= 42:
            lnum = switch["num"] - 14
            ret = post_kintai_state("36",lnum,lstate)
        else:
            ret = post_kintai_state("35",switch["num"],lstate)
        
        file_json_1 = "./teams_data/WorkData_temp_35.json"
        file_json_2 = "./teams_data/WorkData_temp_36.json"
        combined_json = "./teams_data/WorkData_temp_50.json"
        return combine_sect_json(file_json_1, file_json_2, combined_json)
        #return ret

def combine_sect_json(output_file_1, output_file_2, output_file):
    combined_data = ""
    lout_file = output_file
    # JSONファイルを読み込み
    with open(output_file, 'w', encoding='utf-8') as output_file:
        output_file.write('[')    #JSON開始
        with open(output_file_1, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for list, has_more in lookahead(data):
                json.dump(list, output_file, indent=2, ensure_ascii=False)
                output_file.write(',')
        with open(output_file_2, 'r', encoding='utf-8') as file:
            data = json.load(file)
            del data[:28]
            del data[7:]
            for list, has_more in lookahead(data):
                json.dump(list, output_file, indent=2, ensure_ascii=False)
                if(has_more):
                    output_file.write(',')
        output_file.write(']')

    fp_in = open (lout_file,encoding='utf-8')
    json_str = fp_in.read()
    fp_in.close()
    dict_src_json = json.loads(json_str)
    
    return  make_response(jsonify(dict_src_json))

def json_analyze(json):
    if "state" in json:
        return json["state"]
    else:
        return ""

@app.route("/history", methods=['GET', "POST"])
def get_workhis():
    if request.method == "GET":
        return "GET"
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        if switch["name"] == None:
            return "NG"
        if switch["sect"] == None:
            return "NG"
            
        lsect = int(switch["sect"])
        print(switch["name"],switch["sect"],lsect)
        if lsect<=19:
            file_json = R""+ global_cloud_dir + "share_data/history/new_work_his_musen.json"
        elif lsect<=29:
            file_json = R""+ global_cloud_dir + "share_data/history/new_work_his_system.json"
        else:
            file_json = R""+ global_cloud_dir + "share_data/history/new_work_his_AI.json"

        return get_workhis(file_json,switch["sect"],switch["name"],"")
    
@app.route("/34", methods=['GET', "POST"])
def get_work_34():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/new_work_34.json"
        return get_work(file_json,"34")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("34",switch["num"],lstate)
        return ret
@app.route("/33", methods=['GET', "POST"])
def get_work_33():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/work_33.json"
        return get_work(file_json,"33")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("33",switch["num"],lstate)
        return ret
@app.route("/32", methods=['GET', "POST"])
def get_work_32():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/work_32.json"
        return get_work(file_json,"32")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("32",switch["num"],lstate)
        return ret
@app.route("/31", methods=['GET', "POST"])
def get_work_31():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/work_31.json"
        return get_work(file_json,"31")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("31",switch["num"],lstate)
        return ret
@app.route("/30", methods=['GET', "POST"])
def get_work_30():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/work_30.json"
        return get_work(file_json,"30")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("30",switch["num"],lstate)
        return ret
@app.route("/10", methods=['GET', "POST"])
def get_work_10():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/work_10.json"
        return get_work(file_json,"10")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("10",switch["num"],lstate)
        return ret
@app.route("/11", methods=['GET', "POST"])
def get_work_11():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/work_11.json"
        return get_work(file_json,"11")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("11",switch["num"],lstate)
        return ret
@app.route("/14", methods=['GET', "POST"])
def get_work_14():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/work_14.json"
        return get_work(file_json,"14")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("14",switch["num"],lstate)
        return ret
@app.route("/15", methods=['GET', "POST"])
def get_work_15():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/work_15.json"
        return get_work(file_json,"15")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("15",switch["num"],lstate)
        return ret
@app.route("/20", methods=['GET', "POST"])
def get_work_20():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/new_work_20.json"
        return get_work(file_json,"20")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("20",switch["num"],lstate)
        return ret
@app.route("/21", methods=['GET', "POST"])
def get_work_21():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/new_work_21.json"
        return get_work(file_json,"21")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("21",switch["num"],lstate)
        return ret
@app.route("/22", methods=['GET', "POST"])
def get_work_22():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/new_work_22.json"
        return get_work(file_json,"22")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("22",switch["num"],lstate)
        return ret
@app.route("/23", methods=['GET', "POST"])
def get_work_23():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/new_work_23.json"
        return get_work(file_json,"23")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("23",switch["num"],lstate)
        return ret
@app.route("/24", methods=['GET', "POST"])
def get_work_24():
    if request.method == "GET":
        file_json = R""+ global_cloud_dir + "share_data/new_work_24.json"
        return get_work(file_json,"24")
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        
        print(switch["num"])
        lstate = json_analyze(switch)
        ret = post_kintai_state("24",switch["num"],lstate)
        return ret
@app.route("/content", methods=['GET', "POST"])
def get_work_content():
    file_json = R""+global_cloud_dir+"share_data/json_tmp/content.json"
    if request.method == "GET":
        return get_work_content(file_json)
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        print(switch["msg"],switch["tenki"])
        lmsg = switch["msg"]
        ltenki = switch["tenki"]
        return set_work_content(file_json,lmsg,ltenki)

#仙台拠点3F
@app.route("/seat", methods=['GET'])
def get_work_seat():
    file_json = R""+ global_cloud_dir + "share_data/seatinfo/sendai_zaseki3f.json"
    return get_seat_info(file_json,'./SeatData_s_3f_temp.json',"./teams_data/jointData_SendaiSeat_3f.json",0)
#仙台拠点2F
@app.route("/seat_s_2f", methods=['GET'])
def get_work_seat_s2f():
    file_json = R""+ global_cloud_dir + "share_data/seatinfo/sendai_zaseki2f.json"
    return get_seat_info(file_json,'./SeatData_s_2f_temp.json',"./teams_data/jointData_SendaiSeat_2f.json",1)
#仙台定禅寺オフィス
@app.route("/seat_j", methods=['GET'])
def get_work_seat_j():
    file_json = R""+ global_cloud_dir + "share_data/seatinfo/jozenji_zaseki6f.json"
    return get_seat_info(file_json,'./SeatData_j_6f_temp.json',"./teams_data/jointData_JozenjiSeat_6f.json",4)
#金沢駅側7F
@app.route("/seat_k_7fs2", methods=['GET'])
def get_work_seat_k7fs2():
    file_json = R""+ global_cloud_dir + "share_data/seatinfo/kanazawa_zaseki_7fs.json"
    return get_seat_info(file_json,'./SeatData_k_7fs_temp.json',"./teams_data/jointData_KanazawaSeat_7fs.json",2)
#金沢県庁側7F
@app.route("/seat_k_7fp2", methods=['GET'])
def get_work_seat_k7fp2():
    file_json = R""+ global_cloud_dir + "share_data/seatinfo/kanazawa_zaseki_7fp.json"
    return get_seat_info(file_json,'./SeatData_k_7fp_temp.json',"./teams_data/jointData_KanazawaSeat_7fp.json",3)

@app.route("/seat_h", methods=['GET'])
def get_work_seat_h():
    file_json = R""+ global_cloud_dir + "share_data/h_zaseki.json"
    return get_seat_info(file_json,'./SeatData_h_temp.json',"./teams_data/KanazawaSeatData_h.json",8)
#浜松4F
@app.route("/seat_h_free4f", methods=['GET', "POST"])
def get_work_seat_h_free4f():
    if request.method == "GET":
        #make_freeseat_data("","","RESET4F","","")
        return get_seat_info('./SeatFreeData4f_temp.json','./SeatData_h_free4f_temp.json',"./teams_data/jointData_Hamamatsu_4f.json",5)
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        print(switch["name"],switch["sect"],switch["no"])
        lname = switch["name"]
        lname = lname.replace(' ','')
        lsect = switch["sect"]
        lno = int(switch["no"])
        return make_freeseat_data('./SeatFreeData4f_temp.json',lsect,"POST",lname,lno)
#浜松5F
@app.route("/seat_h_free5f", methods=['GET', "POST"])
def get_work_seat_h_free5f():
    if request.method == "GET":
        #make_freeseat_data("","","RESET5F","","")
        return get_seat_info('./SeatFreeData5f_temp.json','./SeatData_h_free5f_temp.json',"./teams_data/jointData_Hamamatsu_5f.json",6)
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        print(switch["name"],switch["sect"],switch["no"])
        lname = switch["name"]
        lname = lname.replace(' ','')
        lsect = switch["sect"]
        lno = int(switch["no"])
        return make_freeseat_data('./SeatFreeData5f_temp.json',lsect,"POST",lname,lno)
#浜松6F
@app.route("/seat_h_free6f", methods=['GET', "POST"])
def get_work_seat_h_free6f():
    if request.method == "GET":
        #make_freeseat_data("","","RESET6F","","")
        return get_seat_info('./SeatFreeData6f_temp.json','./SeatData_h_free6f_temp.json',"./teams_data/jointData_Hamamatsu_6f.json",7)
    else:
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        print(switch["name"],switch["sect"],switch["no"])
        lname = switch["name"]
        lname = lname.replace(' ','')
        lsect = switch["sect"]
        lno = int(switch["no"])
        return make_freeseat_data('./SeatFreeData6f_temp.json',lsect,"POST",lname,lno)

@app.route("/qwerty/debug", methods=['GET', "POST"])
def kintai_debug():
    if request.method == "GET":
        print("デバッグモードへのアクセス GET")
        #以下の状態を返却
        #OneDrive格納ファイル（JSON正当性、タイムスタンプ）
        #中間ファイル（JSON正当性、タイムスタンプ）
        return debug_ctl_get("","","")
        #return "OK"
    else:
        print("デバッグモードへのアクセス POST")
        #OneDrivbeの更新
        #WorkData_temp_xxファイルの削除
        #浜松座席のリセット
        switch = request.data.decode('utf-8')  # デコード
        switch = json.loads(switch)
        lsect = switch["debug"]
        lpass = switch["pass"]
        ltxt = switch["txt"]
        return debug_ctl(lpass,lsect,ltxt)

@app.route("/trip_info", methods=['GET'])
def get_work_trip_info():
    trip_list = ["","","",""]
    file_json = R""+ global_cloud_dir + "share_data/history/new_work_his_musen.json"
    ret1 = get_workhis(file_json,0,"定禅寺","ON")
    file_json = R""+ global_cloud_dir + "share_data/history/new_work_his_system.json"
    ret2 = get_workhis(file_json,1,"定禅寺","ON")
    file_json = R""+ global_cloud_dir + "share_data/history/new_work_his_AI.json"
    ret3 = get_workhis(file_json,1,"定禅寺","ON")
    json_list1 = json.loads(ret1)
    json_list2 = json.loads(ret2)
    json_list3 = json.loads(ret3)

    trip_list[0] = " #" + json_list1["day2"]+json_list2["day2"]+json_list3["day2"]
    trip_list[1] = " #" + json_list1["day3"]+json_list2["day3"]+json_list3["day3"]
    trip_list[2] = " #" + json_list1["day4"]+json_list2["day4"]+json_list3["day4"]
    trip_list[3] = " #" + json_list1["day5"]+json_list2["day5"]+json_list3["day5"]

    for i in range(len(trip_list)):
        tmp = trip_list[i]
        if len(tmp) > 15:
            tmp = tmp.replace('なし　','')
            x = tmp.count(".")
            trip_list[i] = tmp + str(x) + "名　"
        if "土" in tmp:
            trip_list[i] = ""

    #print(trip_list)

    return trip_list

@app.route("/w_info", methods=['GET'])
def get_work_w_info():
    get_work_seat()
    get_work_seat_s2f()
    get_work_seat_k7fs2()
    get_work_seat_k7fp2()
    #get_work_seat_h()
    get_work_seat_h_free4f()
    get_work_seat_h_free5f()
    get_work_seat_h_free6f()
    get_work_seat_j()
    file_json = R""+ global_cloud_dir + "share_data/json_tmp/psnrd_data.json"
    fp_seat = open (file_json, encoding='utf-8')
    json_kintai_str = fp_seat.read()
    dict_ret = json.loads(json_kintai_str)
    #仙台拠点
    dict_ret[0]["work"] = chart_list[0][0] + chart_list[1][0]
    dict_ret[0]["office"] = chart_list[0][1] + chart_list[1][1]
    dict_ret[0]["home"] = chart_list[0][2] + chart_list[1][2]
    dict_ret[0]["trip"] = chart_list[0][3] + chart_list[1][3]
    dict_ret[0]["rest"] = chart_list[0][4] + chart_list[1][4]
    dict_ret[0]["work_1"] = chart_list[1][0]
    dict_ret[0]["work_2"] = chart_list[0][0]
    #金沢拠点
    dict_ret[2]["work"] = chart_list[2][0] + chart_list[3][0]
    dict_ret[2]["office"] = chart_list[2][1] + chart_list[3][1]
    dict_ret[2]["home"] = chart_list[2][2] + chart_list[3][2]
    dict_ret[2]["trip"] = chart_list[2][3] + chart_list[3][3]
    dict_ret[2]["rest"] = chart_list[2][4] + chart_list[3][4]
    dict_ret[2]["work_1"] = chart_list[2][0] + chart_list[3][0]
    #定禅寺拠点
    dict_ret[1]["work"] = chart_list[4][0]
    dict_ret[1]["office"] = chart_list[4][1]
    dict_ret[1]["home"] = chart_list[4][2]
    dict_ret[1]["trip"] = chart_list[4][3]
    dict_ret[1]["rest"] = chart_list[4][4]
    dict_ret[1]["work_1"] = chart_list[4][0]
    dict_ret[1]["work_2"] = chart_list[4][0]
    #浜松拠点
    dict_ret[3]["work"] = chart_list[5][0] + chart_list[6][0] + chart_list[7][0]
    dict_ret[3]["office"] = chart_list[5][1] + chart_list[6][1] + chart_list[7][1]
    dict_ret[3]["home"] = chart_list[5][2] + chart_list[6][2] + chart_list[7][2]
    dict_ret[3]["trip"] = chart_list[5][3] + chart_list[6][3] + chart_list[7][3]
    dict_ret[3]["rest"] = chart_list[5][4] + chart_list[6][4] + chart_list[7][4]
    dict_ret[3]["work_1"] = chart_list[5][0]
    dict_ret[3]["work_2"] = chart_list[6][0]
    dict_ret[3]["work_3"] = chart_list[7][0]

    #print(chart_list)
    #print(dict_ret)

    return make_response(jsonify(dict_ret))

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


def post_kintai_state(sect, id, w_st):
    #変換用のJSONファイル名設定
    file_json = './teams_data/WorkData_temp_' + sect + '.json'
    now = datetime.now() # 現在時刻の取得
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

        if w_st == "出社":
            if "出社勤務中" not in state and "出社" in state:
                new_state = state.replace('出社','出社勤務中')
            else:
                new_state = state
        else:
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
    d = datetime.fromtimestamp(t)
 
    #ファイル時間更新
    file_update_time2 = str(d)

    #TEAMSのJSONファイル読込
    file_json = path
    fp_in = open (file_json,encoding='utf-8')
    json_str = fp_in.read()
    fp_in.close()

    dict_aa = json.loads(json_str)

    return make_response(jsonify(dict_aa))

def set_work_content(path,lmsg,ltenki):
    #TEAMSのJSONファイル読込
    file_json = path

    fp_in = open (file_json,encoding='utf-8')
    json_str = fp_in.read()
    dict_src = json.loads(json_str)
    fp_in.close()

    #データ異常処理
    if ltenki not in "we_on" and ltenki not in "we_off":
        print("データ異常処理",lmsg,ltenki)
        return make_response(jsonify(dict_src))

    fp_in = open (file_json,'w', encoding='utf-8')

    fp_in.write('[{')    #JSON開始
    w_data = '"msg":"' + lmsg +'"'
    fp_in.write(w_data)    #JSON開始
    fp_in.write(',')    #JSON開始
    w_data = '"tenki":"' + ltenki +'"'
    fp_in.write(w_data)    #JSON開始
    #print(dict_src)
    fp_in.write('}]')    #JSON開始
    fp_in.close()

    return make_response(jsonify(dict_src))

def get_seat_info(path, tmp_path, out_f, place_num):
    #チャート用集計リスト初期化
    for x in range(5):
        chart_list[place_num][x] = 0

    #座席のJSONファイル読込
    file_json = path
    fp_zaseki = open (file_json,encoding='utf-8')
    json_str = fp_zaseki.read()
    dict_src_json = json.loads(json_str)
    fp_zaseki.close()
    #変換用のJSONファイル名設定
    #file_name = './SeatData_temp.json'
    file_name = tmp_path

    #元になる中間ファイル再作成
    file_json = R""+ global_cloud_dir + "share_data/work_30.json"
    get_work(file_json,"30")
    file_json = R""+ global_cloud_dir + "share_data/work_31.json"
    get_work(file_json,"31")
    file_json = R""+ global_cloud_dir + "share_data/work_32.json"
    get_work(file_json,"32")
    file_json = R""+ global_cloud_dir + "share_data/work_33.json"
    get_work(file_json,"33")
    file_json = R""+ global_cloud_dir + "share_data/new_work_34.json"
    get_work(file_json,"34")
    file_json = R""+ global_cloud_dir + "share_data/new_work_35.json"
    get_work(file_json,"35")
    file_json = R""+ global_cloud_dir + "share_data/new_work_36.json"
    get_work(file_json,"36")
    file_json = R""+ global_cloud_dir + "share_data/new_work_37.json"
    get_work(file_json,"37")
    file_json = R""+ global_cloud_dir + "share_data/work_39.json"
    get_work(file_json,"39")

    file_json = R""+ global_cloud_dir + "share_data/work_10.json"
    get_work(file_json,"10")
    file_json = R""+ global_cloud_dir + "share_data/work_11.json"
    get_work(file_json,"11")
    file_json = R""+ global_cloud_dir + "share_data/work_14.json"
    get_work(file_json,"14")
    file_json = R""+ global_cloud_dir + "share_data/work_15.json"
    get_work(file_json,"15")
    
    file_json = R""+ global_cloud_dir + "share_data/new_work_20.json"
    get_work(file_json,"20")
    file_json = R""+ global_cloud_dir + "share_data/new_work_21.json"
    get_work(file_json,"21")
    file_json = R""+ global_cloud_dir + "share_data/new_work_22.json"
    get_work(file_json,"22")
    file_json = R""+ global_cloud_dir + "share_data/new_work_23.json"
    get_work(file_json,"23")
    file_json = R""+ global_cloud_dir + "share_data/new_work_24.json"
    get_work(file_json,"24")

    #仙台座席用JSONアップデート
    #33,35,36,37課データから1つのJSONファイル作成
    input_files = ["./teams_data/WorkData_temp_30.json",
                   "./teams_data/WorkData_temp_31.json",
                   "./teams_data/WorkData_temp_32.json",
                   "./teams_data/WorkData_temp_33.json",
                   "./teams_data/WorkData_temp_34.json",
                   "./teams_data/WorkData_temp_35.json",
                   "./teams_data/WorkData_temp_36.json",
                   "./teams_data/WorkData_temp_37.json",
                   "./teams_data/WorkData_temp_39.json",
                   "./teams_data/WorkData_temp_10.json",
                   "./teams_data/WorkData_temp_11.json",
                   "./teams_data/WorkData_temp_14.json",
                   "./teams_data/WorkData_temp_15.json",
                   "./teams_data/WorkData_temp_20.json",
                   "./teams_data/WorkData_temp_21.json",
                   "./teams_data/WorkData_temp_22.json",
                   "./teams_data/WorkData_temp_23.json",
                   "./teams_data/WorkData_temp_24.json"]
    #output_file = "./teams_data/SendaiSeatData.json"
    output_file = out_f
    combine_json_files(input_files, output_file)
    #print("OK--------")
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
            sate,name,sub,chart_data = get_kintai_state(seat_name,dict_kintai_json)
            
            if chart_data <= 4:
                chart_list[place_num][chart_data] = chart_list[place_num][chart_data] + 1

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

    #浜松だけフリーアドレスのため再集計　chart_list　1,2,3,4
    if place_num >= 5 and place_num <= 7:
        file_json = R""+ global_cloud_dir + "share_data/seatinfo/hamamatsu_meibo.json"
        fp_seat = open (file_json,encoding='utf-8')
        json_hmeibo_str = fp_seat.read()
        hmeibo_json = json.loads(json_hmeibo_str)
        fp_seat.close()

        chart_list[place_num][1] = 0
        chart_list[place_num][2] = 0
        chart_list[place_num][3] = 0
        chart_list[place_num][4] = 0

        if place_num == 5:
            for list, has_more in lookahead(hmeibo_json):
                seat_name = list["name"]
                sate,name,sub,chart_data = get_kintai_state(seat_name,dict_kintai_json)
                if chart_data >= 1 and chart_data <= 4:
                    chart_list[place_num][chart_data] = chart_list[place_num][chart_data] + 1
                #print(seat_name,chart_data)

    return make_response(jsonify(dict_ret))

def get_kintai_state(name, find_list):
    #非表示の文字は空を返却
    if "柱" in name:
        return "","","",99
    if "通路" in name:
        return "","","",99
    if "入口" in name:
        return "","","",99
    if "課" in name:
        return "","","",99
    if "3F South" in name:
        co = environment_info_co + "ppm"
        temp = environment_info_temp + "℃"
        hum = environment_info_humidity + "%"
        mrg = temp + "/" + hum
        return mrg,"試験中",co,99
    #座席リストをから対象人物を検索しデータを設定
    for list, has_more in lookahead(find_list):
        kintai_name = list["name"]["DisplayName"]
        kintai_name = kintai_name.replace(' ', '')

        if name in kintai_name:
            kintai_name = kintai_name[:4]
            kintai_satet = list["state"]["Value"]
            kintai_satet = kintai_satet[:4]
            num = get_chart_data(kintai_satet)
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
            #print(kintai_name,num)
            return kintai_satet,kintai_name,kintai_subsatet,num
    return "-","","",99

def get_chart_data(name):
    if "出社勤務" in name:
        ret = 0 #'work'
    elif "出社" in name or "退勤" in name:
        ret = 1 #'office'
    elif "在宅" in name:
        ret = 2 #'home'
    elif "出張" in name:
        ret = 3 #'trip'
    else:
        ret = 4 #'rest' 年休

    return ret

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
                if list["name"] != "None":
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

def make_freeseat_data(path,sect,kind,name,no):
    if kind == "POST":
        #print("POST",path,10)
        fp_zaseki = open (path,encoding='utf-8')
        json_str = fp_zaseki.read()
        dict_src_json = json.loads(json_str)
        fp_zaseki.close()

        if dict_src_json[no]["name"] != "Free" and name != "Free":
            return "座席を指定できませんでした。固定席または既に指定済みの席です。"
        else:
            dict_src_json[no]["name"] = name
            dict_src_json[no]["sect"] = sect

        with open(path, "w") as json_file:
            json.dump(dict_src_json, json_file, indent=4)
        make_response(jsonify(dict_src_json))
        return "OK"
    elif kind == "RESET": #RESET
        # sahreフォルダの座席情報から当日の座席情報を作成
        # 浜松4Fベースデータ作成
        print("RESET",path)
        path = R""+ global_cloud_dir + "share_data/seatinfo/hamamatsu_zaseki4f.json"
        file_json = './SeatFreeData4f_temp.json'
        try:
            shutil.copy(path,file_json)
        except FileNotFoundError:
            print("指定されたファイルが見つかりません")

        # 浜松5Fベースデータ作成
        path = R""+ global_cloud_dir + "share_data/seatinfo/hamamatsu_zaseki5f.json"
        file_json = './SeatFreeData5f_temp.json'
        try:
            shutil.copy(path,file_json)
        except FileNotFoundError:
            print("指定されたファイルが見つかりません")

        # 浜松6Fベースデータ作成
        path = R""+ global_cloud_dir + "share_data/seatinfo/hamamatsu_zaseki6f.json"
        file_json = './SeatFreeData6f_temp.json'
        try:
            shutil.copy(path,file_json)
        except FileNotFoundError:
            print("指定されたファイルが見つかりません")
    elif kind == "RESET4F": #RESET
        # sahreフォルダの座席情報から当日の座席情報を作成
        print("RESET",path)
        path = R""+ global_cloud_dir + "share_data/seatinfo/hamamatsu_zaseki4f.json"
        file_json = './SeatFreeData4f_temp.json'
        try:
            shutil.copy(path,file_json)
        except FileNotFoundError:
            print("指定されたファイルが見つかりません")
    elif kind == "RESET5F": #RESET
        # sahreフォルダの座席情報から当日の座席情報を作成
        # 浜松5Fベースデータ作成
        path = R""+ global_cloud_dir + "share_data/seatinfo/hamamatsu_zaseki5f.json"
        file_json = './SeatFreeData5f_temp.json'
        try:
            shutil.copy(path,file_json)
        except FileNotFoundError:
            print("指定されたファイルが見つかりません")
    elif kind == "RESET6F": #RESET
        # sahreフォルダの座席情報から当日の座席情報を作成
        # 浜松6Fベースデータ作成
        path = R""+ global_cloud_dir + "share_data/seatinfo/hamamatsu_zaseki6f.json"
        file_json = './SeatFreeData6f_temp.json'
        try:
            shutil.copy(path,file_json)
        except FileNotFoundError:
            print("指定されたファイルが見つかりません")
    else:
        print("処理なし")

    return "OK"

### 申請履歴情報

def get_workhis(path,no,name,trip):
    history_list = ["not supported","not supported","not supported","not supported","not supported"]
    day_name = ["（月）","（火）","（水）","（木）","（金）","（土）","（日）"]

    if (os.path.exists(path)) == False:
        person_history = {
        "day1":history_list[0],
        "day2":history_list[1],
        "day3":history_list[2],
        "day4":history_list[3],
        "day5":history_list[4],
        "name":name
        }
        ## JSONファイルを返却
        return json.dumps(person_history)

    ## 申請履歴のJSONファイル読み込み
    file_json = path
    fp_in = open (file_json,encoding='utf-8')
    json_str = fp_in.read()
    fp_in.close()
    r_ret = "OK"
    try:
        json_list = json.loads(json_str)
    except json.JSONDecodeError as e:
        r_ret = "NG"
    except OSError as e:
        r_ret = "NG"
    if r_ret == "NG":
        return json.dumps(person_history)
    
    ## 今日の日付設定
    now = datetime.now() # 現在時刻の取得
    dow =  now.weekday()
    n_time = now.strftime('%Y%m%d') + day_name[dow]
    history_list[0] = now - timedelta(days=1)
    dow =  history_list[0].weekday()
    history_list[0] = history_list[0].strftime('%Y%m%d') + day_name[dow]
    history_list[1] = n_time
    history_list[2] = now + timedelta(days=1)
    dow =  history_list[2].weekday()
    history_list[2] = history_list[2].strftime('%Y%m%d') + day_name[dow]
    history_list[3] = now + timedelta(days=2)
    dow =  history_list[3].weekday()
    history_list[3] = history_list[3].strftime('%Y%m%d') + day_name[dow]
    history_list[4] = now + timedelta(days=3)
    dow =  history_list[4].weekday()
    history_list[4] = history_list[4].strftime('%Y%m%d') + day_name[dow]

    g_name = name.replace(' ','')

    if trip == "ON" and no == 0:
        for i in range(5):
            history_list[i] = history_list[i] + "なし　"

    ## 該当者のファイルのみ抽出
    # 氏名判定
    for list, has_more in lookahead(json_list):
        if trip == "ON":
            l_name = "定禅寺"
        else:
            l_name = list["name"]["DisplayName"]
            l_name = l_name.replace(' ','')

        if g_name in l_name:
            ## 一致した場合、日付判定
            for i in range(len(history_list)):     #列数繰り返し
                #print(list["get_date"])
                if trip == "ON":
                    if str(list["get_date"]) in history_list[i]:
                        if l_name in str(list["state"]["Value"]):
                            lstr = list["name"]["DisplayName"]
                            s_str = lstr.find("(") + 1
                            e_str = lstr.find(")")
                            lstr = lstr[s_str:e_str]
                            history_list[i] = history_list[i] + lstr + ".　"
                else:
                    # 勤務状態設定
                    if str(list["get_date"]) in history_list[i]:
                        l_timeoff = ""
                        if list["time_off"]["Value"] != "-" and list["time_off"]["Value"] != "無":
                            l_timeoff = "/" + list["time_off"]["Value"]
                        history_list[i] = history_list[i] + ":" +list["state"]["Value"] + l_timeoff

                        # フレックス情報設定
                        if str(list["flex"]["Value"]) == "有":
                            l_flex = str(list["flex_s_time"]) + "~" + str(list["flex_e_time"])
                            l_flex = l_flex.replace('フレ：','')
                            l_flex = l_flex.replace('\u3000','')
                            history_list[i] = history_list[i] + "(フレックス " + l_flex + ")"
                            #history_list[i] = history_list[i].encode(encoding='utf-8')
                        # 時間休情報設定
                        if str(list["time_off"]["Value"]) == "有":
                            history_list[i] = history_list[i] + "(時間休 " + str(list["time_off_s_time"]) + str(list["time_off_e_time"])  + ")"
                #print(history_list)

    if trip != "ON":
        for i in range(len(history_list)):     #列数繰り返し
            if "土" in history_list[i] or "日" in history_list[i]:
                history_list[i] = history_list[i] + ":-----"
            if len(history_list[i]) <= 11:
                history_list[i] = history_list[i] + ":出社"
            #年月日挿入
            tmp_str = history_list[i]
            l_day = tmp_str[6:8] + "日"
            l_mon = tmp_str[4:6] + "月"
            l_year = tmp_str[0:4] + "年"
            history_list[i] = l_year + l_mon + l_day + tmp_str[8:]
    if trip == "ON" and no == 1:
        for i in range(len(history_list)):     #列数繰り返し
            tmp_str = history_list[i]
            history_list[i] = tmp_str[11:]
    if trip == "ON" and no == 0:
        for i in range(len(history_list)):     #列数繰り返し
            #年月日挿入
            tmp_str = history_list[i]
            l_day = tmp_str[6:8] + "日"
            l_mon = tmp_str[4:6] + "月"

            history_list[i] = l_mon + l_day + tmp_str[8:]
    ## 当日-1日+3日間の計5日間のリストを作成
    person_history = {
        "day1":history_list[0],
        "day2":history_list[1],
        "day3":history_list[2],
        "day4":history_list[3],
        "day5":history_list[4],
        "name":name
    }
    
    #print(person_history)

    ## JSONファイルを返却

    return json.dumps(person_history, ensure_ascii=False)

file_update_time = ["no","no","no","no","no","no","no","no","no","no",
                    "no","no","no","no","no","no","no","no","no","no",
                    "no","no","no","no","no","no","no","no","no","no",
                    "no","no","no","no","no","no","no","no","no","no"]

file_state_reset = ["-","-","-","-","-","-","-","-","-","-",
                    "no","no","-","-","no","no","-","-","-","-",
                    "no","no","no","no","no","-","-","-","-","-",
                    "no","no","no","no","no","no","no","no","-","no"]
sect_dat = [10,11,14,15,20,21,22,23,24,30,31,32,33,34,35,36,37,39]
### TeamsのJSONファイルを取得し、表示用のJSONファイルに変換して返却
###
def get_work(path,no):
    info_file_state = "no"
    state_reset = "no"
    day_reset = "no"

    now = datetime.now() # 現在時刻の取得
    n_time = now.strftime('%Y/%m/%d')
    #print(now)
    
    file_temp = R""+ global_cloud_dir + "share_data/worktime/last_time.txt"
    
    up_t = os.path.getmtime(file_temp)
    up_t_int = datetime.fromtimestamp(up_t)
    up_t_str = str(up_t_int)
    up_t_str = up_t_str[:10]
    up_t_str = up_t_str.replace("-", '/') 

    #print(no,file_state_reset)
    #print(n_time,len(n_time),up_t_str,len(n_time))
    if(no == "35" or no == "11"):
        #print("One Drive Update")
        dummy_temp = R""+ global_cloud_dir + "share_data/dumy2.txt"
        f_dummy = open(dummy_temp,'w')
        f_dummy.write(str(now))
        f_dummy.close()

    #リセット誤検知防止のため二重判定
    #ファイル更新日時と現在日時で異なっているか判定
    if(up_t_str != n_time):
        print("リセット条件1 成立",n_time,len(n_time),up_t_str,len(up_t_str))
        #現在日時と書き込み日時が異なっているか判定
        f = open(file_temp,'r')
        last_time = f.read()
        f.close()

        if(last_time != n_time and len(last_time)==10 ):
            print("リセット条件2 成立 リセット！",last_time,len(last_time),n_time,len(n_time))
            f = open(file_temp,'w')
            f.write(n_time)
            f.close()

            day_reset = "yes"
            for cnt in range(len(file_state_reset)):
                if file_state_reset[ cnt ] == "no":
                    file_state_reset[ cnt ] = "reset"
            #print("日付更新リセット",last_time,n_time,file_state_reset)

    #前回からファイルが更新されたか確認
    try:
        t = os.path.getmtime(path)
    except OSError as e:
        print("teams JSON ファイル読み込みエラー")
        return "JSON ERROR 01"
    d = datetime.fromtimestamp(t)

    #変換用のJSONファイル名設定
    file_name = './teams_data/WorkData_temp_' + no + '.json'
    try:
        t2 = os.path.getmtime(file_name)
    except OSError as e:
        print("勤怠情報保存ファイル読み込みエラー")
        info_file_state = "error"
        d = "9999"  #異常値設定し次のif文を回避
    

    #d = "9999"  #異常値設定し次のif文を回避
    #日付が更新された場合はリセット
    
    if file_state_reset[ int(no) ] == "reset":
        print(no,file_state_reset)
        #file_state_reset[ int(no) ] = "no"
        state_reset = "yes"

    #ファイルのタイムスタンプに更新が無ければ既存のJSONファイルを返却
    if file_update_time[ int(no) ] in str(d) and state_reset != "yes":
        #print(file_update_time[ int(no) ])
        #print("No renewal",no)

        fp_old = open (file_name,encoding='utf-8')
        json_old = fp_old.read()
        fp_old.close()
        
        dict_old = json.loads(json_old)

        return make_response(jsonify(dict_old))

    print("Renewal work data",no)
    if(info_file_state != "error"):
        #ファイル時間更新
        file_update_time[ int(no)] = str(d)

    #TEAMSのJSONファイル読込
    file_json = path
    fp_in = open (file_json,encoding='utf-8')
    json_str = fp_in.read()
    fp_in.close()
    r_ret = "OK"
    try:
        dict_src_json = json.loads(json_str)
    except json.JSONDecodeError as e:
        r_ret = "NG"
    except OSError as e:
        r_ret = "NG"

    dst_path = './backup/last_teams_json'
    src_path = file_json
    #エラーの場合前回のファイルを利用して表示する　★
    if r_ret == "NG":
        ret = src_path.rfind('/')
        src_path = src_path[ret:]
        src_path = dst_path + src_path
        fp_in = open (src_path,encoding='utf-8')
        json_str = fp_in.read()
        fp_in.close()
        dict_src_json = json.loads(json_str)
        print("バックアップデータ利用",src_path)
    else:
        #前回のファイルをバックアップする　★
        shutil.copy(src_path, dst_path)
    
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
        try:
            dict_old_json = json.loads(json_str)
        except json.JSONDecodeError as e:
            print("teams JSON ファイル読み込みエラー")

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
                tmp_old_state = dict_old_json[cnt]["state"]["Value"]
                if json_update == "ng":
                    if "出社勤務中" in tmp_old_state or "退勤" in tmp_old_state:
                        list["state"]["Value"] = tmp_old_state
                    else:
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
                    list["get_time"] = "データ受信待ち"


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
                if e_time == "" and json_update == "ok":
                    list["work_e_time"] = old_time

            cnt = cnt + 1
        ##状態を更新したファイルに更新
        with open(file_name, "w", encoding='utf-8') as f:
            json.dump(dict_dst_json2, f, indent=4, ensure_ascii=False)
    else:
        file_state_reset[ int(no) ] = "no"
        print("勤務状態リセット", no, state_reset, day_reset)
        if day_reset == "yes":
            #ファイルをバックアップ
            #カウントファイルを読み込む
            file_temp = "./backup/last_backup_cnt.txt"

            f = open(file_temp,'r')
            tmp_cnt = f.read()
            last_cnt = int(tmp_cnt)
            f.close()

            no_cnt = 0
            for cnt in range(len(file_state_reset)):
                if file_state_reset[ cnt ] == "no":
                    no_cnt = no_cnt + 1
            if no_cnt < 2:
                print("リセット１回目！！！",no_cnt)
                last_cnt = last_cnt + 1
                make_freeseat_data("","","RESET","","") #フリー座席リセット
                ##座席表バックアップ
                dst_path = './backup/' + str(last_cnt)
                src_path = './SeatData_h_free4f_temp.json'
                shutil.copy(src_path, dst_path)
                src_path = './SeatData_h_free5f_temp.json'
                shutil.copy(src_path, dst_path)
                src_path = './SeatData_h_free6f_temp.json'
                shutil.copy(src_path, dst_path)
            if last_cnt > 5:
                last_cnt = 1
            print("リセットカウント",last_cnt)
            f = open(file_temp,'w')
            f.write(str(last_cnt))
            f.close()

            for cnt in range(len(sect_dat)):
                dst_path = './backup/' + str(last_cnt)
                src_path = './teams_data/WorkData_temp_' + str(sect_dat[cnt]) + '.json'
                print(dst_path)
                print(src_path)
                shutil.copy(src_path, dst_path)


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

##デバッグ機能#############################################################
def debug_ctl(lpass,lsect,ltxt):
    print("デバッグ操作",lpass,lsect,ltxt)
    if global_pass != lpass:
        return "認証エラー"
    
    if lsect == "001": #浜松座席リセット
        print("### 浜松の座席表をリセットし、新規座席表からデータを更新")
        make_freeseat_data("","","RESET","","")
    elif lsect == "002": #WorkData_temp_xxファイルの削除
        print("### 指定された課のWorkData_temp_xxを削除")
    elif lsect == "003": #OneDriveの更新
        print("### 指定されたファイルをOneDrive上に新規作成")
    else:
        print("### 該当なし指示")
        return "処理なし"
    
def debug_ctl_get(lpass,lsect,ltxt):
    print("デバッグ情報取得",lpass,lsect,ltxt)
    #勤怠管理中間ファイル確認（WorkData_temp_xx.json）
    work_files = [
        "new_work_10.json",
        "new_work_11.json",
        "new_work_14.json",
        "new_work_15.json",
        "new_work_20.json",
        "new_work_21.json",
        "new_work_22.json",
        "new_work_23.json",
        "new_work_24.json",
        "new_work_30.json",
        "new_work_31.json",
        "new_work_32.json",
        "new_work_33.json",
        "new_work_34.json",
        "new_work_35.json",
        "new_work_36.json",
        "new_work_37.json",
        "new_work_39.json",
        "new_work_his_musen.json",
        "new_work_his_system.json",
        "new_work_his_AI.json",
        "./teams_data/WorkData_temp_10.json",
        "./teams_data/WorkData_temp_11.json",
        "./teams_data/WorkData_temp_14.json",
        "./teams_data/WorkData_temp_15.json",
        "./teams_data/WorkData_temp_20.json",
        "./teams_data/WorkData_temp_21.json",
        "./teams_data/WorkData_temp_22.json",
        "./teams_data/WorkData_temp_23.json",
        "./teams_data/WorkData_temp_24.json",
        "./teams_data/WorkData_temp_30.json",
        "./teams_data/WorkData_temp_31.json",
        "./teams_data/WorkData_temp_32.json",
        "./teams_data/WorkData_temp_33.json",
        "./teams_data/WorkData_temp_34.json",
        "./teams_data/WorkData_temp_35.json",
        "./teams_data/WorkData_temp_36.json",
        "./teams_data/WorkData_temp_37.json",
        "./teams_data/WorkData_temp_39.json"
    ]
    work_path = [
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/",
        R""+ global_cloud_dir + "share_data/history/",
        R""+ global_cloud_dir + "share_data/history/",
        R""+ global_cloud_dir + "share_data/history/",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        ""
    ]
    read_res = [[0] * 3 for i in range(len(work_files))]

    for i in range(len(work_files)):
        read_str = ""
        try:
            #ファイル名設定
            read_res[i][0]=work_files[i]

            #ファイルタイムスタンプ調査
            lpath = work_path[i] + work_files[i]
            read_str = os.path.getmtime(lpath)
            read_str = datetime.fromtimestamp(read_str)
            read_res[i][1]=read_str

            #ファイル要素数調査
            f = open (lpath,encoding='utf-8')
            json_str = f.read()
            ch_file = json.loads(json_str)
            f.close()
            read_res[i][2]=0
            for list, has_more in lookahead(ch_file):
                read_res[i][2]=read_res[i][2]+1
          
        except OSError as e:
            read_str = "ファイル読み込みエラー"
            read_res[i]="NG"

    #print(read_res)
    return read_res
    
    print(read_res)
    #座席表用勤怠情報一覧ファイル確認(xxxxSeatData)

    #浜松座席データファイル一覧
    ## 座席管理用ファイル（フリーアドレス管理用のファイル）
    ## 座席ファイル（OneDriveからのコピー）

if __name__ == '__main__':
    app.debug = True
    #app.run()
    app.run(debug=True, host="0.0.0.0", port=5001)
