import requests
import json
from datetime import datetime, timedelta

# API基础URL
BASE_URL = "http://localhost:5000/api"

def test_api():
    print("开始测试API...")

    # 1. 用户注册
    # print("\n1. 测试用户注册...")
    # register_data = {
    #     "username": "lidaifeng",
    #     "email": "ldfhead@163.com",
    #     "password": "feng199186"
    # }

    # try:
    #     response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    #     print(f"注册响应: {response.status_code} - {response.json()}")
    # except Exception as e:
    #     print(f"注册请求失败: {e}")

    # 2. 用户登录
    print("\n2. 测试用户登录...")
    login_data = {
        "username": "lidaifeng",
        "password": "feng199186"
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        login_result = response.json()
        print(f"登录响应: {response.status_code} - {login_result}")

        # 获取访问令牌
        access_token = login_result.get('access_token')
        if not access_token:
            print("登录失败，无法获取访问令牌")
            return

        headers = {"Authorization": f"Bearer {access_token}"}
    except Exception as e:
        print(f"登录请求失败: {e}")
        return
    #2.1Getbaby
    # response = requests.get
    
    # 3. 创建婴儿
    print("\n3. 测试创建婴儿...")
    baby_data = {
        "name": "李望舒2",
        "birth_date": "2025-08-06",
        "gender": "female"
        # "id":,
    }

    try:
        response = requests.post(f"{BASE_URL}/baby/createBaby", json=baby_data, headers=headers)
        baby_result = response.json()
        print(f"创建婴儿响应: {response.status_code} - {baby_result}")

        # 获取婴儿ID
        baby_id = baby_result['data']['id'] if 'data' in baby_result else baby_result.get('baby', {}).get('id')
        if not baby_id:
            print("创建婴儿失败，无法获取婴儿ID")
            return
    except Exception as e:
        print(f"创建婴儿请求失败: {e}")
        return

    # # 4. 设置默认婴儿
    # print("\n4. 测试设置默认婴儿...")
    # try:
    #     response = requests.post(f"{BASE_URL}/baby/{baby_id}/set-default", headers=headers)
    #     print(f"设置默认婴儿响应: {response.status_code} - {response.json()}")
    # except Exception as e:
    #     print(f"设置默认婴儿请求失败: {e}")

    # # 5. 创建母乳喂养记录
    # print("\n5. 测试创建母乳喂养记录...")
    # start_time = datetime.now().isoformat()
    # breast_feeding_data = {
    #     "feeding_type": "breast",
    #     "start_time": start_time,
    #     "baby_id": baby_id
    # }

    # try:
    #     response = requests.post(f"{BASE_URL}/feeding/", json=breast_feeding_data, headers=headers)
    #     feeding_result = response.json()
    #     print(f"创建母乳喂养响应: {response.status_code} - {feeding_result}")

    #     # 获取喂养记录ID
    #     feeding_id = feeding_result['data']['id'] if 'data' in feeding_result else feeding_result.get('feeding', {}).get('id')
    # except Exception as e:
    #     print(f"创建母乳喂养请求失败: {e}")
    #     return

    # 6. 结束母乳喂养记录
    print("\n6. 测试结束母乳喂养记录...")
    end_time = (datetime.now() + timedelta(minutes=15)).isoformat()
    end_feeding_data = {
        "end_time": end_time
    }

    try:
        response = requests.put(f"{BASE_URL}/feeding/breast/{feeding_id}/end", json=end_feeding_data, headers=headers)
        print(f"结束母乳喂养响应: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"结束母乳喂养请求失败: {e}")

#     # 7. 创建奶粉喂养记录
#     print("\n7. 测试创建奶粉喂养记录...")
#     bottle_feeding_data = {
#         "feeding_type": "bottle",
#         "bottle_ml": 120,
#         "start_time": datetime.now().isoformat(),
#         "baby_id": baby_id
#     }

#     try:
#         response = requests.post(f"{BASE_URL}/feeding/", json=bottle_feeding_data, headers=headers)
#         print(f"创建奶粉喂养响应: {response.status_code} - {response.json()}")
#     except Exception as e:
#         print(f"创建奶粉喂养请求失败: {e}")

#     # 8. 创建大小便记录
#     print("\n8. 测试创建大小便记录...")
#     diaper_data = {
#         "diaper_type": "wet",
#         "baby_id": baby_id,
#         "timestamp": datetime.now().isoformat()
#     }

#     try:
#         response = requests.post(f"{BASE_URL}/diaper/", json=diaper_data, headers=headers)
#         print(f"创建大小便记录响应: {response.status_code} - {response.json()}")
#     except Exception as e:
#         print(f"创建大小便记录请求失败: {e}")

#     # 9. 创建睡眠记录
#     print("\n9. 测试创建睡眠记录...")
#     sleep_start_data = {
#         "start_time": datetime.now().isoformat(),
#         "baby_id": baby_id
#     }

#     try:
#         response = requests.post(f"{BASE_URL}/sleep/start", json=sleep_start_data, headers=headers)
#         sleep_result = response.json()
#         print(f"开始睡眠记录响应: {response.status_code} - {sleep_result}")

#         # 获取睡眠记录ID
#         sleep_id = sleep_result['data']['id'] if 'data' in sleep_result else sleep_result.get('sleep', {}).get('id')

#         # 结束睡眠记录
#         if sleep_id:
#             end_sleep_data = {
#                 "end_time": (datetime.now() + timedelta(hours=2)).isoformat()
#             }
#             response = requests.put(f"{BASE_URL}/sleep/{sleep_id}/end", json=end_sleep_data, headers=headers)
#             print(f"结束睡眠记录响应: {response.status_code} - {response.json()}")
#     except Exception as e:
#         print(f"创建睡眠记录请求失败: {e}")

#     # 10. 获取统计数据
#     print("\n10. 测试获取统计数据...")
#     stats_data = {
#         "baby_id": baby_id,
#         "start_date": (datetime.now() - timedelta(days=7)).isoformat(),
#         "end_date": datetime.now().isoformat()
#     }

#     try:
#         response = requests.post(f"{BASE_URL}/stats/feeding/dail"y, json=stats_data, headers=headers)
#         print(f"获取喂养统计响应: {response.status_code} - {response.json()}")
#     except Exception as e:
#         print(f"获取喂养统计请求失败: {e}")

#     print("\nAPI测试完成!")

if __name__ == "__main__":
    test_api()