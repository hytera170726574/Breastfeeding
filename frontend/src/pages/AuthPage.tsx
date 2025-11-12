import { useState } from 'react';
// 导入我们封装的API服务函数
import { registerUser, loginUser } from '../services/api';

const AuthPage = () => {
  // 这个状态(state)用来控制显示登录(true)还是注册(false)表单
  const [isLogin, setIsLogin] = useState(true);

  // 定义一个函数，当注册成功后，可以从子组件调用它来切换到登录视图
  const handleRegisterSuccess = () => {
    setIsLogin(true); // 切换到登录视图
    // 这里可以添加一个提示，比如 "注册成功，请登录！"
    alert('注册成功，请登录！');
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-blue-100 to-purple-200">
      {/* Decorative circles from the original design */}
      <div className="absolute top-0 left-0 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
      <div className="absolute top-0 right-0 w-72 h-72 bg-blue-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob [animation-delay:2s]"></div>
      <div className="absolute bottom-0 left-1/4 w-72 h-72 bg-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob [animation-delay:4s]"></div>

      <div className="w-full max-w-4xl flex rounded-2xl shadow-2xl overflow-hidden z-10 bg-white bg-opacity-80 backdrop-blur-lg border border-gray-200">
        {/* Left Side: Welcome Message */}
        <div className="hidden md:flex w-1/2 bg-gradient-to-br from-blue-500 to-purple-600 text-white p-12 flex-col justify-center">
          <h1 className="text-4xl font-bold mb-4">欢迎回来</h1>
          <p className="text-blue-100">记录宝宝成长的每一个珍贵时刻。</p>
        </div>

        {/* Right Side: Form */}
        <div className="w-full md:w-1/2 p-8 md:p-12">
          <h2 className="text-3xl font-bold text-gray-800 mb-6 text-center">
            {isLogin ? '登录' : '注册'}
          </h2>

          {isLogin ? (
            <LoginForm />
          ) : (
            // 将 handleRegisterSuccess 函数作为 prop 传递给 RegisterForm
            <RegisterForm onRegisterSuccess={handleRegisterSuccess} />
          )}

          <div className="mt-6 text-center">
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="text-sm text-blue-600 hover:underline"
            >
              {isLogin ? '还没有账户？立即注册' : '已有账户？直接登录'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const LoginForm = () => {
  // 状态管理：用户名、密码、加载状态和错误信息
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * 处理登录表单提交
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); // 阻止页面刷新
    setError(null);

    if (!username || !password) {
      setError('请输入用户名和密码');
      return;
    }

    setIsLoading(true);

    try {
      // 调用登录API
      await loginUser({ username, password });

      // 登录成功后，我们不再需要做任何事，因为App.tsx会处理页面跳转
      // 这里可以简单地重新加载页面，让App.tsx来决定显示哪个页面
      window.location.reload();

    } catch (err: any) {
      console.error('登录失败:', err);
      setError(err.message || '发生未知错误');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
      {error && <div className="p-3 bg-red-100 text-red-700 rounded-lg">{error}</div>}
      <div>
        <label htmlFor="login-username" className="block text-sm font-medium text-gray-700">用户名</label>
        <input
          type="text"
          id="login-username"
          className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="请输入您的用户名"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
      </div>
      <div>
        <label htmlFor="login-password" className="block text-sm font-medium text-gray-700">密码</label>
        <input
          type="password"
          id="login-password"
          className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>
      <button
        type="submit"
        className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition disabled:bg-blue-400"
        disabled={isLoading}
      >
        {isLoading ? '登录中...' : '登录'}
      </button>
    </form>
  );
};

// 接收 onRegisterSuccess 函数作为 props
const RegisterForm = ({ onRegisterSuccess }: { onRegisterSuccess: () => void }) => {
  // 使用 useState 来管理每个输入框的值
  // 每当输入框内容变化，React会重新渲染组件以显示新值
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // 管理加载状态，防止用户在请求期间重复点击
  const [isLoading, setIsLoading] = useState(false);
  // 管理API请求可能返回的错误信息
  const [error, setError] = useState<string | null>(null);

  /**
   * 处理表单提交的函数
   * @param e - 表单提交事件对象
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); // 阻止浏览器默认的表单提交行为（页面刷新）

    // 简单的客户端验证
    if (!username || !email || !password || !confirmPassword) {
      setError('所有字段均为必填项');
      return;
    }
    if (password.length < 8) {
      setError('密码长度不能少于8位');
      return;
    }
    if (password !== confirmPassword) {
      setError('两次输入的密码不一致');
      return;
    }

    setIsLoading(true); // 开始API请求，设置加载状态为true
    setError(null);     // 清除之前的错误信息

    try {
      // 调用我们封装的API函数
      const userData = { username, email, password };
      await registerUser(userData);

      // 如果 registerUser 成功 (没有抛出错误), 则调用父组件传来的成功回调
      onRegisterSuccess();

    } catch (err: any) {
      // 如果 registerUser 抛出错误，我们在这里捕获它
      console.error('注册失败:', err);
      setError(err.message || '发生未知错误'); // 将错误信息显示给用户
    } finally {
      // 无论成功还是失败，最后都要结束加载状态
      setIsLoading(false);
    }
  };

  return (
    // 当表单提交时，调用 handleSubmit 函数
    <form className="space-y-6" onSubmit={handleSubmit}>
      {/* 如果有错误信息，就在这里显示出来 */}
      {error && <div className="p-3 bg-red-100 text-red-700 rounded-lg">{error}</div>}

      <div>
        <label htmlFor="register-username" className="block text-sm font-medium text-gray-700">用户名</label>
        <input
          type="text"
          id="register-username"
          className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="您的昵称"
          value={username} // 将输入框的值与 state 绑定
          onChange={(e) => setUsername(e.target.value)} // 当内容变化时，更新 state
          required
        />
      </div>
      <div>
        <label htmlFor="register-email" className="block text-sm font-medium text-gray-700">邮箱</label>
        <input
          type="email"
          id="register-email"
          className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>
      <div>
        <label htmlFor="register-password" className="block text-sm font-medium text-gray-700">密码</label>
        <input
          type="password"
          id="register-password"
          className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="至少8位字符"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>
      <div>
        <label htmlFor="register-confirm-password" className="block text-sm font-medium text-gray-700">确认密码</label>
        <input
          type="password"
          id="register-confirm-password"
          className="mt-1 block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="请再次输入密码"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />
      </div>
      <button
        type="submit"
        className="w-full bg-purple-600 text-white py-3 rounded-lg font-semibold hover:bg-purple-700 transition disabled:bg-purple-400"
        disabled={isLoading} // 当正在加载时，禁用按钮
      >
        {isLoading ? '注册中...' : '注册'}
      </button>
    </form>
  );
};

export default AuthPage;

