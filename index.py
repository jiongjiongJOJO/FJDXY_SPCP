# coding=utf-8
import base64
import io
import os

import requests
import random
import re
import json
import time
import sys
from lxml import etree


def push(key, title, content):  # 函数用来发送填报失败信息
    url = 'http://www.pushplus.plus/send'
    data = {
        "token": key,
        "title": title,
        "content": "<xmp>" + content + "</xmp>"
    }
    body = json.dumps(data).encode(encoding='utf-8')
    headers = {'Content-Type': 'application/json'}
    requests.post(url, data=body, headers=headers)

def codeIdentification(img):
    try:
        # client_id 为官网获取的AK， client_secret 为官网获取的SK
        host = f'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={ocr_ak}&client_secret={ocr_sk}'
        response = requests.get(host)
        if response:
            access_token = response.json()['access_token']

        request_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}&language_type=ENG"

        params = {"image": img}
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        response = requests.post(request_url, data=params, headers=headers)
        if response:
            print(response.json())
            text = ''
            for i in response.json()['words_result']:
                text += i['words']
            return text
        return None
    except:
        return None

def login():

    # 安徽科技学院不校验验证码，可以随机生成，福建水利水电职业技术学院需要验证码校验，这里通过百度OCR进行识别
    # # 产生随机验证码（其实没必要，服务端不验证，输入固定的验证码即可）
    # selectChar = ["2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f", "g", "h", "j", "k", "m", "n",
    #               "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "A", "B", "C", "D", "E", "F", "G", "H", "J",
    #               "K", "L", "M", "N", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
    # codeInput = ''
    # for i in range(4):
    #     codeInput += selectChar[random.randint(0, 54)]

    # 先创建一个session，方便后续post和get
    session = requests.session()

    # 设置浏览器headers，这里用的我的浏览器信息，需要改的话，自己修改
    session.headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Origin': 'http://xg.fjsdxy.com',
        'Pragma': 'no-cache',
        'Referer': 'http://xg.fjsdxy.com/SPCP/Web/',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
    }



    while(True):
        # 获取登录页ReSubmiteFlag
        ReSubmiteFlag = re.findall('<input name="ReSubmiteFlag" type="hidden" value="(.*?)" />',
                                   session.get('http://xg.fjsdxy.com/SPCP/Web/').text)[0]
        # 获取验证码
        code_result = session.get("http://xg.fjsdxy.com/SPCP/Web/Account/GetLoginVCode?dt=" + str(time.time()))
        code_url = "data:image/jpeg;base64," + base64.b64encode(io.BytesIO(code_result.content).read()).decode()
        print(code_url)
        # OCR识别
        code = codeIdentification(code_url)
        if(not code is None):
            code = code.replace(" ","")
            if(len(code)==4):
                # 登录信息，其中userid是学号，password是密码，codeInput是上面生成的验证码
                data = {'StuLoginMode': '1', 'txtUid': userid, 'txtPwd': password, 'code': code,
                        'ReSubmiteFlag': ReSubmiteFlag}
                try:
                    # 登录账号，获取cookies
                    response_login = session.post('http://xg.fjsdxy.com/SPCP/Web/', data=data, verify=False)
                    if ('安全退出' in response_login.text):
                        break
                except:
                    print('疫情填报登录失败，请检查平台是否能正常访问！')
                    push(send_key, '福建水利水电职业技术学院 - 疫情填报登陆失败', '疫情填报登录失败，请检查平台是否能正常访问！')
                    sys.exit()

    return session


def get_info(session):
    try:
        # 打开疫情填报页面，获取所需信息
        response = session.get('http://xg.fjsdxy.com/SPCP/Web/Report/Index', verify=False)

        # 接下来一大段都是通过正则表达式和lxml模块获取对应的Data信息，以实现自动填报
        info = response.text

        if ('当前采集日期已登记！' in info):
            print('疫情填报失败：今日已填报！')
            push(send_key, '福建水利水电职业技术学院 - 疫情填报失败', info)
            Data = None
        else:
            html = etree.HTML(info)

            Data = {
                'StudentId': re.findall(
                    '''<input name="StudentId" type="text" id="StudentId" readonly="readonly" class="input-style" style=" {8}border: none;" value="(.*?)" />''',
                    info)[0],
                'Name': re.findall(
                    '''<input name="Name" type="text" id="Name" readonly="readonly" class="input-style" style=" {8}border: none;" value="(.*?)" />''',
                    info)[0],
                'Sex': re.findall('''<input id="Sex" name="Sex" type="hidden" value="(.*?)" />''', info)[0],
                'SpeType': re.findall('''<input id="SpeType" name="SpeType" type="hidden" value="(.*?)" />''', info)[0],
                'CollegeNo':
                    re.findall('''<input id="CollegeNo" name="CollegeNo" type="hidden" value="(.*?)" />''', info)[0],
                'SpeGrade': re.findall('''<input id="SpeGrade" name="SpeGrade" type="hidden" value="(.*?)" />''', info)[
                    0],
                'SpecialtyName':
                    re.findall('''<input id="SpecialtyName" name="SpecialtyName" type="hidden" value="(.*?)" />''',
                               info)[0],
                'ClassName':
                    re.findall('''<input id="ClassName" name="ClassName" type="hidden" value="(.*?)" />''', info)[0],
                'MoveTel': re.findall(
                    '''<input name="MoveTel" type="text" id="MoveTel" class="required validate input-style" vtype="TelPhone" value="(.*?)" />''',
                    info)[0],
                'Province': html.xpath(f'//*[@name="Province"]/option[@selected="selected"]')[0].attrib.get("value"),
                'City': re.findall(
                    '''<select name="City" onchange="CityChange\(this\);" data-defaultValue="(.*?)" class="select-style required validate"></select>''',
                    info)[0],
                'County': re.findall(
                    '''<select name="County" data-defaultValue="(.*?)" class="select-style required validate"></select>''',
                    info)[0],
                'ComeWhere': re.findall(
                    '''<input name="ComeWhere" type="text" maxlength="50" value="(.*?)" class="required validate input-style" placeholder="例：XX街道XX社区XX号" />''',
                    info)[0],
                'FaProvince': html.xpath(f'//*[@name="FaProvince"]/option[@selected="selected"]')[0].attrib.get("value"),
                'FaCity': re.findall(
                    '''<select name="FaCity" onchange="CityChange\(this\);" data-defaultValue="(.*?)" class="select-style required validate"></select>''',
                    info)[0],
                'FaCounty': re.findall(
                    '''<select name="FaCounty" data-defaultValue="(.*?)" class="select-style required validate"></select>''',
                    info)[0],
                'FaComeWhere': re.findall(
                    '''<input name="FaComeWhere" type="text" maxlength="50" value="(.*?)" class="required validate input-style" placeholder="例：XX街道XX社区XX号" />''',
                    info)[0]
            }


            PZData = []
            # 单选框
            radio = re.findall(r'<input name=\'radio_.+\' id="(.*?)"', info)
            radio_count = 0
            for i, r in enumerate(radio):
                result = html.xpath(f'//*[@id="{r}"]')
                if (('checked="checked"' in etree.tostring(result[0], encoding='utf-8').decode())):
                    pzd = {
                        "OptionName": result[0].attrib.get("data-optionname"),
                        "SelectId": r,
                        "TitleId": result[0].xpath("..")[0].attrib.get('data-tid'),
                        "OptionType": "0"
                    }
                    PZData.append(pzd)
                    radio_count += 1
                    Data['radio_'+str(radio_count)] = r

            # 填空题
            text = re.findall(r'name="text_(.*?)"', info)
            black_count = 0
            for i, r in enumerate(text):
                result = html.xpath(f'//*[@name="text_{r}"]')
                if (result[0].attrib.get('value') != ''):
                    pzd = {
                        "OptionName": result[0].attrib.get("value"),
                        "SelectId": result[0].xpath("..")[0].attrib.get('data-sid'),
                        "TitleId": result[0].xpath("..")[0].attrib.get('data-tid'),
                        "OptionType": "2"
                    }
                    if(not pzd['SelectId']):
                        pzd['SelectId'] = ""
                    PZData.append(pzd)
                    black_count += 1
                    Data['text_'+str(black_count)] = result[0].attrib.get('value')

            Data = {**Data,**{
                'Other': re.findall('''<textarea name="Other" id="Other" rows="3">(.*?)</textarea>''',info)[0],
                'GetAreaUrl': '/SPCP/Web/Report/GetArea',
                'IdCard': re.findall('''<input id="IdCard" name="IdCard" type="hidden" value="(.*?)" />''', info)[0],
                'ProvinceName':
                    re.findall('''<input id="ProvinceName" name="ProvinceName" type="hidden" value="(.*?)" />''', info)[
                        0],
                'CityName': re.findall('''<input id="CityName" name="CityName" type="hidden" value="(.*?)" />''', info)[
                    0],
                'CountyName':
                    re.findall('''<input id="CountyName" name="CountyName" type="hidden" value="(.*?)" />''', info)[0],
                'FaProvinceName':
                    re.findall('''<input id="FaProvinceName" name="FaProvinceName" type="hidden" value="(.*?)" />''',
                               info)[0],
                'FaCityName':
                    re.findall('''<input id="FaCityName" name="FaCityName" type="hidden" value="(.*?)" />''', info)[0],
                'FaCountyName':
                    re.findall('''<input id="FaCountyName" name="FaCountyName" type="hidden" value="(.*?)" />''', info)[
                        0],
                'radioCount': str(radio_count),
                'checkboxCount': '0',
                'blackCount': str(black_count),
                'PZData': str(PZData),
                'ReSubmiteFlag': re.findall('''<input name="ReSubmiteFlag" type="hidden" value="(.*?)" />''',info)[0]
            }
                    }
    except Exception as e:
        print(e)
        print('获取个人信息失败！')
        push(send_key, '福建水利水电职业技术学院 - 疫情填报失败', '获取个人信息失败！')
        Data = None
    return session, Data


def Temper(session):
    date = [str((time.gmtime().tm_hour + 8)%24),str(time.gmtime().tm_min)]
    print(date)
    # 随机体温
    Temper = random.randint(0, 9)
    # 体温填报
    try:
        response_Temper = session.get('http://xg.fjsdxy.com/SPCP/Web/Temperature/StuTemperatureInfo')
        ReSubmiteFlag = re.findall('<input name="ReSubmiteFlag" type="hidden" value="(.*?)" />',response_Temper.text)[0]
        data = {'TimeNowHour': date[0], 'TimeNowMinute': date[1], 'Temper1': '36', 'Temper2': Temper,
                'ReSubmiteFlag': ReSubmiteFlag}
        response_Temper = session.post('http://xg.fjsdxy.com/SPCP/Web/Temperature/StuTemperatureInfo', data=data)
        # 输出结果
        if ('填报成功！' in response_Temper.text):
            print('体温填报-填报成功！')
        else:
            print(f'{date[0]}:{date[1]}  体温填报失败')
            push(send_key, '福建水利水电职业技术学院 - 体温填报填报失败', response_Temper.text)
    except:
        print(f'{date[0]}:{date[1]}  体温填报失败')
        push(send_key, f'福建水利水电职业技术学院 - 体温填报({date[0]}:{date[1]})失败', '请手动填报')


def yiqing(session, Data):
    # 疫情填报
    try:
        response = session.post('http://xg.fjsdxy.com/SPCP/Web/Report/Index', data=Data)
        if ('提交成功！' in response.text):
            print('疫情填报-提交成功！')
        else:
            print('疫情填报失败')
            push(send_key, '福建水利水电职业技术学院 - 疫情填报失败', response.text)
    except:
        print('疫情填报失败')
        push(send_key, '福建水利水电职业技术学院 - 疫情填报失败', '疫情填报失败，请手动填报！')


def main_handler(a, b):
    session = login()
    hour = time.gmtime().tm_hour + 8
    if(hour>=7 and hour<=9):
        session, Data = get_info(session)
        if (Data != None):
            yiqing(session, Data)
    Temper(session)



if __name__ == '__main__':
    userinfo = os.getenv('USERINFO')
    if(userinfo is None):
        userinfo = """{
            "user": "123456789",
            "password": "123456789",
            "OCR_ak": "123456789",
            "OCR_sk": "123456789",
            "send_key": "123456789"
            }"""
    global send_key,ocr_ak,ocr_sk
    try:
        userid = json.loads(userinfo).get('user')
        password = json.loads(userinfo).get('password')
        ocr_ak = json.loads(userinfo).get('OCR_ak')
        ocr_sk = json.loads(userinfo).get('OCR_sk')
        send_key = json.loads(userinfo).get('send_key')
    except:
        print('环境变量userinfo格式错误')
        sys.exit()
    main_handler(None, None)
