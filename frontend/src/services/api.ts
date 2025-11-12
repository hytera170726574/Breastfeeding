// src/services/api.ts

/**
 * 这个文件是我们的API服务层。
 * 我们将所有与后端服务器的通信函数都放在这里。
 * 这样做的好处是，如果未来API的地址或者调用方式有变动，
 * 我们只需要修改这个文件，而不用去每个组件里修改。
 */

// 从后端代码我们知道，API的基础URL是 /api
const API_BASE_URL = '/api';

/**
 * 注册新用户的函数
 * @param userData - 包含用户名、邮箱和密码的对象
 * @returns 返回一个Promise，成功时解析为后端返回的数据，失败时拒绝并返回错误信息
 */
export const registerUser = async (userData: any) => {
  // 使用 fetch API 向后端发送POST请求
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST', // 请求方法为POST
    headers: {
      'Content-Type': 'application/json', // 告诉后端我们发送的是JSON格式的数据
    },
    body: JSON.stringify(userData), // 将JavaScript对象转换为JSON字符串
  });

  // 解析后端返回的JSON数据
  const data = await response.json();

  // 如果HTTP响应状态码不是 "ok" (例如 400, 500等), 说明有错误发生
  if (!response.ok) {
    // 抛出一个错误，错误信息优先使用后端返回的message，否则使用通用提示
    throw new Error(data.message || '注册失败，请稍后重试');
  }

  // 如果一切顺利，返回后端处理后的数据
  return data;
};

/**
 * 登录用户的函数
 * @param credentials - 包含邮箱和密码的对象
 * @returns 返回一个Promise，成功时解析为后端返回的数据
 */
export const loginUser = async (credentials: any) => {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || '登录失败，请检查用户名或密码');
  }

  // 登录成功后，后端会返回 access_token
  if (data.access_token) {
    // 我们将 token 存储在浏览器的 localStorage 中
    // localStorage 可以在浏览器关闭后依然保留数据
    localStorage.setItem('authToken', data.access_token);
  }

  return data;
};
